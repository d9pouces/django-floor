# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django.http import HttpRequest
from redis import StrictRedis
# noinspection PyUnresolvedReferences
from ws4redis.publisher import redis_connection_pool
# noinspection PyUnresolvedReferences
from ws4redis.settings import WS4REDIS_PREFIX
from djangofloor.decorators import SignalRequest

__author__ = 'Matthieu Gallet'


class Sessions(object):
    def __init__(self, key):
        self.key = self._key(key)
        self.connection = StrictRedis(connection_pool=redis_connection_pool)

    @staticmethod
    def _key(key):
        return '%sdf:session_set:%s' % (WS4REDIS_PREFIX or '', key)

    @staticmethod
    def _session_key(request):
        if isinstance(request, HttpRequest) and request.session:
            return request.session.session_key
        elif isinstance(request, SignalRequest):
            return request.session_key
        return None

    def add(self, request):
        return self.__iadd__(request)

    def remove(self, request):
        return self.__isub__(request)

    def all(self):
        return self.connection.smembers(self.key)

    def __iter__(self):
        return self.connection.smembers(self.key).__iter__()

    def __len__(self):
        return self.connection.scard(self.key)

    def __contains__(self, request):
        session_key = self._session_key(request)
        if session_key:
            return self.connection.sismember(self.key, session_key)
        return False

    def __iadd__(self, request):
        session_key = self._session_key(request)
        if session_key:
            self.connection.sadd(self.key, session_key)
        return self

    def __isub__(self, request):
        session_key = self._session_key(request)
        if session_key:
            self.connection.srem(self.key, session_key)
        return self
