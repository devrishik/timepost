# -*- coding: utf-8 -*-
# Import the reverse lookup function
import json
import requests
from django.shortcuts import render
from django.core.urlresolvers import reverse

# view imports
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from django.views.generic import ListView
from django.http import HttpResponseRedirect, HttpResponse

from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

from braces.views import LoginRequiredMixin

from .forms import UserForm, InstagramUserForm, InstagramUserIDForm
from .models import User, Follow
from .tasks import get_paginated_followers
from post_web.celery import app

from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.views.generic.base import TemplateView
from instagram.client import InstagramAPI


class GraphView(LoginRequiredMixin, TemplateView):

    template_name = "core/graph.html"

    def get_context_data(self, **kwargs):
        context = super(GraphView, self).get_context_data(**kwargs)
        context['graph_username'] = kwargs['username']
        return context


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        context['form'] = InstagramUserForm()
        return context


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail",
            kwargs={"username": self.request.user.username})


class UserUpdateView(LoginRequiredMixin, UpdateView):

    form_class = UserForm

    # we already imported User in the view code above, remember?
    model = User

    # send the user back to their own page after a successful update
    def get_success_url(self):
        return reverse("users:detail",
                    kwargs={"username": self.request.user.username})

    def get_object(self):
        # Only get the User record for the user making the request
        return User.objects.get(username=self.request.user.username)

class UserListView(LoginRequiredMixin, ListView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = "username"
    slug_url_kwarg = "username"

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(UserListView, self).dispatch(*args, **kwargs)


def get_insta(request, username=None):
    '''
    Takes a user and fetches all its followers
    '''
    try:
        account = SocialAccount.objects.get(user__username=username)
        social_app = SocialApp.objects.get(name='Instagram')
        token = SocialToken.objects.get(account=account, app=social_app)
        api = InstagramAPI(access_token=token)
        url = 'https://api.instagram.com/v1/users/{id}/followed-by?access_token={token}'.format(id=account.uid, token=token.token)
        response = requests.get(url)
        store_followers.delay(account.user, token, response)
    except SocialAccount.DoesNotExist:
        pass
    return HttpResponseRedirect('/users/graph/{0}'.format(username))

@app.task(name='store-followers')
def store_followers(user, token, response):
    '''
    Stores all the followers
    '''
    data = json.loads(response.content)
    user_list = data['data']
    for folllower in user_list:
        username = folllower['username']
        uid = folllower['id']
        try:
            followee = User.objects.get(username=username)
            followee.uid = uid
            followee.save()
        except User.DoesNotExist:
            followee = User.objects.create(username=username, uid=uid)

        try:
            Follow.objects.get(user=user, follower=followee)
        except Follow.DoesNotExist:
            Follow.objects.create(user=user, follower=followee)
        set_timestamp(token, uid)

def set_timestamp(token, uid):
    print 'set_timestamp'
    '''
    Gets the latest timestamp for a uid
    '''
    url = 'https://api.instagram.com/v1/users/{id}/media/recent/?access_token={token}'.format(id=uid, token=token.token)
    response = requests.get(url)
    data = json.loads(response.content)
    timestamp = None
    try:
        data = data['data']
        if data:
            timestamp = data[0]['created_time']
    except KeyError:
        pass
    user = User.objects.get(uid=uid)
    user.timestamp = timestamp
    user.save()

def day_graph(request, username):
    '''
    Ajax function, used to draw graph
    '''
    user = User.objects.get(username=username)
    _dict = user.day_time_dict()
    arr = []
    for i in range(25):
        try:
            arr.append(_dict[i])
        except KeyError:
            arr.append(0)
    del arr[0]
    context = {'data': arr,
                'timepost': user.day_timepost()}
    return HttpResponse(json.dumps(context), content_type="application/json")

def search_user(request):
    print 'search_user'
    if request.method == 'POST':
        form = InstagramUserForm(request.POST)
        if form.is_valid():
            review_id = request.POST['username']
            account = SocialAccount.objects.get(user__username=request.user.username)
            social_app = SocialApp.objects.get(name='Instagram')
            token = SocialToken.objects.get(account=account, app=social_app)
            api = InstagramAPI(access_token=token)

            context = {'users':[], 'form': InstagramUserForm(), 'id_form': InstagramUserIDForm()}

            results = api.user_search(q=review_id)
            for result in results:
                context['users'].append({'username': result.username, 'id': result.id})

            # url = 'https://api.instagram.com/v1/users/search?q={id}&access_token={token}'.format(id=review_id, token=token.token)
            # try:
            #     response = requests.get(url)
            #     data = json.loads(response.content)
            #     if data['meta']['code'] == 200:
            #         for d in data['data']:
            #             context['users'].append({'username': d['username'], 'id': d['id']})
            # except ValueError:
            #     pass
    return render(request, 'core/user_search.html', context)            

def timepost_on_id(request):
    print 'timepost_on_id'
    if request.method == 'POST':
        form = InstagramUserIDForm(request.POST)
        if form.is_valid():
            user_id = request.POST['pk']

            account = SocialAccount.objects.get(user__username=request.user.username)
            social_app = SocialApp.objects.get(name='Instagram')
            token = SocialToken.objects.get(account=account, app=social_app)
            api = InstagramAPI(access_token=token)

            id_user = api.user(user_id)
            # url = 'https://api.instagram.com/v1/users/{id}?access_token={token}'.format(id=user_id, token=token.token)
            # response  = requests.get(url)

            try:
                user = User.objects.get(username=id_user.username)
                user.uid = user_id
                user.save()
            except User.DoesNotExist:
                user = User()
                user.uid = user_id
                user.username = id_user.username
                user.save()
            get_paginated_followers.delay(user, api)

    return HttpResponseRedirect('/users/graph/{0}'.format(user.username))

            #     url = 'https://api.instagram.com/v1/users/{id}?access_token={token}'.format(id=user_id, token=token.token)
            # response  = requests.get(url)
            # try:
            #     data = json.loads(response.content)
            #     if data['meta']['code'] == 200:
            #         try:
            #             user = User.objects.get(username=data['data']['username'])
            #             user.uid = user_id
            #             user.save()
            #         except User.DoesNotExist:
            #             user = User()
            #             user.uid = user_id
            #             user.username = data['data']['username']
            #             user.save()

            #         url = 'https://api.instagram.com/v1/users/{id}/followed-by?access_token={token}'.format(id=user.uid, token=token.token)
            #         # resp = requests.get(url)
            #         # store_followers(user, token, resp)
                    
            #         get_timepost_on_id.delay(token, user.uid)
                    
            #         return HttpResponseRedirect('/users/graph/{0}'.format(user.username))
            # except ValueError:
            #     pass
