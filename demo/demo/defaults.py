# coding=utf-8
from __future__ import unicode_literals

__author__ = 'flanker'

FLOOR_URL_CONF = 'demo.urls.urls'
FLOOR_PROJECT_NAME = 'Demo DjangoFloor'
FLOOR_INSTALLED_APPS = ['demo', ]

########################################################################################################################
# sessions
########################################################################################################################
# SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_PREFIX = 'session'
SESSION_REDIS_HOST = '{REDIS_HOST}'
SESSION_REDIS_PORT = '{REDIS_PORT}'
SESSION_REDIS_DB = 10


########################################################################################################################
# caching
########################################################################################################################
# CACHES = {
#     'default': {'BACKEND': 'django_redis.cache.RedisCache', 'LOCATION': 'redis://{REDIS_HOST}:{REDIS_PORT}/11',
#                 'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient', 'PARSER_CLASS': 'redis.connection.HiredisParser', }, },
#     }

########################################################################################################################
# django-redis-websocket
########################################################################################################################
# WSGI_APPLICATION = 'ws4redis.django_runserver.application'
# FLOOR_USE_WS4REDIS = True

########################################################################################################################
# celery
########################################################################################################################
# USE_CELERY = True
