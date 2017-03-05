# -*- coding: utf-8 -*-
"""WSGI interface for aiohttp
==========================

Websocket handler specific to aiohttp, as well as its main function.
"""
from __future__ import unicode_literals, print_function, absolute_import

# noinspection PyCompatibility
import asyncio
import logging

# noinspection PyPackageRequirements
import aiohttp
# noinspection PyPackageRequirements
import aiohttp.web
# noinspection PyPackageRequirements
import aiohttp.web_reqrep
# noinspection PyPackageRequirements
import asyncio_redis
from aiohttp_wsgi import WSGIHandler
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import HttpRequest
from djangofloor.wsgi.wsgi_server import WebsocketWSGIServer

__author__ = 'Matthieu Gallet'
logger = logging.getLogger('django.request')


# noinspection PyCompatibility
class WebsocketHandler(object):
    """Handle a websocket as a async routine"""

    @asyncio.coroutine
    def __call__(self, request):
        ws = aiohttp.web.WebSocketResponse()
        # noinspection PyDeprecation
        ws.start(request)
        django_request = self.get_http_request(request)
        window_info = WebsocketWSGIServer.process_request(django_request)
        channels, echo_message = WebsocketWSGIServer.process_subscriptions(django_request)

        connection = yield from asyncio_redis.Connection.create(**settings.WEBSOCKET_REDIS_CONNECTION)
        subscriber = yield from connection.start_subscribe()
        yield from subscriber.subscribe(channels)
        # noinspection PyBroadException
        try:
            # noinspection PyTypeChecker
            yield from asyncio.gather(self.handle_ws(window_info, ws), self.handle_redis(window_info, ws, subscriber))
        except aiohttp.ClientDisconnectedError:
            pass
        except RuntimeError:  # avoid raise RuntimeError('WebSocket connection is closed.')
            pass
        except Exception as e:
            logger.exception(e)
        return ws

    @asyncio.coroutine
    def handle_ws(self, window_info, ws):
        """process each event received on the websocket connection.

        :param window_info: window
        :type window_info: :class:`djangofloor.wsgi.window_info.WindowInfo`
        :param ws: open websocket connection
        :type ws: :class:`aiohttp.web.WebSocketResponse`
        """
        while True:
            msg_ws = yield from ws.receive()
            if msg_ws:
                # noinspection PyTypeChecker
                self.on_msg_from_ws(window_info, ws, msg_ws)

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

    @asyncio.coroutine
    def handle_redis(self, window_info, ws, subscriber):
        """ handle the Redis pubsub connection"""
        while True:
            msg_redis = yield from subscriber.next_published()
            if msg_redis:
                # noinspection PyTypeChecker
                self.on_msg_from_redis(window_info, ws, msg_redis)

    @staticmethod
    def get_http_request(aiohttp_request):
        """Build a Django request from a aiohttp request: required to get sessions and topics.

        :param aiohttp_request: websocket request provided
        :type aiohttp_request: :class:`aiohttp.web_reqrep.Request`
        """
        assert isinstance(aiohttp_request, aiohttp.web_reqrep.Request)
        django_request = HttpRequest()
        django_request.GET = aiohttp_request.rel_url.query
        django_request.COOKIES = aiohttp_request.cookies
        django_request.session = None
        django_request.user = None
        return django_request


def run_server(host, port):
    """run the aiohttp server on the specified network interface.

    :param host: network adress to bind to
    :type host: :class:`str`
    :param port: port to listen to
    :type port: :class:`int`
    """
    # noinspection PyUnresolvedReferences
    import djangofloor.celery
    app = aiohttp.web.Application()
    http_application = get_wsgi_application()
    wsgi_handler = WSGIHandler(http_application)
    if settings.WEBSOCKET_URL:
        app.router.add_route('GET', settings.WEBSOCKET_URL, WebsocketHandler())
    app.router.add_route("*", "/{path_info:.*}", wsgi_handler)

    loop = asyncio.get_event_loop()
    handler = app.make_handler()

    f = loop.create_server(handler, host=host, port=port, )
    srv = loop.run_until_complete(f)
    logger.info("Server started at {sock[0]}:{sock[1]}".format(sock=srv.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(handler.finish_connections(1.0))
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.cleanup())
    loop.close()
