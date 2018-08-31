import asyncio

# noinspection PyProtectedMember
import concurrent.futures._base as base
import logging

# noinspection PyPackageRequirements
import aiohttp

# noinspection PyPackageRequirements
import asyncio_redis

# noinspection PyPackageRequirements
from aiohttp import web
from aiohttp_wsgi import WSGIHandler
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import HttpRequest

try:
    # noinspection PyPackageRequirements
    from aiohttp.web_reqrep import Request
except ImportError:
    # noinspection PyPackageRequirements
    from aiohttp.web_request import Request
from djangofloor.wsgi.wsgi_server import WebsocketWSGIServer

logger = logging.getLogger("django.request")


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


@asyncio.coroutine
def handle_redis(window_info, ws, subscriber):
    """ handle the Redis pubsub connection"""
    while window_info.is_active:
        msg_redis = yield from subscriber.next_published()
        if msg_redis:
            yield from ws.send_str(msg_redis.value)


@asyncio.coroutine
def handle_ws(window_info, ws):
    """process each event received on the websocket connection.

    :param window_info: window
    :type window_info: :class:`djangofloor.wsgi.window_info.WindowInfo`
    :param ws: open websocket connection
    :type ws: :class:`aiohttp.web.WebSocketResponse`
    """

    while window_info.is_active:
        msg = yield from ws.receive(timeout=settings.WEBSOCKET_CONNECTION_EXPIRE)
        # for msg in ws:
        if msg.type == web.WSMsgType.text:
            if msg.data == settings.WEBSOCKET_HEARTBEAT:
                yield from ws.send_str(settings.WEBSOCKET_HEARTBEAT)
            elif msg.data == "close":
                window_info.is_active = False
                break
            else:
                WebsocketWSGIServer.publish_message(window_info, msg.data)
        elif msg.type == web.WSMsgType.binary:
            pass
        elif msg.type == web.WSMsgType.close:
            window_info.is_active = False
            break


@asyncio.coroutine
def websocket_handler(request):
    ws = web.WebSocketResponse()
    try:
        yield from ws.prepare(request)
        django_request = get_http_request(request)
        window_info = WebsocketWSGIServer.process_request(django_request)
        channels, echo_message = WebsocketWSGIServer.process_subscriptions(
            django_request
        )
        connection = yield from asyncio_redis.Connection.create(
            **settings.WEBSOCKET_REDIS_CONNECTION
        )
        subscriber = yield from connection.start_subscribe()
    except Exception as e:
        logger.exception(e)
        return ws

    try:
        yield from subscriber.subscribe(channels)
        window_info.is_active = True
        yield from asyncio.gather(
            handle_ws(window_info, ws), handle_redis(window_info, ws, subscriber)
        )
    except aiohttp.ClientConnectionError:
        pass
    except asyncio.TimeoutError:
        pass
    except base.CancelledError:
        pass
    except RuntimeError:  # avoid raise RuntimeError('WebSocket connection is closed.')
        pass
    except Exception as e:
        logger.exception(e)
    finally:
        if subscriber:
            yield from subscriber.unsubscribe(channels)
        connection.close()
    return ws


def get_application():
    # noinspection PyUnresolvedReferences
    import djangofloor.celery

    http_application = get_wsgi_application()
    if settings.WEBSOCKET_URL:
        app = web.Application()
        wsgi_handler = WSGIHandler(http_application)
        app.router.add_route("GET", settings.WEBSOCKET_URL, websocket_handler)
        app.router.add_route("*", "/{path_info:.*}", wsgi_handler)
    else:
        app = http_application
    return app


application = get_application()
