# -*- coding: utf-8 -*-
"""Log utilities to improve Django logging
=======================================

Define useful handlers, formatters and filters and generate an complete log configuration.
"""
from __future__ import unicode_literals, print_function, absolute_import

import logging
import logging.handlers
import os
import re
import sys
import time
import warnings

from django.conf import settings
from django.core.management import color_style
from django.utils.log import AdminEmailHandler as BaseAdminEmailHandler
# noinspection PyUnresolvedReferences
from django.utils.six.moves.urllib.parse import urlparse

__author__ = 'Matthieu Gallet'


class ColorizedFormatter(logging.Formatter):
    """Used in console for applying colors to log lines, corresponding to the log level.
    """
    def __init__(self, *args, **kwargs):
        self.style = color_style()
        kwargs.setdefault('fmt', '%(asctime)s [%(name)s] [%(levelname)s] %(message)s')
        kwargs.setdefault('datefmt', '%Y-%m-%d %H:%M:%S')
        super(ColorizedFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        """apply a log color, corresponding to the log level"""
        msg = record.msg
        level = record.levelno
        if level <= logging.DEBUG:
            msg = self.style.HTTP_SUCCESS(msg)
        elif level <= logging.INFO:
            msg = self.style.HTTP_NOT_MODIFIED(msg)
        elif level <= logging.WARNING:
            msg = self.style.HTTP_INFO(msg)
        else:
            msg = self.style.HTTP_SERVER_ERROR(msg)
        record.msg = msg
        return super(ColorizedFormatter, self).format(record)


class ServerFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.style = color_style()
        super(ServerFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        msg = record.msg
        status_code = getattr(record, 'status_code', None)

        if status_code:
            if 200 <= status_code < 300:
                # Put 2XX first, since it should be the common case
                msg = self.style.HTTP_SUCCESS(msg)
            elif 100 <= status_code < 200:
                msg = self.style.HTTP_INFO(msg)
            elif status_code == 304:
                msg = self.style.HTTP_NOT_MODIFIED(msg)
            elif 300 <= status_code < 400:
                msg = self.style.HTTP_REDIRECT(msg)
            elif status_code == 404:
                msg = self.style.HTTP_NOT_FOUND(msg)
            elif 400 <= status_code < 500:
                msg = self.style.HTTP_BAD_REQUEST(msg)
            else:
                # Any 5XX, or any other status code
                msg = self.style.HTTP_SERVER_ERROR(msg)

        if self.uses_server_time() and not hasattr(record, 'server_time'):
            record.server_time = self.formatTime(record, self.datefmt)

        record.msg = msg
        return super(ServerFormatter, self).format(record)

    def uses_server_time(self):
        return self._fmt.find('%(server_time)') >= 0


# noinspection PyClassHasNoInit
class AdminEmailHandler(BaseAdminEmailHandler):
    """Enhance the AdminEmailHandler provided by Django:
     Does not try to send email if `settings.EMAIL_HOST` is not set.
     Also limits the mail rates to avoid to spam the poor admins."""
    _previous_email_time = None
    min_interval = 600
    """min time (in seconds) between two successive sends"""

    def send_mail(self, subject, message, *args, **kwargs):
        """just check if email can be sent before applying the original method."""
        if self.can_send_email() and settings.EMAIL_HOST:
            try:
                super(AdminEmailHandler, self).send_mail(subject, message, *args, **kwargs)
            except Exception as e:
                print("Unable to send e-mail to admin. Please checks your e-mail settings [%r]." % e)
                if settings.LOG_DIRECTORY:
                    print('Check logs in %s' % settings.LOG_DIRECTORY)

    def can_send_email(self):
        """Check the time of the previous email to allow the new one"""
        now = time.time()
        previous = AdminEmailHandler._previous_email_time
        AdminEmailHandler._previous_email_time = now
        can_send = True
        if previous and now - previous < self.min_interval:
            can_send = False
        return can_send


class RemoveDuplicateWarnings(logging.Filter):
    """Displays py.warnings messages unless the same warning was already sent.
    """
    def __init__(self, name=''):
        super(RemoveDuplicateWarnings, self).__init__(name=name)
        self.previous_records = set()

    def filter(self, record):
        """check if the message has already been sent from the same Python file."""
        record_value = hash('%r %r' % (record.pathname, record.args))
        result = record_value not in self.previous_records
        self.previous_records.add(record_value)
        return result


# noinspection PyTypeChecker
def log_configuration(settings_dict):
    """Generate a log configuration depending on a few parameters:

  * the debug mode (if `DEBUG == True`, everything is printed to the console and lower log level are applied),
  * the log directory (if set, everything is output to several rotated log files),
  * the log remote URL (to send data to syslog or logd),
  * script name (for determining the log filename).

    Required values in the `settings_dict`:

    *  `LOG_DIRECTORY`: dirname where log files are written. Is automatically created if required,
    *  `DF_MODULE_NAME`: your project name, also used in log filenames,
    *  `SCRIPT_NAME`: name of the current Python script ("django", "aiohttp" or "celery")
    *  `DEBUG`: `True` or `False`
    *  `LOG_REMOTE_URL`: examples: "syslog+tcp://localhost:514/user", "syslog:///local7"
         "syslog:///dev/log/daemon", "logd:///project_name"
    """
    log_directory = settings_dict['LOG_DIRECTORY']
    module_name = settings_dict['DF_MODULE_NAME']
    script_name = settings_dict['SCRIPT_NAME']
    debug = settings_dict['DEBUG']
    log_remote_url = settings_dict['LOG_REMOTE_URL']

    fmt_server = 'django.server' if sys.stdout.isatty() else None
    fmt_stderr = 'colorized' if sys.stderr.isatty() else None
    fmt_stdout = 'colorized' if sys.stdout.isatty() else None
    formatters = {
        'django.server': {'()': 'djangofloor.log.ServerFormatter',
                          'format': '%(asctime)s [%(name)s] [%(levelname)s] %(message)s'},
        'nocolor': {'()': 'logging.Formatter', 'fmt': '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S', },
        'colorized': {'()': 'djangofloor.log.ColorizedFormatter'}}
    filters = {'remove_duplicate_warnings': {'()': 'djangofloor.log.RemoveDuplicateWarnings'}}
    server_loggers = ['aiohttp.access', 'gunicorn.access', 'django.server', 'geventwebsocket.handler']

    loggers = {'django': {'handlers': [], 'level': 'WARN', 'propagate': True},
               'django.db.backends': {'handlers': [], 'level': 'WARN', 'propagate': True},
               'django.request': {'handlers': [], 'level': 'INFO', 'propagate': True},
               'django.security': {'handlers': [], 'level': 'WARN', 'propagate': True},
               'djangofloor.signals': {'handlers': [], 'level': 'WARN', 'propagate': True},
               'gunicorn.error': {'handlers': [], 'level': 'WARN', 'propagate': True},
               'pip.vcs': {'handlers': [], 'level': 'ERROR', 'propagate': True},
               'py.warnings': {'handlers': [], 'level': 'ERROR', 'propagate': True,
                               'filters': ['remove_duplicate_warnings']}, }
    for logger in server_loggers:
        loggers[logger] = {'handlers': ['access'], 'level': 'INFO', 'propagate': False}
    root = {'handlers': [], 'level': 'DEBUG'}
    handlers = {'access': {'class': 'logging.StreamHandler', 'level': 'INFO',
                                    'stream': 'ext://sys.stdout', 'formatter': fmt_server}}
    config = {'version': 1, 'disable_existing_loggers': True, 'formatters': formatters, 'filters': filters,
              'handlers': handlers, 'loggers': loggers, 'root': root}
    if debug:
        warnings.simplefilter('always', DeprecationWarning)
        logging.captureWarnings(True)
        loggers['django.request'].update({'level': 'DEBUG'})
        loggers['py.warnings'].update({'level': 'DEBUG'})
        loggers['djangofloor.signals'].update({'level': 'DEBUG'})
        handlers.update({'stdout': {'class': 'logging.StreamHandler', 'level': 'DEBUG',
                                    'stream': 'ext://sys.stdout', 'formatter': fmt_stdout}})
        root.update({'handlers': ['stdout'], 'level': 'INFO'})
        return config

    error_handler = {'class': 'logging.StreamHandler', 'stream': 'ext://sys.stderr', 'formatter': fmt_stderr}
    handlers.update({"mail_admins": {'class': 'djangofloor.log.AdminEmailHandler', 'level': 'ERROR', },
                     'info': {'class': 'logging.StreamHandler', 'level': 'INFO', 'stream': 'ext://sys.stdout',
                              'formatter': fmt_stdout}})
    if log_directory is not None:
        log_directory = os.path.normpath(log_directory)
        if not os.path.isdir(log_directory):
            print('Log folder does not exist. Try mkdir -p "%s"' % log_directory)

            # noinspection PyUnusedLocal
            def get_handler(suffix):
                return error_handler
        else:
            def get_handler(suffix):
                name = '%s-%s-%s.log' % (module_name, script_name, suffix)
                return {'class': 'logging.handlers.RotatingFileHandler', 'maxBytes': 1000000, 'backupCount': 3,
                        'formatter': 'nocolor', 'filename': os.path.join(log_directory, name)}
        error_handler = get_handler('error')
        handlers.update({'info': get_handler('info'),
                         'access': get_handler('access'),
                         'mail_admins': {'level': 'ERROR', 'class': 'djangofloor.log.AdminEmailHandler'}})
    if log_remote_url:
        parsed_log_url = urlparse(log_remote_url)
        scheme = parsed_log_url.scheme
        device, sep, facility_name = parsed_log_url.path.rpartition('/')
        if scheme == 'syslog' or scheme == 'syslog+tcp':
            import platform
            import socket
            import syslog
            if parsed_log_url.hostname and parsed_log_url.port and re.match('^\d+$', parsed_log_url.port):
                address = (parsed_log_url.hostname, int(parsed_log_url.port))
            elif device:
                address = device
            elif platform.system() == 'Darwin':
                address = '/var/run/syslog'
            elif platform.system() == 'Linux':
                address = '/dev/log'
            else:
                address = ('localhost', 514)
            socktype = socket.SOCK_DGRAM if scheme == 'syslog' else socket.SOCK_STREAM
            facility = logging.handlers.SysLogHandler.facility_names.get(facility_name, syslog.LOG_USER)
            error_handler = {'class': 'logging.handlers.SysLogHandler', 'address': address, 'facility': facility,
                             'socktype': socktype}
        elif scheme == 'logd':
            identifier = facility_name or module_name
            error_handler = {'class': 'systemd.journal.JournalHandler', 'SYSLOG_IDENTIFIER': identifier}

    error_handler['level'] = 'ERROR'
    handlers['error'] = error_handler
    loggers['django.request'].update({'level': 'WARN'})
    root.update({'handlers': ['mail_admins', 'error', 'info']})
    return config


log_configuration.required_settings = ['DEBUG', 'DF_MODULE_NAME', 'SCRIPT_NAME', 'LOG_DIRECTORY',
                                                'LOG_REMOTE_URL']