# -*- coding: utf-8 -*-
"""Root URLs provided by DjangoFloor
=================================

By default, register URLs for the admin site, `jsi18n`, static and media files, favicon and robots.txt.
If DjangoDebugToolbar is present, then its URL is also registered.

"""
from __future__ import unicode_literals, print_function, absolute_import

from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.utils.module_loading import import_string
from django.views.i18n import javascript_catalog
from django.views.static import serve

from djangofloor import urls
from djangofloor.scripts import load_celery
from djangofloor.utils import get_view_from_string
from djangofloor.views import favicon, robots

__author__ = 'Matthieu Gallet'

load_celery()
admin.autodiscover()

if settings.DF_URL_CONF:
    extra_urls = import_string(settings.DF_URL_CONF)
else:
    extra_urls = []
prefix = '^' + settings.URL_PREFIX[1:]
urlpatterns = [url(prefix + 'jsi18n/$', javascript_catalog, {'packages': ('djangofloor', 'django.contrib.admin'), }),
               url(prefix + '%s(?P<path>.*)$' % settings.MEDIA_URL[1:], serve, {'document_root': settings.MEDIA_ROOT}),
               url(prefix + '%s(?P<path>.*)$' % settings.STATIC_URL[1:], serve,
                   {'document_root': settings.STATIC_ROOT}),
               url(prefix + 'df/', include(urls, namespace='df')),
               url(prefix + 'robots\.txt$', robots),
               url(prefix + 'favicon\.ico$', favicon, name='favicon'),
               ] + list(extra_urls)
if settings.DF_LOGIN_VIEW:
    login_view = get_view_from_string(settings.DF_LOGIN_VIEW)
    urlpatterns += [url(prefix + settings.LOGIN_URL[1:], login_view, name='login')]
urlpatterns += [url(prefix + 'admin/', include(admin.site.urls))]
if settings.USE_REST_FRAMEWORK:
    urlpatterns += [url(prefix + 'api-auth/', include('rest_framework.urls', namespace='rest_framework'))]
if settings.DF_INDEX_VIEW:
    index_view = get_view_from_string(settings.DF_INDEX_VIEW)
    urlpatterns += [url(prefix + '$', index_view, name='index')]
if settings.DEBUG and settings.USE_DEBUG_TOOLBAR:
    urlpatterns += [url(prefix + '__debug__/', include('debug_toolbar.urls')), ]
if settings.USE_ALL_AUTH:
    urlpatterns += [url(r'^accounts/', include('allauth.urls')), ]

# urlpatterns += [url(r'^df/signal/(?P<signal>[\w\.\-_]+)\.json$', legacy.signal_call, name='df_signal_call'),
#                 url(r'^df/signals.js$', legacy.signals),
#                 url(r'^df/ws_emulation.js$', legacy.get_signal_calls, name='df_get_signal_calls'),
#                 ]
