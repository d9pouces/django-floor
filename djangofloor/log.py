"""Log utilities to improve Django logging
=======================================

Define useful handlers, formatters and filters and generate an complete log configuration.
"""
import logging
import logging.handlers
import os
import re
import sys
import time
import warnings
from traceback import extract_stack
from urllib.parse import urlparse

from django.core.checks.messages import Warning
from django.core.management import color_style
from django.utils.log import AdminEmailHandler as BaseAdminEmailHandler

from djangofloor.checks import settings_check_results

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
            msg = self.style.WARNING(msg)
        else:
            msg = self.style.ERROR(msg)
        record.msg = msg
        return super(ColorizedFormatter, self).format(record)


class ServerFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.style = color_style()
        super(ServerFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        msg = record.msg
        status_code = getattr(record, 'status_code', None)
        level = record.levelno
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
        elif level <= logging.DEBUG:
            msg = self.style.HTTP_SUCCESS(msg)
        elif level <= logging.INFO:
            msg = self.style.HTTP_NOT_MODIFIED(msg)
        elif level <= logging.WARNING:
            msg = self.style.WARNING(msg)
        else:
            msg = self.style.ERROR(msg)

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
        from django.conf import settings
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


class SlowQueryCallback:
    def __init__(self, duration: float):
        self.duration = duration or 30.

    def __call__(self, record):
        return record.duration > self.duration

    def __repr__(self):
        return 'lambda record: record.duration > %s' % self.duration

    def __str__(self):
        return 'lambda record: record.duration > %s' % self.duration


def resolve_command():
    f = extract_stack()
    for (filename, line_number, name, text) in f:
        if filename.endswith('djangofloor/scripts.py') and name in ('django', 'celery', 'uwsgi', 'gunicorn', 'aiohttp'):
            return name
    return None


# noinspection PyMethodMayBeStatic
class LogConfiguration:
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
    required_settings = ['DEBUG', 'DF_MODULE_NAME', 'SCRIPT_NAME', 'LOG_DIRECTORY', 'LOG_REMOTE_URL',
                         'LOG_SLOW_QUERIES_DURATION', 'LOG_REMOTE_ACCESS']
    request_loggers = ['aiohttp.access', 'gunicorn.access', 'django.server', 'geventwebsocket.handler']

    def __init__(self):
        self.formatters = {}
        self.filters = {}
        self.loggers = {}
        self.handlers = {}
        self.root = {}
        self.config = {}
        self.log_suffix = None
        self.module_name = None
        self.log_directory = None
        self.script_name = None

    def __call__(self, settings_dict):
        self.log_directory = settings_dict['LOG_DIRECTORY']
        log_remote_url = settings_dict['LOG_REMOTE_URL']
        self.module_name = settings_dict['DF_MODULE_NAME']
        log_remote_access = settings_dict['LOG_REMOTE_ACCESS']
        script_name = settings_dict['SCRIPT_NAME']
        debug = settings_dict['DEBUG']

        self.log_suffix = self.get_logfile_suffix(script_name, sys.argv)
        self.formatters = self.get_default_formatters(settings_dict)
        self.filters = self.get_default_filters(settings_dict)
        self.loggers = self.get_default_loggers(settings_dict)
        self.handlers = self.get_default_handlers(settings_dict)
        self.root = self.get_default_root(settings_dict)
        config = {'version': 1, 'disable_existing_loggers': True, 'formatters': self.formatters,
                  'filters': self.filters, 'handlers': self.handlers, 'loggers': self.loggers, 'root': self.root}
        if debug:
            warnings.simplefilter('always', DeprecationWarning)
            logging.captureWarnings(True)
            self.loggers['django.request']['level'] = 'DEBUG'
            self.loggers['py.warnings']['level'] = 'DEBUG'
            self.loggers['djangofloor.signals']['level'] = 'DEBUG'
            self.root['level'] = 'DEBUG'
            self.add_handler('ROOT', 'stdout', level='INFO', formatter='colorized')
            for logger in self.request_loggers:
                self.add_handler(logger, 'stderr', formatter='django.server')
            return config
        has_handler = False
        if self.log_directory:
            self.add_handler('ROOT', 'log', level='WARN')
            self.add_handler('ROOT', 'errors', level='ERROR')
            if self.get_slow_query_duration(settings_dict):
                self.add_handler('django.db', 'slow_queries', level='WARN')
            for logger in self.request_loggers:
                self.add_handler(logger, 'access', level='INFO')
            has_handler = True
        if log_remote_url:
            parsed_log_url = urlparse(log_remote_url)
            scheme = parsed_log_url.scheme
            device, sep, facility_name = parsed_log_url.path.rpartition('/')
            if scheme == 'syslog' or scheme == 'syslog+tcp':
                import platform
                import socket
                import syslog
                if parsed_log_url.hostname and parsed_log_url.port and re.match(r'^\d+$', parsed_log_url.port):
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
                self.add_handler('ROOT', 'syslog', level='WARN', address=address, facility=facility,
                                 socktype=socktype)
                if log_remote_access:
                    for logger in self.request_loggers:
                        self.add_handler(logger, 'syslog', level='INFO', address=address, facility=facility,
                                         socktype=socktype)
                has_handler = True
            elif scheme == 'logd':
                identifier = facility_name or self.module_name
                self.add_handler('ROOT', 'syslog', level='WARN', SYSLOG_IDENTIFIER=identifier)
                if log_remote_access:
                    for logger in self.request_loggers:
                        self.add_handler(logger, 'syslog', level='INFO', SYSLOG_IDENTIFIER=identifier)
                has_handler = True
        if not has_handler:
            self.add_handler('ROOT', 'stdout', level='WARN', formatter='colorized')
            for logger in self.request_loggers:
                self.add_handler(logger, 'stderr', formatter='django.server')
        self.root['handlers'].append('mail_admins')
        return config

    @property
    def fmt_stderr(self):
        return 'colorized' if sys.stderr.isatty() else None

    @property
    def fmt_stdout(self):
        return 'colorized' if sys.stdout.isatty() else None

    def get_slow_query_duration(self, settings_dict):
        return settings_dict['LOG_SLOW_QUERIES_DURATION']

    def get_default_formatters(self, settings_dict):
        return {
            'django.server': {'()': 'djangofloor.log.ServerFormatter',
                              'format': '%(asctime)s [%(name)s] [%(levelname)s] %(message)s'},
            'nocolor': {'()': 'logging.Formatter', 'fmt': '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
                        'datefmt': '%Y-%m-%d %H:%M:%S', },
            'colorized': {'()': 'djangofloor.log.ColorizedFormatter'},
        }

    def get_default_handlers(self, settings_dict):
        return {
            'mail_admins': {'class': 'djangofloor.log.AdminEmailHandler', 'level': 'ERROR', },
        }

    def get_default_filters(self, settings_dict):
        slow_query_duration = self.get_slow_query_duration(settings_dict)
        return {
            'remove_duplicate_warnings': {'()': 'djangofloor.log.RemoveDuplicateWarnings'},
            'slow_queries': {'()': 'django.utils.log.CallbackFilter',
                             'callback': SlowQueryCallback(slow_query_duration)},
        }

    def get_default_root(self, settings_dict):
        return {'handlers': [], 'level': 'WARN'}

    def get_default_loggers(self, settings_dict):
        loggers = {
            'py.warnings': {'handlers': [], 'level': 'ERROR', 'propagate': True,
                            'filters': ['remove_duplicate_warnings']},
            'pip.vcs': {'handlers': [], 'level': 'ERROR', 'propagate': True},
            'django': {'handlers': [], 'level': 'WARN', 'propagate': True},
            'django.db': {'handlers': [], 'level': 'DEBUG', 'propagate': True},
            'django.db.backends': {'handlers': [], 'level': 'WARN', 'propagate': True},
            'django.request': {'handlers': [], 'level': 'INFO', 'propagate': True},
            'django.security': {'handlers': [], 'level': 'WARN', 'propagate': True},
            'djangofloor.signals': {'handlers': [], 'level': 'WARN', 'propagate': True},
            'gunicorn.error': {'handlers': [], 'level': 'WARN', 'propagate': True},
        }
        for logger in self.request_loggers:
            loggers[logger] = {'handlers': [], 'level': 'INFO', 'propagate': False}
        return loggers

    def add_handler(self, logger: str, filename: str, level: str = 'WARN', formatter=None, **kwargs):
        """Add a handler to a logger.
        The name of the added handler is unique, so the definition of the handler is also add if required.
        You can use "ROOT" as logger name to target the root logger.

        filename: can be a filename or one of the following special values: "stderr", "stdout", "logd", "syslog"
        """
        if filename == 'stderr':
            handler_name = '%s.%s' % (filename, level.lower())
            if formatter in ('django.server', 'colorized') and not sys.stderr.isatty():
                formatter = None
            elif formatter:
                handler_name += '.%s' % formatter
            handler = {'class': 'logging.StreamHandler', 'level': level, 'stream': 'ext://sys.stderr',
                       'formatter': formatter}
        elif filename == 'stdout':
            handler_name = '%s.%s' % (filename, level.lower())
            if formatter in ('django.server', 'colorized') and not sys.stdout.isatty():
                formatter = None
            elif formatter:
                handler_name += '.%s' % formatter
            handler = {'class': 'logging.StreamHandler', 'level': level, 'stream': 'ext://sys.stdout',
                       'formatter': formatter}
        elif filename == 'syslog':
            handler_name = '%s.%s' % (filename, level.lower())
            handler = {'class': 'logging.handlers.SysLogHandler', **kwargs}
        elif filename == 'logd':
            try:
                # noinspection PyUnresolvedReferences,PyPackageRequirements
                import systemd.journal
            except ImportError:
                warning = Warning('Unable to import systemd.journal (required to log with journlad)',
                                  hint=None, obj='systemd.journal', id='djangofloor.W006')
                settings_check_results.append(warning)
                # replace logd by writing to a plain-text log
                self.add_handler(logger, level.lower(), level=level)
                return
            handler_name = '%s.%s' % (filename, level.lower())
            handler = {'class': 'systemd.journal.JournalHandler', **kwargs}
        else:  # basename of a plain-text log
            log_directory = os.path.normpath(self.log_directory)
            if not os.path.isdir(log_directory):
                warning = Warning('Missing directory, you can create it with \nmkdir -p "%s"' % log_directory,
                                  hint=None, obj=log_directory, id='djangofloor.W004')
                settings_check_results.append(warning)
                self.add_handler(logger, 'stdout', level=level, **kwargs)
                return
            basename = '%s-%s-%s.log' % (self.module_name, self.log_suffix, filename)
            log_filename = os.path.join(log_directory, basename)
            try:
                open(log_filename, 'a').close()
            except PermissionError:
                warning_ = Warning('Unable to write logs in "%s". Unsufficient rights?' % log_directory,
                                   hint=None, obj=log_directory, id='djangofloor.W005')
                settings_check_results.append(warning_)
                self.add_handler(logger, 'stdout', level=level, **kwargs)
            handler_name = '%s.%s.%s' % (self.module_name, self.log_suffix, filename)
            handler = {'class': 'logging.handlers.RotatingFileHandler', 'maxBytes': 1000000, 'backupCount': 3,
                       'formatter': 'nocolor', 'filename': log_filename}

        if handler_name not in self.handlers:
            self.handlers[handler_name] = handler
        if logger == 'ROOT':
            self.root['handlers'].append(handler_name)
        else:
            self.loggers[logger]['handlers'].append(handler_name)

    def get_logfile_suffix(self, script_name, argv):
        command_name = resolve_command()
        if command_name == 'django' and len(argv) > 1:
            log_suffix = '%s-%s' % (script_name, argv[1])
        elif command_name == 'celery' and len(argv) > 1:
            log_suffix = '%s-%s' % (script_name, argv[1])
            if argv[1] == 'worker':
                index = -1
                if '-Q' in argv:
                    index = argv.index('-Q') + 1
                elif '--queues' in argv:
                    index = argv.index('--queues') + 1
                if 0 <= index < len(argv):
                    log_suffix += '-%s' % ('.'.join(sorted(argv[index].split(','))))
        else:
            log_suffix = script_name
        return log_suffix


log_configuration = LogConfiguration()
