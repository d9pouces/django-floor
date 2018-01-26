"""Convert a websocket topic to a string
=====================================

Each webpage using websockets is connected to several topics.
Other websocket topics can be any Python object that will be serialized to a string.
Two topics are transparently automatically added: `BROADCAST` and `WINDOW`.
The default serializer should be sufficient for any Django models, but of course you can override it
with the `WEBSOCKET_TOPIC_SERIALIZER` setting.

"""
import logging

from django.contrib.auth import get_user_model
from django.db.models import Model
from djangofloor.wsgi.window_info import Session


__author__ = 'Matthieu Gallet'
logger = logging.getLogger('djangofloor.signals')


def serialize_topic(window_info, obj):
    """ The default serialization function can serialize any Python object with the following rules

  * :class:`djangofloor.tasks.BROADCAST` to '-broadcast'
  * :class:`djangofloor.tasks.WINDOW` to '-window.' + the unique window key provided
    by the :class:`djangofloor.wsgi.window_info.WindowInfo` object,
  * :class:`django.db.models.Model` as "app_label.model_name.primary_key"
  * :class:`djangofloor.tasks.USER` to converted to the authenticated user then
    serialized as any Django model,
  * :class:`django.wsgi.window_info.Session` serialized to "-session.key"
  * other objects are serialized to "class.hash(obj)"

"""
    from djangofloor.tasks import BROADCAST, USER, WINDOW
    if obj is BROADCAST:
        return '-broadcast'
    elif obj is WINDOW:
        if window_info is None:
            return None
        return '-window.%s' % window_info.window_key
    elif isinstance(obj, type):
        return '-<%s>' % obj.__name__
    elif isinstance(obj, Model):
        # noinspection PyProtectedMember
        meta = obj._meta
        return '-%s.%s.%s' % (meta.app_label, meta.model_name, obj.pk or 0)
    elif obj is USER:
        if window_info is None:
            return None
        # noinspection PyProtectedMember
        meta = get_user_model()._meta
        return '-%s.%s.%s' % (meta.app_label, meta.model_name, window_info.user_pk)
    elif isinstance(obj, Session):
        return '-session.%s' % obj.key
    return '-%s.%s' % (obj.__class__.__name__, hash(obj))
