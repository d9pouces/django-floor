"""Define Celery tasks and functions for calling signals
=====================================================

This module is automatically imported by Celery.
Use these functions for:

  * setting websocket channels allowed for a given :class:`django.http.response.HttpResponse`,
  * calling signals, with a full function (:meth:`djangofloor.tasks.call`) and a
    shortcut (:meth:`djangofloor.tasks.scall`)

"""

import json
import logging
import os
import uuid
import warnings
from functools import lru_cache

from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string
from redis import StrictRedis, ConnectionPool

from djangofloor.decorators import (
    REGISTERED_SIGNALS,
    SignalConnection,
    REGISTERED_FUNCTIONS,
    FunctionConnection,
    DynamicQueueName,
)
from djangofloor.scripts import load_celery
from djangofloor.utils import import_module, RemovedInDjangoFloor200Warning
from djangofloor.wsgi.exceptions import NoWindowKeyException
from djangofloor.wsgi.window_info import WindowInfo

__author__ = "Matthieu Gallet"
logger = logging.getLogger("djangofloor.signals")


class Constant:
    """Allow to define constants that can be nicely printed to stdout"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


# special values for the "to" argument
SERVER = Constant("SERVER")
SESSION = Constant("SESSION")
WINDOW = Constant("WINDOW")
USER = Constant("USER")
BROADCAST = Constant("BROADCAST")

_signal_encoder = import_string(settings.WEBSOCKET_SIGNAL_ENCODER)
_topic_serializer = import_string(settings.WEBSOCKET_TOPIC_SERIALIZER)

__values = {
    "host": settings.WEBSOCKET_REDIS_HOST,
    "port": ":%s" % settings.WEBSOCKET_REDIS_PORT
    if settings.WEBSOCKET_REDIS_PORT
    else "",
    "db": settings.WEBSOCKET_REDIS_DB,
    "password": ":%s@" % settings.WEBSOCKET_REDIS_PASSWORD
    if settings.WEBSOCKET_REDIS_PASSWORD
    else "",
}
redis_connection_pool = ConnectionPool.from_url(
    "redis://%(password)s%(host)s%(port)s/%(db)s" % __values
)


def get_websocket_redis_connection():
    """Return a valid Redis connection, using a connection pool."""
    return StrictRedis(connection_pool=redis_connection_pool)


def set_websocket_topics(request, *topics):
    """Use it in a Django view for setting websocket topics. Any signal sent to one of these topics will be received
by the client.

    :param request: :class:`django.http.request.HttpRequest`
    :param topics: list of topics that will be subscribed by the websocket (can be any Python object).
    """
    if not settings.USE_CELERY:
        return
    # noinspection PyTypeChecker
    if not hasattr(request, "window_key"):
        raise NoWindowKeyException(
            "You should use the DjangoFloorMiddleware middleware"
        )
    token = request.window_key
    request.has_websocket_topics = True
    prefix = settings.WEBSOCKET_REDIS_PREFIX
    request = WindowInfo.from_request(request)
    topic_strings = {_topic_serializer(request, x) for x in topics if x is not SERVER}
    # noinspection PyUnresolvedReferences,PyTypeChecker
    if getattr(request, "user", None) and request.user.is_authenticated:
        topic_strings.add(_topic_serializer(request, USER))
    topic_strings.add(_topic_serializer(request, WINDOW))
    topic_strings.add(_topic_serializer(request, BROADCAST))
    connection = get_websocket_redis_connection()
    redis_key = "%s%s" % (prefix, token)
    connection.delete(redis_key)
    for topic in topic_strings:
        if topic is not None:
            connection.rpush(redis_key, prefix + topic)
    connection.expire(redis_key, settings.WEBSOCKET_REDIS_EXPIRE)


def scall(window_info, signal_name, to=None, **kwargs):
    """Shortcut to :meth:`djangofloor.tasks.call`, allowing to directly pass arguments of the signal to this function.
Your signal cannot use `window_info`, `signal_name` and `to` as argument names.

These two successive calls are strictly equivalent:

.. code-block:: python

    from djangofloor.tasks import call, scall, WINDOW, SERVER

    def my_python_view(request):
        scall(request, 'my.signal.name', to=[WINDOW, SERVER], arg1=12, arg2='Hello')
        call(request, 'my.signal.name', to=[WINDOW, SERVER], kwargs={'arg1': 12, 'arg2': 'Hello'})

    """
    return _call_signal(
        window_info, signal_name, to=to, kwargs=kwargs, from_client=False
    )


# noinspection PyIncorrectDocstring
def call(
    window_info,
    signal_name,
    to=None,
    kwargs=None,
    countdown=None,
    expires=None,
    eta=None,
):
    """Call a DjangoFloor signal.

    :param window_info: either a :class:`django.http.request.HttpRequest` or
        a :class:`djangofloor.wsgi.window_info.WindowInfo`
    :param signal_name: name of the called signal (:class:`str`)
    :param to: :class:`list` of the topics that should receive the signal
    :param kwargs: dict with all arguments of your signal. Will be encoded to JSON with
       `settings.WEBSOCKET_SIGNAL_ENCODER` and decoded with `settings.WEBSOCKET_SIGNAL_DECODER`.
    :param countdown: check the Celery doc (in a nutshell: number of seconds before executing the signal)
    :param expires: check the Celery doc (in a nutshell: if this signal is not executed before this number of seconds,
       it is cancelled)
    :param eta: check the Celery doc (in a nutshell: datetime of running this signal)
    """
    return _call_signal(
        window_info,
        signal_name,
        to=to,
        kwargs=kwargs,
        countdown=countdown,
        expires=expires,
        eta=eta,
        from_client=False,
    )


def _call_signal(
    window_info,
    signal_name,
    to=None,
    kwargs=None,
    countdown=None,
    expires=None,
    eta=None,
    from_client=False,
):
    """actually calls a DF signal, dispatching them to their destination:

    * only calls Celery tasks if a delay is required (`coutdown` argument)
    * write messages to websockets if no delay is required

    """
    import_signals_and_functions()
    window_info = WindowInfo.from_request(
        window_info
    )  # ensure that we always have a true WindowInfo object
    if kwargs is None:
        kwargs = {}
    for k in (SERVER, WINDOW, USER, BROADCAST):
        if to is k:
            to = [k]
    if to is None:
        to = [USER]
    serialized_client_topics = []
    to_server = False
    logger.debug('received signal "%s" to %r' % (signal_name, to))
    for topic in to:
        if topic is SERVER:
            if signal_name not in REGISTERED_SIGNALS:
                logger.debug('Signal "%s" is unknown by the server.' % signal_name)
            to_server = True
        else:
            serialized_topic = _topic_serializer(window_info, topic)
            if serialized_topic is not None:
                serialized_client_topics.append(serialized_topic)
    celery_kwargs = {}
    if expires:
        celery_kwargs["expires"] = expires
    if eta:
        celery_kwargs["eta"] = eta
    if countdown:
        celery_kwargs["countdown"] = countdown
    queues = {
        x.get_queue(window_info, kwargs)
        for x in REGISTERED_SIGNALS.get(signal_name, [])
    }
    window_info_as_dict = None
    if window_info:
        window_info_as_dict = window_info.to_dict()
    if celery_kwargs:
        if serialized_client_topics:
            queues.add(settings.CELERY_DEFAULT_QUEUE)
        for queue in queues:
            topics = (
                serialized_client_topics
                if queue == settings.CELERY_DEFAULT_QUEUE
                else []
            )
            _server_signal_call.apply_async(
                [
                    signal_name,
                    window_info_as_dict,
                    kwargs,
                    from_client,
                    topics,
                    to_server,
                    queue,
                ],
                queue=queue,
                **celery_kwargs,
            )
    else:
        if to_server:
            for queue in queues:
                _server_signal_call.apply_async(
                    [
                        signal_name,
                        window_info_as_dict,
                        kwargs,
                        from_client,
                        [],
                        to_server,
                        queue,
                    ],
                    queue=queue,
                )
        if serialized_client_topics:
            signal_id = str(uuid.uuid4())
            for topic in serialized_client_topics:
                _call_ws_signal(signal_name, signal_id, topic, kwargs)


def _call_ws_signal(signal_name, signal_id, serialized_topic, kwargs):
    connection = get_websocket_redis_connection()
    serialized_message = json.dumps(
        {"signal": signal_name, "opts": kwargs, "signal_id": signal_id},
        cls=_signal_encoder,
    )
    topic = settings.WEBSOCKET_REDIS_PREFIX + serialized_topic
    logger.debug("send message to topic %r" % topic)
    connection.publish(topic, serialized_message.encode("utf-8"))


def _return_ws_function_result(window_info, result_id, result, exception=None):
    connection = get_websocket_redis_connection()
    json_msg = {
        "result_id": result_id,
        "result": result,
        "exception": str(exception) if exception else None,
    }
    serialized_message = json.dumps(json_msg, cls=_signal_encoder)
    serialized_topic = _topic_serializer(window_info, WINDOW)
    if serialized_topic:
        topic = settings.WEBSOCKET_REDIS_PREFIX + serialized_topic
        logger.debug("send function result to topic %r" % topic)
        connection.publish(topic, serialized_message.encode("utf-8"))


@lru_cache()
def import_signals_and_functions():
    """Import all `signals.py`, 'forms.py' and `functions.py` files to register signals and WS functions
(tries these files for all Django apps).
    """

    def try_import(module):
        try:
            import_module(module)
        except ImportError as e:
            if package_dir and os.path.isfile(
                os.path.join(package_dir, "%s.py" % module_name)
            ):
                logger.exception(e)
        except Exception as e:
            logger.exception(e)

    load_celery()
    for app_config in apps.app_configs.values():
        app = app_config.name
        package_dir = app_config.path
        for module_name in ("signals", "forms", "functions"):
            if os.path.isfile(os.path.join(package_dir, "%s.py" % module_name)):
                try_import("%s.%s" % (app, module_name))
            elif os.path.isdir(os.path.join(package_dir, module_name)):
                for f in os.listdir(os.path.join(package_dir, module_name)):
                    f = os.path.splitext(f)[0]
                    try_import("%s.%s.%s" % (app, module_name, f))
    logger.debug(
        "Found signals: %s"
        % ", ".join(["%s (%d)" % (k, len(v)) for (k, v) in REGISTERED_SIGNALS.items()])
    )
    logger.debug(
        "Found functions: %s" % ", ".join([str(k) for k in REGISTERED_FUNCTIONS])
    )


@shared_task(serializer="json", bind=True)
def _server_signal_call(
    self,
    signal_name,
    window_info_dict,
    kwargs=None,
    from_client=False,
    serialized_client_topics=None,
    to_server=False,
    queue=None,
):
    logger.info(
        'Signal "%s" called on queue "%s" to topics %s (from client?: %s, to server?: %s)'
        % (signal_name, queue, serialized_client_topics, from_client, to_server)
    )
    try:
        if kwargs is None:
            kwargs = {}
        if serialized_client_topics:
            signal_id = str(uuid.uuid4())
            for topic in serialized_client_topics:
                _call_ws_signal(signal_name, signal_id, topic, kwargs)
        window_info = WindowInfo.from_dict(window_info_dict)
        import_signals_and_functions()
        window_info.celery_request = self.request
        if not to_server or signal_name not in REGISTERED_SIGNALS:
            return
        for connection in REGISTERED_SIGNALS[signal_name]:
            assert isinstance(connection, SignalConnection)
            if connection.get_queue(window_info, kwargs) != queue or (
                from_client
                and not connection.is_allowed_to(connection, window_info, kwargs)
            ):
                continue
            new_kwargs = connection.check(kwargs)
            if new_kwargs is None:
                continue
            result = connection(window_info, **new_kwargs)
            # TODO remove the following part
            if isinstance(result, list):
                warnings.warn(
                    "signals should not return list anymore.",
                    RemovedInDjangoFloor200Warning,
                )
                for data in result:
                    call(
                        window_info,
                        data["signal"],
                        to=[WINDOW, SERVER],
                        kwargs=data["options"],
                    )
    except Exception as e:
        logger.exception(e)


@shared_task(serializer="json", bind=True)
def _server_function_call(
    self, function_name, window_info_dict, result_id, kwargs=None
):
    logger.info("Function %s called from client." % function_name)
    e, result, window_info = None, None, None
    try:
        if kwargs is None:
            kwargs = {}
        window_info = WindowInfo.from_dict(window_info_dict)
        import_signals_and_functions()
        window_info.celery_request = self.request
        connection = REGISTERED_FUNCTIONS[function_name]
        assert isinstance(connection, FunctionConnection)
        if not connection.is_allowed_to(connection, window_info, kwargs):
            raise ValueError("Unauthorized function call %s" % connection.path)
        kwargs = connection.check(kwargs)
        if kwargs is not None:
            # noinspection PyBroadException
            result = connection(window_info, **kwargs)
    except Exception as e:
        logger.exception(e)
        result = None
    if window_info:
        _return_ws_function_result(window_info, result_id, result, exception=e)


# TODO remove the following functions
def import_signals():
    """.. deprecated:: 1.0 do not use it"""
    warnings.warn(
        "djangofloor.tasks.import_signals() has been replaced by "
        "djangofloor.tasks.import_signals_and_functions()",
        RemovedInDjangoFloor200Warning,
    )
    return import_signals_and_functions()


@shared_task(serializer="json")
def signal_task(signal_name, request_dict, from_client, kwargs):
    """.. deprecated:: 1.0 do not use it"""
    warnings.warn(
        "djangofloor.tasks.signal_task is deprecated.", RemovedInDjangoFloor200Warning
    )
    return _server_signal_call(
        signal_name,
        request_dict,
        kwargs=kwargs,
        from_client=from_client,
        to_server=True,
    )


@shared_task(serializer="json")
def delayed_task(signal_name, request_dict, sharing, from_client, kwargs):
    """.. deprecated:: 1.0 do not use it"""
    warnings.warn(
        "djangofloor.tasks.delayed_task is deprecated.", RemovedInDjangoFloor200Warning
    )
    import_signals()
    window_info = WindowInfo.from_dict(request_dict)
    # noinspection PyProtectedMember
    from djangofloor.df_ws4redis import _sharing_to_topics

    to = _sharing_to_topics(window_info, sharing) + [SERVER]
    return _server_signal_call(
        signal_name,
        request_dict,
        kwargs=kwargs,
        from_client=from_client,
        serialized_client_topics=to,
        to_server=True,
    )


def df_call(
    signal_name,
    request,
    sharing=None,
    from_client=False,
    kwargs=None,
    countdown=None,
    expires=None,
    eta=None,
):
    """.. deprecated:: 1.0, do not use it"""
    # noinspection PyUnusedLocal
    from_client = from_client
    warnings.warn(
        "djangofloor.tasks.df_call is deprecated.", RemovedInDjangoFloor200Warning
    )
    # noinspection PyProtectedMember
    from djangofloor.df_ws4redis import _sharing_to_topics

    to = _sharing_to_topics(request, sharing) + [SERVER]
    call(
        signal_name,
        request,
        to=to,
        kwargs=kwargs,
        countdown=countdown,
        expires=expires,
        eta=eta,
    )


def get_expected_queues():
    expected_queues = set()
    if not settings.USE_CELERY:
        return expected_queues
    import_signals_and_functions()
    for connection in REGISTERED_FUNCTIONS.values():
        if isinstance(connection.queue, DynamicQueueName):
            for queue_name in connection.queue.get_available_queues():
                expected_queues.add(queue_name)
        elif not callable(connection.queue):
            expected_queues.add(connection.queue)
    for connections in REGISTERED_SIGNALS.values():
        for connection in connections:
            if isinstance(connection.queue, DynamicQueueName):
                for queue_name in connection.queue.get_available_queues():
                    expected_queues.add(queue_name)
            elif not callable(connection.queue):
                expected_queues.add(connection.queue)
    return expected_queues
