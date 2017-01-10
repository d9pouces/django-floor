# -*- coding: utf-8 -*-
"""Define some helpers functions for using django-websocket-redis with DjangoFloor.

You should not directly use these functions.
"""
from __future__ import unicode_literals, absolute_import
import json

from django.conf import settings
from django.utils.encoding import force_text
from django.utils.six import binary_type
from django.utils.translation import ugettext as _
# noinspection PyUnresolvedReferences
from ws4redis.subscriber import RedisSubscriber
# noinspection PyUnresolvedReferences
from ws4redis.publisher import RedisPublisher
# noinspection PyUnresolvedReferences
from ws4redis.redis_store import RedisMessage

from djangofloor.decorators import SignalRequest
from djangofloor.exceptions import ApiException
from djangofloor.tasks import BROADCAST, df_call, SESSION, USER, get_signal_encoder, get_signal_decoder, WINDOW

__author__ = 'Matthieu Gallet'


def ws_call(signal_name, request, sharing, kwargs):
    """ Call a JS signal from the Python side.

    :param signal_name: name of signal
    :type signal_name:
    :param request: a SignalRequest with session_key and username
    :type request: :class:`djangofloor.decorators.SignalRequest`
    :param sharing: the required sharing. Can be SESSION, USER or BROADCAST or any dict which is valid
    for django-websockets-redis.
    :type sharing:
    :param kwargs: options to pass to the JS signal
    :type kwargs:
    :return: `None`
    """
    if isinstance(sharing, binary_type):
        sharing = force_text(sharing)
    facility = settings.FLOOR_WS_FACILITY
    if sharing == SESSION:
        sharing = {SESSION: [request.session_key, ]}
    elif sharing == WINDOW:
        sharing = {BROADCAST: True}
        facility = request.window_key
    elif sharing == USER:
        sharing = {USER: [request.username, ]}
    elif sharing == BROADCAST:
        sharing = {BROADCAST: True}
    if BROADCAST in sharing:
        sharing[BROADCAST] = True
    redis_publisher = RedisPublisher(facility=facility, **sharing)
    msg = json.dumps({'signal': signal_name, 'options': kwargs}, cls=get_signal_encoder())
    redis_publisher.publish_message(RedisMessage(msg.encode('utf-8')))


class Subscriber(RedisSubscriber):
    """ Read messages sent by the client and call its signals.
    """

    internal_publishers = {'%s:%s:%s' % (settings.WS4REDIS_PREFIX, BROADCAST, 'djangofloor')}

    def __init__(self, connection):
        super(Subscriber, self).__init__(connection)
        # noinspection PyTypeChecker
        self.request = SignalRequest(None, None, None)

    def set_pubsub_channels(self, request, channels):
        self.request = request
        super(Subscriber, self).set_pubsub_channels(request, channels)

    def publish_message(self, message, expire=None):
        """
        Publish a ``message`` on the subscribed channel on the Redis datastore.
        ``expire`` sets the time in seconds, on how long the message shall additionally of being
        published, also be persisted in the Redis datastore. If unset, it defaults to the
        configuration settings ``WS4REDIS_EXPIRE``.
        """
        # noinspection PyUnusedLocal
        expire = expire
        if not isinstance(message, RedisMessage):
            raise ValueError('message object is not of type RedisMessage')
        if self._publishers != self.internal_publishers:
            return
        # noinspection PyBroadException
        try:
            message_dict = json.loads(message.decode('utf-8'), cls=get_signal_decoder())
            self.request.window_key = message_dict['window_key']
            df_call(message_dict['signal'], self.request, sharing=None, from_client=True,
                    kwargs=message_dict['options'])
        except ApiException as e:
            df_call('df.messages.error', self.request, sharing=WINDOW, from_client=True,
                    kwargs={'html': _('Error: %(msg)s') % {'msg': force_text(e)}})
        except Exception as e:
            df_call('df.messages.error', self.request, sharing=WINDOW, from_client=True,
                    kwargs={'html': _('Invalid websocket message: %(msg)s.') % {'msg': force_text(e)}})
