import requests
import json

from core.models import User, Follow

from post_web.celery import app

from instagram.bind import InstagramAPIError


@app.task(name='get-paginated-followers')
def get_paginated_followers(user, api):

    # try:
    #     generator = api.user_followed_by(user_id=user.uid, as_generator=True)
    #     for page in generator:
    #     	# for f_user in page[0]:
    #         store_followers.delay(user, api, page[0])
    # except InstagramAPIError as e:
    #     print e.error_message
    #     pass

    token = api.access_token.token
    url = 'https://api.instagram.com/v1/users/{id}/followed-by?access_token={token}'.format(id=user.uid, token=token)
    response = requests.get(url)
    recursive_followers.delay(user, api, response)

@app.task(name='recursive-followers')
def recursive_followers(user, api, response):
    data = json.loads(response.content)
    next_url = ''
    if data['meta']['code'] == 200:
        if data['pagination']:
            print 'pagination'
            next_url = data['pagination']['next_url']
        print 'next_url->' + str(next_url)
        store_followers.delay(user, api, response)
        if not next_url == '':
            resp = requests.get(next_url)
            recursive_followers.delay(user, api, resp)

@app.task(name='store-followers')
def store_followers(user, api, response):
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
        set_timestamp(api, uid)
	

    # for follower in f_users:
    #     username = follower.username
    #     uid = follower.id
    #     try:
    #         followee = User.objects.get(username=username)
    #         followee.uid = uid
    #         followee.save()
    #     except User.DoesNotExist:
    #         followee = User.objects.create(username=username, uid=uid)

    #     try:
    #         Follow.objects.get(user=user, follower=followee)
    #     except Follow.DoesNotExist:
    #         Follow.objects.create(user=user, follower=followee)
    #     set_timestamp(api, uid)


def set_timestamp(api, uid):
    print 'set_timestamp'
    '''
    Gets the latest timestamp for a uid
    '''
    url = 'https://api.instagram.com/v1/users/{id}/media/recent/?access_token={token}'.format(id=uid, token=api.access_token.token)
    response = requests.get(url)
    data = json.loads(response.content)
    timestamp = None
    try:
        data = data['data']
        if data:
            timestamp = data[0]['created_time']
    except KeyError:
        pass
    # timestamp = None
    # try:
    #     media = api.user_recent_media(user_id=uid)[0]
    #     if media:
    #         timestamp = media[0].created_time
    # except (AttributeError, KeyError):
    # 	pass
    user = User.objects.get(uid=uid)
    user.timestamp = timestamp
    user.save()
