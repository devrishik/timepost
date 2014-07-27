# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from core import views

urlpatterns = patterns('',
    # URL pattern for the UserListView
    url(
        regex=r'^$',
        view=views.UserListView.as_view(),
        name='list'
    ),
    # URL pattern for the UserRedirectView
    url(
        regex=r'^~redirect/$',
        view=views.UserRedirectView.as_view(),
        name='redirect'
    ),
    url(r'^search_user/$', views.search_user, name='search'),
    url(r'^graph/(?P<username>[\w\-_]+)/$', views.GraphView.as_view(), name='graph'),
    url(r'^line_data/(?P<username>[\w\-_]+)/$', views.day_graph, name='day_graph'),
    url(r'^timepost_on_id/$', views.timepost_on_id, name='timepost_on_id'),
    # URL pattern for the UserDetailView    
    url(
        regex=r'^(?P<username>[\w\-_]+)/$',
        view=views.UserDetailView.as_view(),
        name='detail'
    ),
    url(r'^insta/(?P<username>[\w\-_]+)$', views.get_insta, name="insta"),
    # URL pattern for the UserUpdateView
    url(
        regex=r'^~update/$',
        view=views.UserUpdateView.as_view(),
        name='update'
    ),

)