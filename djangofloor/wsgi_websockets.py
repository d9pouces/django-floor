# coding=utf-8
from __future__ import unicode_literals
__author__ = 'flanker'
import gevent.socket
import redis.connection
from ws4redis.uwsgi_runserver import uWSGIWebsocketServer

redis.connection.socket = gevent.socket
application = uWSGIWebsocketServer()