# coding=utf-8
"""
WSGI config for djangofloor project.

This module contains the WSGI application used by Django's development server, patched for websockets.
It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
from __future__ import unicode_literals
__author__ = 'Matthieu Gallet'
from django.conf import settings
from djangofloor.wsgi_http import application as _django_app


def application(environ, start_response):
    """
    Return a WSGI application which is patched to be used with websockets.

    :return: a HTTP app, or a WS app (depending on the URL path)
    """
    if settings.FLOOR_USE_WS4REDIS and environ.get('PATH_INFO').startswith(settings.WEBSOCKET_URL):
        from djangofloor.wsgi_websockets import application as _websocket_app
        return _websocket_app(environ, start_response)
    return _django_app(environ, start_response)
