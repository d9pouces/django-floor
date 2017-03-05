# -*- coding: utf-8 -*-
"""Module with all default DjangoFloor signals
===========================================

For all app in `settings.INSTALLED_APPS`, DjangoFloor tries to import `app.signals` for auto-discovering signals.
If you want to write your signals into other modules, be sure that `app.signals` imports these modules.

"""
from __future__ import unicode_literals, print_function, absolute_import

import logging

from djangofloor.decorators import signal, is_staff
from djangofloor.tasks import scall, WINDOW

__author__ = 'Matthieu Gallet'
logger = logging.getLogger('djangofloor.signals')


@signal(path='df.monitoring.check_ws', is_allowed_to=is_staff)
def check_websockets(window_info):
    """Used for checking if websockets are functional or not for your installation. Called from the monitoring view."""
    logger.info('websocket OK')
    scall(window_info, 'df.monitoring.checked_ws', to=[WINDOW])
