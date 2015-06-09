# coding=utf-8
from __future__ import unicode_literals
"""Define mappings from the URL requested by a user to a proper Python view."""
__author__ = 'flanker'
from django.utils.module_loading import import_string
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from djangofloor.scripts import load_celery
load_celery()

admin.autodiscover()

if settings.FLOOR_URL_CONF:
    extra_urls = import_string(settings.FLOOR_URL_CONF)
else:
    extra_urls = []

if settings.FLOOR_INDEX:
    index_view = settings.FLOOR_INDEX
else:
    index_view = 'djangofloor.views.index'

urlpatterns = patterns('',
                       url(r'^accounts/', include('allauth.urls')),
                       url(r'^admin/', include(admin.site.urls)),
                       (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('djangofloor', 'django.contrib.admin', ), }),
                       (r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
                       (r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
                       (r'^df/signal/(?P<signal>[\w\.\-_]+)\.json$', 'djangofloor.views.signal_call'),
                       (r'^df/signals.js$', 'djangofloor.views.signals'),
                       (r'^df/ws_emulation.js$', 'djangofloor.views.get_signal_calls'),
                       (r'^robots\.txt$', 'djangofloor.views.robots'),
                       (r'^$', index_view),
                       *extra_urls)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('', url(r'^__debug__/', include(debug_toolbar.urls)), )