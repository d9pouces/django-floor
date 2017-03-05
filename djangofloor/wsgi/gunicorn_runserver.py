# -*- coding: utf-8 -*-
"""WSGI application for Gunicorn
=============================

This module contains the WSGI application used by Gunicorn. However, websockets do not properly work
(due to active polling on the websocket that eats the whole CPU).

"""
from __future__ import unicode_literals, print_function, absolute_import

import logging
import select

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.utils import six
from djangofloor.wsgi.wsgi_server import WebsocketWSGIServer

__author__ = 'Matthieu Gallet'
logger = logging.getLogger('django.request')

if six.PY3:
    # noinspection PyShadowingBuiltins
    xrange = range


class GunicornWebsocketServer(WebsocketWSGIServer):
    WS_GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    WS_VERSIONS = (b'13', b'8', b'7')

    def get_ws_file_descriptor(self, websocket):
        return websocket.stream.handler.socket.fileno()

    def flush_websocket(self, websocket):
        pass

    def upgrade_websocket(self, environ, start_response):
        return environ['wsgi.websocket']

    def select(self, rlist, wlist, xlist, timeout=None):
        # return gevent.select.select(rlist, wlist, xlist, timeout)
        return select.select(rlist, wlist, xlist, timeout)

    def verify_client(self, ws):
        pass

    def ws_send_bytes(self, websocket, message):
        return websocket.send(message)

    def ws_receive_bytes(self, websocket):
        return websocket.receive()

http_application = get_wsgi_application()
ws_application = GunicornWebsocketServer()


def application(environ, start_response):
    """
    Return a WSGI application which is patched to be used with websockets.

    :return: a HTTP app, or a WS app (depending on the URL path)
    """
    if settings.WEBSOCKET_URL and environ.get('PATH_INFO', '').startswith(settings.WEBSOCKET_URL):
        return ws_application(environ, start_response)
    return http_application(environ, start_response)
