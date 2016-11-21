# coding=utf-8
from __future__ import unicode_literals
from djangofloor.utils import ExpandIterable

FLOOR_TEMPLATE_CONTEXT_PROCESSORS = []
FLOOR_INSTALLED_APPS = []
FLOOR_EXTRA_APPS = []
OTHER_ALLAUTH = []
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.admin',
    'djangofloor',
    'bootstrap3',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'pipeline',
    'debug_toolbar',
    ExpandIterable('FLOOR_EXTRA_APPS'),
    ExpandIterable('OTHER_ALLAUTH'),
    ExpandIterable('FLOOR_INSTALLED_APPS'),
]
