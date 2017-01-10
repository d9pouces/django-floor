# coding=utf-8
from __future__ import unicode_literals
__author__ = 'Matthieu Gallet'
# noinspection PyUnresolvedReferences,PyPackageRequirements
import gevent.socket
import redis.connection
# noinspection PyUnresolvedReferences
from ws4redis.uwsgi_runserver import uWSGIWebsocketServer

redis.connection.socket = gevent.socket
application = uWSGIWebsocketServer()
