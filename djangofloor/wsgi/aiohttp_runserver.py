"""WSGI interface for aiohttp
==========================

Websocket handler specific to aiohttp, as well as its main function.
"""
# noinspection PyCompatibility
import asyncio
# noinspection PyProtectedMember
import concurrent.futures._base as base
import logging

# noinspection PyPackageRequirements
import aiohttp
# noinspection PyPackageRequirements
import aiohttp.web
import time

try:
    # noinspection PyPackageRequirements
    from aiohttp.web_reqrep import Request
except ImportError:
    # noinspection PyPackageRequirements
    from aiohttp.web_request import Request
# noinspection PyPackageRequirements
import asyncio_redis
from aiohttp_wsgi import WSGIHandler
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import HttpRequest
from djangofloor.wsgi.wsgi_server import WebsocketWSGIServer

__author__ = 'Matthieu Gallet'
logger = logging.getLogger('django.request')


@asyncio.coroutine
def handle_redis(window_info, ws, subscriber):
    """ handle the Redis pubsub connection"""
    while True:
        msg_redis = yield from subscriber.next_published()
        if msg_redis:
            # noinspection PyTypeChecker
            WebsocketHandler.on_msg_from_redis(window_info, ws, msg_redis)


@asyncio.coroutine
def handle_ws(window_info, ws):
    """process each event received on the websocket connection.

    :param window_info: window
    :type window_info: :class:`djangofloor.wsgi.window_info.WindowInfo`
    :param ws: open websocket connection
    :type ws: :class:`aiohttp.web.WebSocketResponse`
    """
    while True:
        msg_ws = yield from ws.receive(timeout=settings.WEBSOCKET_CONNECTION_EXPIRE)
        if msg_ws:
            # noinspection PyTypeChecker
            WebsocketHandler.on_msg_from_ws(window_info, ws, msg_ws)


@asyncio.coroutine
def websocket_handler(request):
    ws = aiohttp.web.WebSocketResponse()
    try:
        yield from ws.prepare(request)
        django_request = WebsocketHandler.get_http_request(request)
        window_info = WebsocketWSGIServer.process_request(django_request)
        channels, echo_message = WebsocketWSGIServer.process_subscriptions(django_request)
        connection = yield from asyncio_redis.Connection.create(**settings.WEBSOCKET_REDIS_CONNECTION)
        subscriber = yield from connection.start_subscribe()
    except Exception as e:
        logger.exception(e)
        return ws
    try:
        yield from subscriber.subscribe(channels)
        # noinspection PyTypeChecker
        yield from asyncio.gather(handle_ws(window_info, ws), handle_redis(window_info, ws, subscriber))
    except aiohttp.ClientConnectionError:
        pass
    except base.CancelledError:
        pass
    except RuntimeError:  # avoid raise RuntimeError('WebSocket connection is closed.')
        pass
    except Exception as e:
        logger.exception(e)
    return ws


class WebsocketHandler:
    """Handle a websocket as a async routine"""

    @staticmethod
    def on_msg_from_ws(window_info, ws, msg):
        """ process any received websocket message

        :param window_info: window
        :type window_info: :class:`djangofloor.wsgi.window_info.WindowInfo`
        :param ws: open websocket connection
        :type ws: :class:`aiohttp.web.WebSocketResponse`
        :param msg: message received on the websocket
        :type msg: :class:`aiohttp.WSMessage`
        """
        if not msg:
            pass
        elif msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                ws.close()
            elif msg.data == settings.WEBSOCKET_HEARTBEAT:
                ws.send_str(settings.WEBSOCKET_HEARTBEAT)
            else:
                WebsocketWSGIServer.publish_message(window_info, msg.data)
                # ws.send_str(msg.data + '/answer')

    # noinspection PyUnusedLocal
    @staticmethod
    def on_msg_from_redis(window_info, ws, msg):
        """ called on each message received on the redis pubsub connection
        and write it to the websocket"""
        message = msg.value
        ws.send_str(message)

    @staticmethod
    def get_http_request(aiohttp_request):
        """Build a Django request from a aiohttp request: required to get sessions and topics.

        :param aiohttp_request: websocket request provided
        :type aiohttp_request: :class:`Request`
        """
        assert isinstance(aiohttp_request, Request)
        django_request = HttpRequest()
        django_request.GET = aiohttp_request.rel_url.query
        django_request.COOKIES = aiohttp_request.cookies
        django_request.session = None
        django_request.user = None
        return django_request


def get_application():
    # noinspection PyUnresolvedReferences
    import djangofloor.celery
    http_application = get_wsgi_application()
    if settings.WEBSOCKET_URL:
        app = aiohttp.web.Application()
        wsgi_handler = WSGIHandler(http_application)
        app.router.add_route('GET', settings.WEBSOCKET_URL, websocket_handler)
        app.router.add_route("*", "/{path_info:.*}", wsgi_handler)
    else:
        app = http_application
    return app


application = get_application()
