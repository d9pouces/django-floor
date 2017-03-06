# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

import logging
import time

import re
from djangofloor.decorators import signal, everyone
from djangofloor.tasks import scall, BROADCAST, SERVER, WINDOW
from djangofloor.wsgi.window_info import render_to_string

__author__ = 'Matthieu Gallet'
logger = logging.getLogger('django.request')
logger2 = logging.getLogger('djangofloor.signals')


# noinspection PyUnusedLocal
@signal(is_allowed_to=everyone, path='demo.slow_signal', queue='slow')
def slow_signal(window_info, content=''):
    logger.warning('wait for 10 seconds [éà]…')
    time.sleep(10)
    logger.warning('10 seconds: done.')
    scall(window_info, 'demo.print_sig2', to=[BROADCAST, SERVER],
          content='This message is sent by a dedicated Celery queue [éà]')


@signal(is_allowed_to=everyone, path='demo.print_sig1')
def print_sig1(window_info, content=''):
    logger.debug('Debug log message [%r]' % content)
    logger.info('Debug info message [%r]' % content)
    logger.warning('Debug warn message [%r]' % content)
    logger.error('Debug error message [%r]' % content)
    logger2.debug('Debug log message / logger2 [%r]' % content)
    logger2.info('Debug info message / logger2 [%r]' % content)
    logger2.warning('Debug warn message / logger2 [%r]' % content)
    logger2.error('Debug error message / logger2 [%r]' % content)
    scall(window_info, 'df.notify', to=[BROADCAST, SERVER],
          content="Some lines should be added in the Celery log files",
          level='success', timeout=2, style='notification')
    scall(window_info, 'demo.print_sig2', to=[BROADCAST, SERVER], content=content)


@signal(is_allowed_to=everyone, path='demo.print_sig2')
def print_sig2(window_info, content=''):
    scall(window_info, 'df.notify', to=[BROADCAST, SERVER],
          content="Server notification that causes an error in the Celery queue[éà] [%r]" % content,
          level='warning', timeout=2, style='notification')
    1/0


@signal(is_allowed_to=everyone, path='demo.chat.receive')
def chat_receive(window_info, content=''):
    matcher = re.match('^@([\w\-_]+).*', content)
    if matcher:
        dest = 'chat-%s' % matcher.group(1)
    else:
        dest = BROADCAST
    scall(window_info, 'demo.chat.send', to=[WINDOW, dest], content=content)


@signal(is_allowed_to=everyone, path='demo.show_modal')
def show_modal(window_info, message='Message', level=1):
    content = render_to_string('easydemo/modal.html', {'message': message, 'level': level})
    respawn = {'signal': 'demo.show_modal', 'options': {'message': '%s (-)' % message, 'level': level}}
    if level % 2 == 0:
        respawn = None
    scall(window_info, 'df.modal.show', to=[BROADCAST], html=content,
          respawn=respawn, clean_stack=level == 15)
