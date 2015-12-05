# coding=utf-8
from __future__ import unicode_literals
import os

__author__ = 'Matthieu Gallet'
LOCAL_PATH = '.%sdjango_data' % os.path.sep
FLOOR_URL_CONF = 'demo.urls.urls'
FLOOR_PROJECT_NAME = 'Demo DjangoFloor'
FLOOR_INSTALLED_APPS = ['demo', ]
FLOOR_FAKE_AUTHENTICATION_USERNAME = 'test_user'
########################################################################################################################
# sessions
########################################################################################################################
# SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_PREFIX = 'session'
SESSION_REDIS_HOST = '{REDIS_HOST}'
SESSION_REDIS_PORT = '{REDIS_PORT}'
SESSION_REDIS_DB = 10

WS4REDIS_EMULATION_INTERVAL = 1000
DEBUG = False

########################################################################################################################
# django-redis-websocket
########################################################################################################################
# WSGI_APPLICATION = 'ws4redis.django_runserver.application'
# FLOOR_USE_WS4REDIS = True

########################################################################################################################
# celery
########################################################################################################################
USE_CELERY = False
