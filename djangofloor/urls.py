# -*- coding: utf-8 -*-
"""URLs specific to DjangoFloor
============================

Define URLs for user authentication forms and for defining JS signals.
Also define the URL linked to the monitoring and to the search views.
"""
from __future__ import unicode_literals, print_function, absolute_import

from django.conf import settings
from django.conf.urls import url

from djangofloor.utils import get_view_from_string
from djangofloor.views import auth, signals, monitoring

__author__ = 'Matthieu Gallet'


urlpatterns = [
    url(r'^logout/', auth.logout, name='logout'),
    url(r'^password_reset/', auth.password_reset, name='password_reset'),
    url(r'^set_password/', auth.set_password, name='set_password'),
]
if settings.WEBSOCKET_URL:
    urlpatterns += [url(r'^signals.js$', signals, name='signals')]
if settings.DF_SYSTEM_CHECKS:
    urlpatterns += [url(r'^monitoring/system_state/', monitoring.system_state, name='system_state')]
if settings.DF_SITE_SEARCH_VIEW:
    search_view = get_view_from_string(settings.DF_SITE_SEARCH_VIEW)
    urlpatterns += [url(r'^search/', search_view, name='site_search')]
