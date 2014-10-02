#coding=utf-8
"""Define mappings from the URL requested by a user to a proper Python view."""
from django.utils.module_loading import import_string
from djangofloor.scripts import load_celery

__author__ = 'flanker'

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
load_celery()

admin.autodiscover()

if settings.FLOOR_URLCONF:
    extra_urls = import_string(settings.FLOOR_URLCONF)
else:
    extra_urls = []

urlpatterns = patterns('',
                       url(r'^accounts/', include('allauth.urls')),
                       url(r'^admin/', include(admin.site.urls)),
                       (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
                        {'packages': ('djangofloor', 'django.contrib.admin', ), }),
                       (r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
                        {'document_root': settings.MEDIA_ROOT}),
                       (r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
                        {'document_root': settings.STATIC_ROOT}),
                       (r'^robots\.txt$', 'djangofloor.views.robots'),
                       (r'^test/$', 'djangofloor.views.test'),
                       (r'^$', 'djangofloor.views.index'),
                       *extra_urls)
