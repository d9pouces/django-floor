# coding=utf-8
"""Define mappings from the URL requested by a user to a proper Python view."""
from __future__ import unicode_literals

from django.views.i18n import javascript_catalog
from django.views.static import serve
from django.utils.module_loading import import_string
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from djangofloor.views import signal_call, signals, get_signal_calls, robots
from djangofloor.scripts import load_celery


__author__ = 'Matthieu Gallet'
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
index_view = import_string(index_view)

urlpatterns = [url(r'^accounts/', include('allauth.urls')),
               url(r'^admin/', include(admin.site.urls)),
               url(r'^jsi18n/$', javascript_catalog, {'packages': ('djangofloor', 'django.contrib.admin', ), }),
               url(r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
               url(r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
               url(r'^df/signal/(?P<signal>[\w\.\-_]+)\.json$', signal_call, name='df_signal_call'),
               url(r'^df/signals.js$', signals),
               url(r'^df/ws_emulation.js$', get_signal_calls, name='df_get_signal_calls'),
               url(r'^robots\.txt$', robots),
               url(r'^$', index_view, name='index'),
               ] + list(extra_urls)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls)), ]
