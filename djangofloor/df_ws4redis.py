# -*- coding: utf-8 -*-
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
from djangofloor.tasks import BROADCAST, df_call, SESSION, USER


__author__ = 'flanker'


def ws_call(signal_name, request, sharing, kwargs):
    if isinstance(sharing, binary_type):
        sharing = force_text(sharing)
    if sharing == SESSION:
        sharing = {SESSION: [request.session_key, ]}
    elif sharing == USER:
        sharing = {USER: [request.username, ]}
    elif sharing == BROADCAST:
        sharing = {BROADCAST: True}
    if BROADCAST in sharing:
        sharing[BROADCAST] = True
    redis_publisher = RedisPublisher(facility=settings.FLOOR_WS_FACILITY, **sharing)
    msg = json.dumps({'signal': signal_name, 'options': kwargs})
    redis_publisher.publish_message(RedisMessage(msg.encode('utf-8')))


class Subscriber(RedisSubscriber):

    internal_publishers = {'%s:%s:%s' % (settings.WS4REDIS_PREFIX, BROADCAST, 'djangofloor')}

    def __init__(self, connection):
        super(Subscriber, self).__init__(connection)
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
        if not isinstance(message, RedisMessage):
            raise ValueError('message object is not of type RedisMessage')
        if self._publishers != self.internal_publishers:
            return
        # noinspection PyBroadException
        try:
            message_dict = json.loads(message.decode('utf-8'))
            df_call(message_dict['signal'], self.request, sharing=None, from_client=True, kwargs=message_dict['options'])
        except ApiException as e:
            df_call('df.messages.error', self.request, sharing=SESSION, from_client=True, kwargs={'html': _('Error: %(msg)s') % {'msg': force_text(e)}})
        except Exception as e:
            df_call('df.messages.error', self.request, sharing=SESSION, from_client=True, kwargs={'html': _('Invalid websocket message: %(msg)s.') % {'msg': force_text(e)}})