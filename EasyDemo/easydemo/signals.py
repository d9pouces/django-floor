import logging
import time

import re
from djangofloor.decorators import signal, everyone
from djangofloor.signals.bootstrap3 import render_to_modal
from djangofloor.tasks import scall, BROADCAST, SERVER, WINDOW
from djangofloor.wsgi.window_info import render_to_string

__author__ = 'Matthieu Gallet'
logger = logging.getLogger('django.request')
logger2 = logging.getLogger('djangofloor.signals')


# noinspection PyUnusedLocal
@signal(is_allowed_to=everyone, path='demo.slow_signal', queue='slow')
def slow_signal(window_info, content=''):
    logger.warning('wait for 10 seconds [with some special chars to check the encoding: éà]…')
    scall(window_info, 'df.notify', to=[BROADCAST, SERVER],
          content="A second message should be display in ten seconds.",
          level='success', timeout=2, style='notification')
    time.sleep(10)
    logger.warning('10 seconds: done.')
    scall(window_info, 'demo.print_sig2', to=[BROADCAST, SERVER],
          content='This message is sent by a dedicated Celery queue'
                  ' [with some special chars to check the encoding: éà]')


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
          content="Server notification that causes an error in the Celery queue"
                  "[with some special chars for checking encoding: éà] [%r]" % content,
          level='warning', timeout=2, style='notification')
    1/0


@signal(is_allowed_to=everyone, path='demo.chat.receive')
def chat_receive(window_info, content=''):
    matcher = re.match(r'^@([\w\-_]+).*', content)
    if matcher:
        dest = 'chat-%s' % matcher.group(1)
    else:
        dest = BROADCAST
    scall(window_info, 'demo.chat.send', to=[WINDOW, dest], content=content)


@signal(is_allowed_to=everyone, path='demo.show_modal')
def show_modal(window_info, message='Message', level=1):
    render_to_modal(window_info, 'easydemo/modal.html', {'message': message, 'level': level},
                    to=[BROADCAST])
