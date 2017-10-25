import base64
import logging
from hashlib import sha1

from django.conf import settings
from django.core.wsgi import get_wsgi_application
# noinspection PyPackageRequirements
from eventlet.green import select
# noinspection PyPackageRequirements
from gunicorn.workers.async import ALREADY_HANDLED

from djangofloor.wsgi.exceptions import UpgradeRequiredError, HandshakeError
from djangofloor.wsgi.websocket import WebSocket
from djangofloor.wsgi.wsgi_server import WebsocketWSGIServer

logger = logging.getLogger(__name__)


class WebSocketWSGI(WebsocketWSGIServer):
    WS_GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    WS_VERSIONS = ('13', '8', '7')

    def upgrade_websocket(self, environ, start_response):
        """
        Attempt to upgrade the socket environ['wsgi.input'] into a websocket enabled connection.
        """
        websocket_version = environ.get('HTTP_SEC_WEBSOCKET_VERSION', '')
        print('websocket_version %s' % websocket_version)
        if not websocket_version:
            raise UpgradeRequiredError
        elif websocket_version not in self.WS_VERSIONS:
            raise HandshakeError('Unsupported WebSocket Version: {0}'.format(websocket_version))

        key = environ.get('HTTP_SEC_WEBSOCKET_KEY', '').strip()
        if not key:
            raise HandshakeError('Sec-WebSocket-Key header is missing/empty')
        try:
            key_len = len(base64.b64decode(key))
        except TypeError:
            raise HandshakeError('Invalid key: {0}'.format(key))
        if key_len != 16:
            # 5.2.1 (3)
            raise HandshakeError('Invalid key: {0}'.format(key))

        sec_ws_accept = base64.b64encode(sha1(key.encode('utf-8') + self.WS_GUID).digest())
        sec_ws_accept = sec_ws_accept.decode('ascii')
        headers = [
            ('Upgrade', 'websocket'),
            ('Connection', 'Upgrade'),
            ('Sec-WebSocket-Accept', sec_ws_accept),
            ('Sec-WebSocket-Version', str(websocket_version)),
        ]
        logger.debug('WebSocket request accepted, switching protocols')
        start_response(str('101 Switching Protocols'), headers)
        return GunicornWebSocket(environ['gunicorn.socket'], websocket_version)

    def get_ws_file_descriptor(self, websocket):
        return websocket.get_file_descriptor()

    def select(self, rlist, wlist, xlist, timeout=None):
        return select.select(rlist, wlist, xlist, timeout)

    def flush_websocket(self, websocket):
        pass

    def ws_send_bytes(self, websocket, message):
        return websocket.send(message)

    def ws_receive_bytes(self, websocket):
        return websocket.receive()

    def default_response(self):
        return ALREADY_HANDLED


class GunicornWebSocket(WebSocket):

    def __init__(self, wsgi_input, version):
        super().__init__(Stream(wsgi_input))
        self.version = version


class Stream(object):
    """
    Wraps the handler's socket/rfile attributes and makes it in to a file like
    object that can be read from/written to by the lower level websocket api.
    """

    __slots__ = ('read', 'write', 'fileno')

    # noinspection PyProtectedMember
    def __init__(self, sock):
        self.read = sock.recv
        self.write = sock.sendall
        self.fileno = sock.fileno()


ws_application = WebSocketWSGI()
http_application = get_wsgi_application()


def application(environ, start_response):
    """
    Return a WSGI application which is patched to be used with websockets.

    :return: a HTTP app, or a WS app (depending on the URL path)
    """
    if settings.WEBSOCKET_URL and environ.get('PATH_INFO', '').startswith(settings.WEBSOCKET_URL):
        return ws_application(environ, start_response)
    return http_application(environ, start_response)
