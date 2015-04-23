# coding=utf-8
from __future__ import unicode_literals
"""Define mappings from the URL requested by a user to a proper Python view."""
from django.utils.module_loading import import_string
from djangofloor.scripts import load_celery

__author__ = 'flanker'

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
load_celery()

admin.autodiscover()

if settings.FLOOR_URL_CONF:
    extra_urls = import_string(settings.FLOOR_URL_CONF)
else:
    extra_urls = []

urlpatterns = patterns('',
                       url(r'^accounts/', include('allauth.urls')),
                       url(r'^admin/', include(admin.site.urls)),
                       (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('djangofloor', 'django.contrib.admin', ), }),
                       (r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
                       (r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
                       (r'^df/signal/(?P<signal>[\w\.\-_]+)\.json$', 'djangofloor.views.signal_call'),
                       (r'^df/signals.js$', 'djangofloor.views.signals'),
                       (r'^robots\.txt$', 'djangofloor.views.robots'),
                       (r'^$', 'djangofloor.views.index'),
                       *extra_urls)
