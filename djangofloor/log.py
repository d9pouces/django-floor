"""Log utilities to improve Django logging
=======================================

Define useful handlers, formatters and filters and generate an complete log configuration.
"""
import atexit
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
from djangofloor.utils import is_package_present

__author__ = "Matthieu Gallet"


class ColorizedFormatter(logging.Formatter):
    """Used in console for applying colors to log lines, corresponding to the log level.
    """

    def __init__(self, *args, **kwargs):
        self.style = color_style()
        kwargs.setdefault("fmt", "%(asctime)s [%(name)s] [%(levelname)s] %(message)s")
        kwargs.setdefault("datefmt", "%Y-%m-%d %H:%M:%S")
        super().__init__(*args, **kwargs)

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
        return super().format(record)

    def formatStack(self, stack_info):
        return self.style.ERROR(stack_info)


class ServerFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.style = color_style()
        super().__init__(*args, **kwargs)

    def format(self, record):
        msg = record.msg
        status_code = getattr(record, "status_code", None)
        level = record.levelno
        if status_code:
            if 200 <= status_code < 300:
                # Put 2XX first, since it should be the common case
                msg = self.style.SUCCESS(msg)
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

        if self.uses_server_time() and not hasattr(record, "server_time"):
            record.server_time = self.formatTime(record, self.datefmt)

        record.msg = msg
        return super().format(record)

    def uses_server_time(self):
        return self._fmt.find("%(server_time)") >= 0


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
                super().send_mail(subject, message, *args, **kwargs)
            except Exception as e:
                print(
                    "Unable to send e-mail to admin. Please checks your e-mail settings [%r]."
                    % e
                )
                if settings.LOG_DIRECTORY:
                    print("Check logs in %s" % settings.LOG_DIRECTORY)

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

    def __init__(self, name=""):
        super().__init__(name=name)
        self.previous_records = set()

    def filter(self, record):
        """check if the message has already been sent from the same Python file."""
        record_value = hash("%r %r" % (record.pathname, record.args))
        result = record_value not in self.previous_records
        self.previous_records.add(record_value)
        return result


# noinspection PyMethodMayBeStatic
class LogConfiguration:
    """Generate a log configuration depending on a few parameters:

    * the debug mode (if `DEBUG == True`, everything is printed to the console and lower log level are applied),
    * the log directory (if set, everything is output to several rotated log files),
    * the log remote URL (to send data to syslog or logd),
    * script name (for determining the log filename).

    Required values in the `settings_dict`:

    *  `DEBUG`: `True` or `False`
    *  `DF_MODULE_NAME`: your project name, used to determine log filenames,
    *  `SCRIPT_NAME`: name of the current Python script ("django", "aiohttp", "gunicorn" or "celery")
    *  `LOG_DIRECTORY`: dirname where log files are written (!),
    *  `LOG_REMOTE_URL`: examples: "syslog+tcp://localhost:514/user", "syslog:///local7"
         "syslog:///dev/log/daemon", "logd:///project_name"
    *  `LOG_REMOTE_ACCESS`: also send HTTP requests to syslog/journald
    *  `SERVER_NAME`: the public name of the server (like "www.example.com")
    *  `SERVER_PORT`: the public port (probably 80 or 443)
    * `LOG_EXCLUDED_COMMANDS`: Django commands that do not write logs
    * `RAVEN_DSN`: `Sentry <https://sentry.io>`_ DSN (URL embedding login and password)
    """

    required_settings = [
        "DEBUG",
        "DF_MODULE_NAME",
        "SCRIPT_NAME",
        "LOG_DIRECTORY",
        "LOG_REMOTE_URL",
        "LOG_REMOTE_ACCESS",
        "SERVER_NAME",
        "SERVER_PORT",
        "LOG_EXCLUDED_COMMANDS",
        "RAVEN_DSN",
    ]
    request_loggers = [
        "aiohttp.access",
        "gunicorn.access",
        "django.server",
        "geventwebsocket.handler",
    ]

    def __init__(self):
        self.formatters = {}
        self.filters = {}
        self.loggers = {}
        self.handlers = {}
        self.root = {}
        self.log_suffix = None
        self.module_name = None
        self.log_directory = None
        self.server_name = None
        self.server_port = None
        self.excluded_commands = {}

    def __call__(self, settings_dict):
        self.module_name = settings_dict["DF_MODULE_NAME"]
        self.server_name = settings_dict["SERVER_NAME"]
        self.server_port = settings_dict["SERVER_PORT"]
        self.excluded_commands = settings_dict["LOG_EXCLUDED_COMMANDS"]
        self.formatters = self.get_default_formatters()
        self.filters = self.get_default_filters()
        self.loggers = self.get_default_loggers()
        self.handlers = self.get_default_handlers()
        self.root = self.get_default_root()
        self.log_suffix = self.get_smart_command_name(
            self.module_name,
            settings_dict["SCRIPT_NAME"],
            sys.argv,
            self.excluded_commands,
        )
        self.log_directory = settings_dict["LOG_DIRECTORY"]
        config = {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": self.formatters,
            "filters": self.filters,
            "handlers": self.handlers,
            "loggers": self.loggers,
            "root": self.root,
        }

        if settings_dict["DEBUG"]:
            warnings.simplefilter("always", DeprecationWarning)
            logging.captureWarnings(True)
            self.loggers["django.request"]["level"] = "DEBUG"
            self.loggers["py.warnings"]["level"] = "DEBUG"
            self.loggers["djangofloor.signals"]["level"] = "DEBUG"
            self.root["level"] = "DEBUG"
            self.add_handler("ROOT", "stdout", level="INFO", formatter="colorized")
            for logger in self.request_loggers:
                self.add_handler(
                    logger, "stderr", level="INFO", formatter="django.server"
                )
            return config
        if settings_dict["RAVEN_DSN"] and is_package_present("raven"):
            self.handlers["sentry"] = {
                "level": "ERROR",
                "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
                "tags": {"application": self.log_suffix},
            }
            self.root["handlers"].append("sentry")
        has_handler = False
        if self.log_directory and self.log_suffix:
            self.add_handler("ROOT", "warning", level="WARN")
            self.add_handler("ROOT", "error", level="ERROR")
            for logger in self.request_loggers:
                self.add_handler(logger, "access", level="INFO", formatter="nocolor")
            has_handler = True
        has_handler = has_handler or self.add_remote_collector(
            settings_dict["LOG_REMOTE_URL"], settings_dict["LOG_REMOTE_ACCESS"]
        )
        if not has_handler or not self.log_suffix:
            # (no file or interactive command) and no logd/syslog => we print to the console (like the debug mode)
            self.add_handler("ROOT", "stdout", level="WARN", formatter="colorized")
            for logger in self.request_loggers:
                self.add_handler(logger, "stderr", formatter="django.server")
        self.root["handlers"].append("mail_admins")
        return config

    def __repr__(self):
        return "%s.%s" % (self.__module__, "log_configuration")

    def add_remote_collector(self, log_remote_url, log_remote_access):
        has_handler = False
        if not log_remote_url:
            return has_handler
        parsed_log_url = urlparse(log_remote_url)
        scheme = parsed_log_url.scheme
        device, sep, facility_name = parsed_log_url.path.rpartition("/")
        if scheme == "syslog" or scheme == "syslog+tcp":
            address, facility, socktype = self.parse_syslog_url(
                parsed_log_url, scheme, device, facility_name
            )
            self.add_handler(
                "ROOT",
                "syslog",
                level="WARN",
                address=address,
                facility=facility,
                socktype=socktype,
                formatter="nocolor",
            )
            if log_remote_access:
                for logger in self.request_loggers:
                    self.add_handler(
                        logger,
                        "syslog",
                        level="INFO",
                        address=address,
                        facility=facility,
                        socktype=socktype,
                        formatter="nocolor",
                    )
            has_handler = True
        elif scheme == "logd":
            identifier = facility_name or self.module_name
            self.add_handler(
                "ROOT",
                "syslog",
                level="WARN",
                SYSLOG_IDENTIFIER=identifier,
                formatter="nocolor",
            )
            if log_remote_access:
                for logger in self.request_loggers:
                    self.add_handler(
                        logger,
                        "syslog",
                        level="INFO",
                        SYSLOG_IDENTIFIER=identifier,
                        formatter="nocolor",
                    )
            has_handler = True
        return has_handler

    def parse_syslog_url(self, parsed_log_url, scheme, device, facility_name):
        import platform
        import socket
        import syslog

        if (
            parsed_log_url.hostname
            and parsed_log_url.port
            and re.match(r"^\d+$", parsed_log_url.port)
        ):
            address = (parsed_log_url.hostname, int(parsed_log_url.port))
        elif device:
            address = device
        elif platform.system() == "Darwin":
            address = "/var/run/syslog"
        elif platform.system() == "Linux":
            address = "/dev/log"
        else:
            address = ("localhost", 514)
        socktype = socket.SOCK_DGRAM if scheme == "syslog" else socket.SOCK_STREAM
        facility = logging.handlers.SysLogHandler.facility_names.get(
            facility_name, syslog.LOG_USER
        )
        return address, facility, socktype

    @property
    def fmt_stderr(self):
        return "colorized" if sys.stderr.isatty() else None

    @property
    def fmt_stdout(self):
        return "colorized" if sys.stdout.isatty() else None

    def get_default_formatters(self):
        name = "%s:%s" % (self.server_name, self.server_port)
        return {
            "django.server": {
                "()": "djangofloor.log.ServerFormatter",
                "format": "%(asctime)s [{}] %(message)s".format(name),
            },
            "nocolor": {
                "()": "logging.Formatter",
                "fmt": "%(asctime)s [{}] [%(levelname)s] %(message)s".format(name),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "colorized": {"()": "djangofloor.log.ColorizedFormatter"},
        }

    def get_default_handlers(self):
        return {
            "mail_admins": {
                "class": "djangofloor.log.AdminEmailHandler",
                "level": "ERROR",
                "include_html": True,
            }
        }

    def get_default_filters(self):
        return {
            "remove_duplicate_warnings": {
                "()": "djangofloor.log.RemoveDuplicateWarnings"
            }
        }

    def get_default_root(self):
        return {"handlers": [], "level": "WARN"}

    def get_default_loggers(self):
        loggers = {
            "py.warnings": {
                "handlers": [],
                "level": "ERROR",
                "propagate": True,
                "filters": ["remove_duplicate_warnings"],
            },
            "pip.vcs": {"handlers": [], "level": "ERROR", "propagate": True},
            "django": {"handlers": [], "level": "WARN", "propagate": True},
            "django.db": {"handlers": [], "level": "WARN", "propagate": True},
            "django.db.backends": {"handlers": [], "level": "WARN", "propagate": True},
            "django.request": {"handlers": [], "level": "INFO", "propagate": True},
            "django.security": {"handlers": [], "level": "WARN", "propagate": True},
            "djangofloor.signals": {"handlers": [], "level": "WARN", "propagate": True},
            "gunicorn.error": {"handlers": [], "level": "WARN", "propagate": True},
        }
        for logger in self.request_loggers:
            loggers[logger] = {"handlers": [], "level": "DEBUG", "propagate": False}
        return loggers

    def add_handler(
        self, logger: str, filename: str, level: str = "WARN", formatter=None, **kwargs
    ):
        """Add a handler to a logger.
        The name of the added handler is unique, so the definition of the handler is also add if required.
        You can use "ROOT" as logger name to target the root logger.

        filename: can be a filename or one of the following special values: "stderr", "stdout", "logd", "syslog"
        """
        if filename == "stderr":
            handler_name = "%s.%s" % (filename, level.lower())
            if formatter in ("django.server", "colorized") and not sys.stderr.isatty():
                formatter = None
            elif formatter:
                handler_name += ".%s" % formatter
            handler = {
                "class": "logging.StreamHandler",
                "level": level,
                "stream": "ext://sys.stderr",
                "formatter": formatter,
            }
        elif filename == "stdout":
            handler_name = "%s.%s" % (filename, level.lower())
            if formatter in ("django.server", "colorized") and not sys.stdout.isatty():
                formatter = None
            elif formatter:
                handler_name += ".%s" % formatter
            handler = {
                "class": "logging.StreamHandler",
                "level": level,
                "stream": "ext://sys.stdout",
                "formatter": formatter,
            }
        elif filename == "syslog":
            handler_name = "%s.%s" % (filename, level.lower())
            handler = {"class": "logging.handlers.SysLogHandler", "level": level}
            handler.update(kwargs)
        elif filename == "logd":
            try:
                # noinspection PyUnresolvedReferences,PyPackageRequirements
                import systemd.journal
            except ImportError:
                warning = Warning(
                    "Unable to import systemd.journal (required to log with journlad)",
                    hint=None,
                    obj="configuration",
                )
                settings_check_results.append(warning)
                # replace logd by writing to a plain-text log
                self.add_handler(logger, level.lower(), level=level)
                return
            handler_name = "%s.%s" % (filename, level.lower())
            handler = {"class": "systemd.journal.JournalHandler", "level": level}
            handler.update(kwargs)
        else:  # basename of a plain-text log
            log_directory = os.path.normpath(self.log_directory)
            if not os.path.isdir(log_directory):
                warning = Warning(
                    'Missing directory, you can create it with \nmkdir -p "%s"'
                    % log_directory,
                    hint=None,
                    obj=log_directory,
                )
                settings_check_results.append(warning)
                self.add_handler(logger, "stdout", level=level, **kwargs)
                return
            basename = "%s-%s.log" % (self.log_suffix, filename)
            log_filename = os.path.join(log_directory, basename)
            try:
                remove = not os.path.exists(log_filename)
                open(log_filename, "a").close()  # ok, we can write
                if (
                    remove
                ):  # but if this file did not exist, we remove it to avoid lot of empty log files...
                    os.remove(log_filename)
            except PermissionError:
                warning_ = Warning(
                    'Unable to write logs in "%s". Unsufficient rights?'
                    % log_directory,
                    hint=None,
                    obj=log_directory,
                )
                settings_check_results.append(warning_)
                self.add_handler(logger, "stdout", level=level, **kwargs)
            handler_name = "%s.%s" % (self.log_suffix, filename)
            handler = {
                "class": "logging.handlers.RotatingFileHandler",
                "maxBytes": 1000000,
                "backupCount": 3,
                "formatter": "nocolor",
                "filename": log_filename,
                "level": level,
            }

        if handler_name not in self.handlers:
            self.handlers[handler_name] = handler
        if logger == "ROOT":
            self.root["handlers"].append(handler_name)
        else:
            self.loggers[logger]["handlers"].append(handler_name)

    @staticmethod
    def get_smart_command_name(module_name, script_name, argv, excluded_commands=None):
        """Return a "smart" name for the current command line.
        If it's an interactive Django command (think to "migrate"), returns None
        It it's the celery worker process, specify the running queues in the name
        Otherwise, add the Django command in the name.

        :param module_name:
        :param script_name:
        :param argv:
        :param excluded_commands:
        :return:
        """
        # command_name = LogConfiguration.resolve_command()
        first_arg = argv[1] if len(argv) >= 2 else script_name
        if len(argv) == 1 and script_name in ("django", "control", "celery"):
            # these scripts just display some info and exists
            return None
        if script_name == "django":
            if excluded_commands and first_arg in excluded_commands:
                return None
            log_suffix = "%s-%s" % (module_name, first_arg)
        elif script_name == "celery":
            log_suffix = "%s-%s" % (module_name, "worker")
            if "worker" in argv:
                index = -1
                if "-Q" in argv:
                    index = argv.index("-Q") + 1
                elif "--queues" in argv:
                    index = argv.index("--queues") + 1
                if 0 <= index < len(argv):
                    log_suffix += "-%s" % (".".join(sorted(argv[index].split(","))))
            elif "beat" in argv:
                log_suffix = "%s-%s" % (module_name, "beat")
            else:
                return None
        else:  # probably 'server', 'gunicorn' or 'aiohttp'
            log_suffix = "%s-%s" % (module_name, script_name)
        return log_suffix

    @staticmethod
    def resolve_command():
        f = extract_stack()
        for (filename, line_number, name, text) in f:
            if filename.endswith("djangofloor/scripts.py") and name in (
                "django",
                "celery",
                "uwsgi",
                "gunicorn",
                "aiohttp",
                "control",
                "server",
            ):
                return name
        return None


log_configuration = LogConfiguration()


class PidFilename:
    required_settings = [
        "PID_DIRECTORY",
        "SCRIPT_NAME",
        "LOG_EXCLUDED_COMMANDS",
        "DF_MODULE_NAME",
        "DEBUG",
    ]

    def __call__(self, settings_dict):
        dirname = settings_dict["PID_DIRECTORY"]
        if not dirname or not os.path.isdir(dirname) or settings_dict["DEBUG"]:
            return None

        info = self.get_command_info(
            settings_dict["DF_MODULE_NAME"],
            settings_dict["SCRIPT_NAME"],
            sys.argv,
            settings_dict["LOG_EXCLUDED_COMMANDS"],
        )
        if info:
            pid = os.getpid()
            filename = os.path.join(dirname, "%s.pid" % pid)
            with open(filename, "w") as fd:
                for k, v in sorted(info.items()):
                    fd.write("%s=%s\n" % (k, v))

            def remove_pid():
                if os.path.isfile(filename):
                    os.unlink(filename)

            atexit.register(remove_pid)
            return filename
        return None

    @staticmethod
    def get_command_info(module_name, script_name, argv, excluded_commands=None):
        """Return a "smart" name for the current command line.
        If it's an interactive Django command (think to "migrate"), returns None
        It it's the celery worker process, specify the running queues in the name
        Otherwise, add the Django command in the name.

        :param module_name:
        :param script_name:
        :param argv:
        :param excluded_commands:
        :return:
        """
        # command_name = LogConfiguration.resolve_command()
        first_arg = argv[1] if len(argv) >= 2 else script_name
        if len(argv) == 1 and script_name in ("django", "control", "celery"):
            # these scripts just display some info and exists
            return None
        result = {
            "MODULE": module_name,
            "COMMAND": first_arg,
            "PID": os.getpid(),
            "SCRIPT_NAME": sys.argv[0],
        }
        if (
            script_name == "django"
            and excluded_commands
            and first_arg in excluded_commands
        ):
            return None
        elif script_name == "celery":
            if "worker" in argv:
                result["COMMAND"] = "worker"
                result["QUEUES"] = "celery"
                index = -1
                if "-Q" in argv:
                    index = argv.index("-Q") + 1
                elif "--queues" in argv:
                    index = argv.index("--queues") + 1
                if 0 <= index < len(argv):
                    result["QUEUES"] = "|".join(sorted(argv[index].split(",")))
            elif "beat" in argv:
                result["COMMAND"] = "beat"
            else:
                return None
        else:  # probably 'server', 'gunicorn' or 'aiohttp'
            result["COMMAND"] = script_name
        return result

    def __repr__(self):
        return "%s.pid_filename" % self.__module__


pid_filename = PidFilename()
