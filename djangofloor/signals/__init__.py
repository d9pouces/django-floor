"""Module with all default DjangoFloor signals
===========================================

For all app in `settings.INSTALLED_APPS`, DjangoFloor tries to import `app.signals` for auto-discovering signals.
If you want to write your signals into other modules, be sure that `app.signals` imports these modules.

"""
import logging

from django.utils.translation import ugettext as _

from djangofloor.decorators import signal, is_staff, is_superuser, SerializedForm
from djangofloor.forms import LogNameForm
from djangofloor.signals.bootstrap3 import notify, WARNING, NOTIFICATION, BANNER, SYSTEM, MODAL, INFO, DANGER, \
    SUCCESS, DEFAULT
from djangofloor.tasks import scall, WINDOW

__author__ = 'Matthieu Gallet'
logger = logging.getLogger('djangofloor.signals')


@signal(path='df.monitoring.check_ws', is_allowed_to=is_staff)
def check_websockets(window_info):
    """Used for checking if websockets are functional or not for your installation. Called from the monitoring view."""
    logger.info('websocket OK')
    scall(window_info, 'df.monitoring.checked_ws', to=[WINDOW])


@signal(path='df.monitoring.raise_exception', is_allowed_to=is_superuser)
def check_websockets(window_info):
    """Check what happens when an exception is raised in a Celery queue"""
    notify(window_info, _('An exception (division by zero) has been raised in a Celery queue'), to=WINDOW,
           level=WARNING, style=BANNER)
    # noinspection PyStatementEffect
    1 / 0


@signal(path='df.monitoring.generate_log', is_allowed_to=is_superuser)
def generate_log(window_info, form: SerializedForm(LogNameForm)):
    """Used for checking if websockets are functional or not for your installation. Called from the monitoring view."""
    if form.is_valid():
        logname = form.cleaned_data['log_name'] or form.cleaned_data['other_log_name'] or 'django.requests'
        level = form.cleaned_data['level']
        message = form.cleaned_data['message']
        logger_ = logging.getLogger(logname)
        logger_.log(int(level), message)
        message = _('message "%(message)s" logged to "%(logname)s" at level %(level)s.') % \
            {'message': message, 'level': level, 'logname': logname}
        notify(window_info, message, to=WINDOW, level=WARNING, style=BANNER)
