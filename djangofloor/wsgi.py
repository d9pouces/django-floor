# coding=utf-8
from __future__ import unicode_literals
__author__ = 'flanker'
from django.conf import settings
from djangofloor.wsgi_http import application as _django_app


def application(environ, start_response):
    if settings.USE_WS4REDIS and environ.get('PATH_INFO').startswith(settings.WEBSOCKET_URL):
        from djangofloor.wsgi_websockets import application as _websocket_app
        return _websocket_app(environ, start_response)
    return _django_app(environ, start_response)