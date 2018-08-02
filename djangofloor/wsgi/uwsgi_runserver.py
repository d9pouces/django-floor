import logging

import redis.connection

# noinspection PyUnresolvedReferences,PyPackageRequirements
import uwsgi

# noinspection PyPackageRequirements,PyUnresolvedReferences
import gevent.select
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from djangofloor.wsgi.exceptions import WebSocketError
from djangofloor.wsgi.wsgi_server import WebsocketWSGIServer

__author__ = "Matthieu Gallet"
logger = logging.getLogger("django.request")


class UWSGIWebsocket:
    def __init__(self):
        self._closed = False

    def get_file_descriptor(self):
        """Return the file descriptor for the given websocket"""
        try:
            return uwsgi.connection_fd()
        except IOError as e:
            self.close()
            raise WebSocketError(e)

    @property
    def closed(self):
        return self._closed

    def receive(self):
        if self._closed:
            raise WebSocketError("Connection is already closed")
        try:
            return uwsgi.websocket_recv_nb().decode("utf-8")
        except IOError as e:
            self.close()
            raise WebSocketError(e)

    def flush(self):
        try:
            uwsgi.websocket_recv_nb()
        except IOError:
            self.close()

    # noinspection PyUnusedLocal
    def send(self, message, binary=None):
        try:
            uwsgi.websocket_send(message)
        except IOError as e:
            self.close()
            raise WebSocketError(e)

    # noinspection PyUnusedLocal
    def close(self, code=1000, message=""):
        self._closed = True


class UWSGIWebsocketServer(WebsocketWSGIServer):
    def upgrade_websocket(self, environ, start_response):
        uwsgi.websocket_handshake(
            environ["HTTP_SEC_WEBSOCKET_KEY"], environ.get("HTTP_ORIGIN", "")
        )
        return UWSGIWebsocket()

    def get_ws_file_descriptor(self, websocket):
        return websocket.get_file_descriptor()

    def select(self, rlist, wlist, xlist, timeout=None):
        return gevent.select.select(rlist, wlist, xlist, timeout)

    def flush_websocket(self, websocket):
        return websocket.flush()

    def ws_send_bytes(self, websocket, message):
        return websocket.send(message)

    def ws_receive_bytes(self, websocket):
        return websocket.receive()


redis.connection.socket = gevent.socket
http_application = get_wsgi_application()
ws_application = UWSGIWebsocketServer()


def application(environ, start_response):
    """
    Return a WSGI application which is patched to be used with websockets.

    :return: a HTTP app, or a WS app (depending on the URL path)
    """
    if settings.WEBSOCKET_URL and environ.get("PATH_INFO", "").startswith(
        settings.WEBSOCKET_URL
    ):
        return ws_application(environ, start_response)
    return http_application(environ, start_response)
