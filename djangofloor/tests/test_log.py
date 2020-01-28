import os
import platform
import socket
import tempfile
from io import StringIO
from unittest import TestCase

from djangofloor.log import LogConfiguration

excluded_commands = {
    "migrate",
    "npm",
    "sendtestemail",
    "clearsessions",
    "createsuperuser",
    "sqlflush",
    "makemigrations",
    "startapp",
    "compilemessages",
    "test",
    "flush",
    "sqlsequencereset",
    "makemessages",
    "remove_stale_contenttypes",
    "dumpdb",
    "collectstatic",
    "config",
    "dumpdata",
    "showmigrations",
    "packaging",
    "sqlmigrate",
    "squashmigrations",
    "gen_dev_files",
    "createcachetable",
    "loaddata",
    "shell",
    "testserver",
    "changepassword",
    "dbshell",
    "inspectdb",
    "check",
    "ping_google",
}


class TestLogConfig(TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.config = LogConfiguration(stdout=StringIO(), stderr=StringIO())

    def test_dev_syslog(self):

        r = self.config(
            {
                "DEBUG": False,
                "DF_MODULE_NAME": "djangofloor",
                "SCRIPT_NAME": "worker",
                "LOG_DIRECTORY": None,
                "LOG_REMOTE_URL": "syslog://",
                "LOG_REMOTE_ACCESS": None,
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "80",
                "LOG_EXCLUDED_COMMANDS": excluded_commands,
                "RAVEN_DSN": None,
                "LOG_LEVEL": None,
            },
            argv=["manage.py", "test"],
        )
        if platform.system() == "Darwin":
            address = "/var/run/syslog"
        elif platform.system() == "Linux":
            address = "/dev/log"
        else:
            address = ("localhost", 514)

        self.assertEqual(
            {
                "version": 1,
                "disable_existing_loggers": True,
                "formatters": {
                    "django.server": {
                        "()": "djangofloor.log.ServerFormatter",
                        "format": "%(asctime)s [localhost:80] %(message)s",
                    },
                    "nocolor": {
                        "()": "logging.Formatter",
                        "fmt": "%(asctime)s [localhost:80] [%(levelname)s] %(message)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                    },
                    "colorized": {"()": "djangofloor.log.ColorizedFormatter"},
                },
                "filters": {
                    "remove_duplicate_warnings": {
                        "()": "djangofloor.log.RemoveDuplicateWarnings"
                    }
                },
                "handlers": {
                    "mail_admins": {
                        "class": "djangofloor.log.AdminEmailHandler",
                        "level": "ERROR",
                        "include_html": True,
                    },
                    "syslog.warn": {
                        "class": "logging.handlers.SysLogHandler",
                        "level": "WARN",
                        "address": address,
                        "facility": 8,
                        "socktype": socket.SOCK_DGRAM,
                    },
                },
                "loggers": {
                    "django": {"handlers": [], "level": "ERROR", "propagate": True},
                    "django.db": {"handlers": [], "level": "ERROR", "propagate": True},
                    "django.db.backends": {
                        "handlers": [],
                        "level": "ERROR",
                        "propagate": True,
                    },
                    "django.request": {
                        "handlers": [],
                        "level": "WARN",
                        "propagate": True,
                    },
                    "django.security": {
                        "handlers": [],
                        "level": "ERROR",
                        "propagate": True,
                    },
                    "djangofloor.signals": {
                        "handlers": [],
                        "level": "WARN",
                        "propagate": True,
                    },
                    "gunicorn.error": {
                        "handlers": [],
                        "level": "WARN",
                        "propagate": True,
                    },
                    "pip.vcs": {"handlers": [], "level": "ERROR", "propagate": True},
                    "py.warnings": {
                        "handlers": [],
                        "level": "ERROR",
                        "propagate": True,
                        "filters": ["remove_duplicate_warnings"],
                    },
                    "aiohttp.access": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "django.server": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "geventwebsocket.handler": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "gunicorn.access": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                },
                "root": {"handlers": ["syslog.warn", "mail_admins"], "level": "WARN"},
            },
            r,
        )

    def test_syslog(self):

        r = self.config(
            {
                "DEBUG": False,
                "DF_MODULE_NAME": "djangofloor",
                "SCRIPT_NAME": "worker",
                "LOG_DIRECTORY": None,
                "LOG_REMOTE_URL": "syslog://localhost:514/user",
                "LOG_REMOTE_ACCESS": None,
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "80",
                "LOG_EXCLUDED_COMMANDS": excluded_commands,
                "RAVEN_DSN": None,
                "LOG_LEVEL": None,
            },
            argv=["manage.py", "test"],
        )
        self.assertEqual(
            {
                "version": 1,
                "disable_existing_loggers": True,
                "formatters": {
                    "django.server": {
                        "()": "djangofloor.log.ServerFormatter",
                        "format": "%(asctime)s [localhost:80] %(message)s",
                    },
                    "nocolor": {
                        "()": "logging.Formatter",
                        "fmt": "%(asctime)s [localhost:80] [%(levelname)s] %(message)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                    },
                    "colorized": {"()": "djangofloor.log.ColorizedFormatter"},
                },
                "filters": {
                    "remove_duplicate_warnings": {
                        "()": "djangofloor.log.RemoveDuplicateWarnings"
                    }
                },
                "handlers": {
                    "mail_admins": {
                        "class": "djangofloor.log.AdminEmailHandler",
                        "level": "ERROR",
                        "include_html": True,
                    },
                    "syslog.warn": {
                        "class": "logging.handlers.SysLogHandler",
                        "level": "WARN",
                        "address": ("localhost", 514),
                        "facility": 1,
                        "socktype": socket.SOCK_DGRAM,
                    },
                },
                "loggers": {
                    "django": {"handlers": [], "level": "ERROR", "propagate": True},
                    "django.db": {"handlers": [], "level": "ERROR", "propagate": True},
                    "django.db.backends": {
                        "handlers": [],
                        "level": "ERROR",
                        "propagate": True,
                    },
                    "django.request": {
                        "handlers": [],
                        "level": "WARN",
                        "propagate": True,
                    },
                    "django.security": {
                        "handlers": [],
                        "level": "ERROR",
                        "propagate": True,
                    },
                    "djangofloor.signals": {
                        "handlers": [],
                        "level": "WARN",
                        "propagate": True,
                    },
                    "gunicorn.error": {
                        "handlers": [],
                        "level": "WARN",
                        "propagate": True,
                    },
                    "pip.vcs": {"handlers": [], "level": "ERROR", "propagate": True},
                    "py.warnings": {
                        "handlers": [],
                        "level": "ERROR",
                        "propagate": True,
                        "filters": ["remove_duplicate_warnings"],
                    },
                    "aiohttp.access": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "django.server": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "geventwebsocket.handler": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "gunicorn.access": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                },
                "root": {"handlers": ["syslog.warn", "mail_admins"], "level": "WARN"},
            },
            r,
        )

    def test_syslog_debug(self):

        r = self.config(
            {
                "DEBUG": False,
                "DF_MODULE_NAME": "djangofloor",
                "SCRIPT_NAME": "worker",
                "LOG_DIRECTORY": None,
                "LOG_REMOTE_URL": "syslog://localhost:514/user",
                "LOG_REMOTE_ACCESS": None,
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "80",
                "LOG_EXCLUDED_COMMANDS": excluded_commands,
                "RAVEN_DSN": None,
                "LOG_LEVEL": "DEBUG",
            },
            argv=["manage.py", "test"],
        )
        self.assertEqual(
            {
                "version": 1,
                "disable_existing_loggers": True,
                "formatters": {
                    "django.server": {
                        "()": "djangofloor.log.ServerFormatter",
                        "format": "%(asctime)s [localhost:80] %(message)s",
                    },
                    "nocolor": {
                        "()": "logging.Formatter",
                        "fmt": "%(asctime)s [localhost:80] [%(levelname)s] %(message)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                    },
                    "colorized": {"()": "djangofloor.log.ColorizedFormatter"},
                },
                "filters": {
                    "remove_duplicate_warnings": {
                        "()": "djangofloor.log.RemoveDuplicateWarnings"
                    }
                },
                "handlers": {
                    "mail_admins": {
                        "class": "djangofloor.log.AdminEmailHandler",
                        "level": "ERROR",
                        "include_html": True,
                    },
                    "syslog.warn": {
                        "class": "logging.handlers.SysLogHandler",
                        "level": "WARN",
                        "address": ("localhost", 514),
                        "facility": 1,
                        "socktype": socket.SOCK_DGRAM,
                    },
                },
                "loggers": {
                    "django": {"handlers": [], "level": "INFO", "propagate": True},
                    "django.db": {"handlers": [], "level": "INFO", "propagate": True},
                    "django.db.backends": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": True,
                    },
                    "django.request": {
                        "handlers": [],
                        "level": "DEBUG",
                        "propagate": True,
                    },
                    "django.security": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": True,
                    },
                    "djangofloor.signals": {
                        "handlers": [],
                        "level": "DEBUG",
                        "propagate": True,
                    },
                    "gunicorn.error": {
                        "handlers": [],
                        "level": "DEBUG",
                        "propagate": True,
                    },
                    "pip.vcs": {"handlers": [], "level": "INFO", "propagate": True},
                    "py.warnings": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": True,
                        "filters": ["remove_duplicate_warnings"],
                    },
                    "aiohttp.access": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "django.server": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "geventwebsocket.handler": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "gunicorn.access": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": False,
                    },
                },
                "root": {"handlers": ["syslog.warn", "mail_admins"], "level": "DEBUG"},
            },
            r,
        )

    def test_not_debug_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            r = self.config(
                {
                    "DEBUG": False,
                    "DF_MODULE_NAME": "djangofloor",
                    "SCRIPT_NAME": "worker",
                    "LOG_DIRECTORY": tmp_dir,
                    "LOG_REMOTE_URL": None,
                    "LOG_REMOTE_ACCESS": None,
                    "SERVER_NAME": "localhost",
                    "SERVER_PORT": "80",
                    "LOG_EXCLUDED_COMMANDS": excluded_commands,
                    "RAVEN_DSN": None,
                    "LOG_LEVEL": None,
                },
                argv=["manage.py", "test"],
            )
            self.assertEqual(
                {
                    "version": 1,
                    "disable_existing_loggers": True,
                    "formatters": {
                        "django.server": {
                            "()": "djangofloor.log.ServerFormatter",
                            "format": "%(asctime)s [localhost:80] %(message)s",
                        },
                        "nocolor": {
                            "()": "logging.Formatter",
                            "fmt": "%(asctime)s [localhost:80] [%(levelname)s] %(message)s",
                            "datefmt": "%Y-%m-%d %H:%M:%S",
                        },
                        "colorized": {"()": "djangofloor.log.ColorizedFormatter"},
                    },
                    "filters": {
                        "remove_duplicate_warnings": {
                            "()": "djangofloor.log.RemoveDuplicateWarnings"
                        }
                    },
                    "handlers": {
                        "mail_admins": {
                            "class": "djangofloor.log.AdminEmailHandler",
                            "level": "ERROR",
                            "include_html": True,
                        },
                        "djangofloor-worker.root": {
                            "class": "logging.handlers.RotatingFileHandler",
                            "maxBytes": 1000000,
                            "backupCount": 3,
                            "formatter": "nocolor",
                            "filename": os.path.join(
                                tmp_dir, "djangofloor-worker-root.log"
                            ),
                            "level": "WARN",
                        },
                        "djangofloor-worker.access": {
                            "class": "logging.handlers.RotatingFileHandler",
                            "maxBytes": 1000000,
                            "backupCount": 3,
                            "formatter": "nocolor",
                            "filename": os.path.join(
                                tmp_dir, "djangofloor-worker-access.log"
                            ),
                            "level": "DEBUG",
                        },
                    },
                    "loggers": {
                        "django": {
                            "handlers": [],
                            "level": "ERROR",
                            "propagate": True,
                        },
                        "django.db": {
                            "handlers": [],
                            "level": "ERROR",
                            "propagate": True,
                        },
                        "django.db.backends": {
                            "handlers": [],
                            "level": "ERROR",
                            "propagate": True,
                        },
                        "django.request": {
                            "handlers": [],
                            "level": "WARN",
                            "propagate": True,
                        },
                        "django.security": {
                            "handlers": [],
                            "level": "ERROR",
                            "propagate": True,
                        },
                        "djangofloor.signals": {
                            "handlers": [],
                            "level": "WARN",
                            "propagate": True,
                        },
                        "gunicorn.error": {
                            "handlers": [],
                            "level": "WARN",
                            "propagate": True,
                        },
                        "pip.vcs": {
                            "handlers": [],
                            "level": "ERROR",
                            "propagate": True,
                        },
                        "py.warnings": {
                            "handlers": [],
                            "level": "ERROR",
                            "propagate": True,
                            "filters": ["remove_duplicate_warnings"],
                        },
                        "aiohttp.access": {
                            "handlers": ["djangofloor-worker.access"],
                            "level": "INFO",
                            "propagate": False,
                        },
                        "django.server": {
                            "handlers": ["djangofloor-worker.access"],
                            "level": "INFO",
                            "propagate": False,
                        },
                        "geventwebsocket.handler": {
                            "handlers": ["djangofloor-worker.access"],
                            "level": "INFO",
                            "propagate": False,
                        },
                        "gunicorn.access": {
                            "handlers": ["djangofloor-worker.access"],
                            "level": "INFO",
                            "propagate": False,
                        },
                    },
                    "root": {
                        "handlers": ["djangofloor-worker.root", "mail_admins"],
                        "level": "WARN",
                    },
                },
                r,
            )

    def test_debug_config(self):

        r = self.config(
            {
                "DEBUG": True,
                "DF_MODULE_NAME": "djangofloor",
                "SCRIPT_NAME": "worker",
                "LOG_DIRECTORY": None,
                "LOG_REMOTE_URL": None,
                "LOG_REMOTE_ACCESS": None,
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "80",
                "LOG_EXCLUDED_COMMANDS": excluded_commands,
                "RAVEN_DSN": None,
                "LOG_LEVEL": None,
            },
            argv=["manage.py", "test"],
        )
        self.assertEqual(
            {
                "version": 1,
                "disable_existing_loggers": True,
                "formatters": {
                    "django.server": {
                        "()": "djangofloor.log.ServerFormatter",
                        "format": "%(asctime)s [localhost:80] %(message)s",
                    },
                    "nocolor": {
                        "()": "logging.Formatter",
                        "fmt": "%(asctime)s [localhost:80] [%(levelname)s] %(message)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                    },
                    "colorized": {"()": "djangofloor.log.ColorizedFormatter"},
                },
                "filters": {
                    "remove_duplicate_warnings": {
                        "()": "djangofloor.log.RemoveDuplicateWarnings"
                    }
                },
                "handlers": {
                    "mail_admins": {
                        "class": "djangofloor.log.AdminEmailHandler",
                        "level": "ERROR",
                        "include_html": True,
                    },
                    "stdout.info": {
                        "class": "logging.StreamHandler",
                        "level": "INFO",
                        "stream": "ext://sys.stdout",
                        "formatter": None,
                    },
                    "stderr.debug": {
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "stream": "ext://sys.stderr",
                        "formatter": None,
                    },
                },
                "loggers": {
                    "aiohttp.access": {
                        "handlers": ["stderr.debug"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "django": {"handlers": [], "level": "INFO", "propagate": True},
                    "django.db": {"handlers": [], "level": "INFO", "propagate": True},
                    "django.db.backends": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": True,
                    },
                    "django.request": {
                        "handlers": [],
                        "level": "DEBUG",
                        "propagate": True,
                    },
                    "django.server": {
                        "handlers": ["stderr.debug"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "django.security": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": True,
                    },
                    "djangofloor.signals": {
                        "handlers": [],
                        "level": "DEBUG",
                        "propagate": True,
                    },
                    "geventwebsocket.handler": {
                        "handlers": ["stderr.debug"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "gunicorn.access": {
                        "handlers": ["stderr.debug"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "gunicorn.error": {
                        "handlers": [],
                        "level": "DEBUG",
                        "propagate": True,
                    },
                    "pip.vcs": {"handlers": [], "level": "INFO", "propagate": True},
                    "py.warnings": {
                        "handlers": [],
                        "level": "INFO",
                        "propagate": True,
                        "filters": ["remove_duplicate_warnings"],
                    },
                },
                "root": {"handlers": ["stdout.info"], "level": "DEBUG"},
            },
            r,
        )

    def test_debug_config_error(self):

        r = self.config(
            {
                "DEBUG": True,
                "DF_MODULE_NAME": "djangofloor",
                "SCRIPT_NAME": "worker",
                "LOG_DIRECTORY": None,
                "LOG_REMOTE_URL": None,
                "LOG_REMOTE_ACCESS": None,
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "80",
                "LOG_EXCLUDED_COMMANDS": excluded_commands,
                "RAVEN_DSN": None,
                "LOG_LEVEL": "ERROR",
            }
        )
        self.assertEqual(
            {
                "version": 1,
                "disable_existing_loggers": True,
                "formatters": {
                    "django.server": {
                        "()": "djangofloor.log.ServerFormatter",
                        "format": "%(asctime)s [localhost:80] %(message)s",
                    },
                    "nocolor": {
                        "()": "logging.Formatter",
                        "fmt": "%(asctime)s [localhost:80] [%(levelname)s] %(message)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                    },
                    "colorized": {"()": "djangofloor.log.ColorizedFormatter"},
                },
                "filters": {
                    "remove_duplicate_warnings": {
                        "()": "djangofloor.log.RemoveDuplicateWarnings"
                    }
                },
                "handlers": {
                    "mail_admins": {
                        "class": "djangofloor.log.AdminEmailHandler",
                        "level": "ERROR",
                        "include_html": True,
                    },
                    "stdout.info": {
                        "class": "logging.StreamHandler",
                        "level": "INFO",
                        "stream": "ext://sys.stdout",
                        "formatter": None,
                    },
                    "stderr.debug": {
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "stream": "ext://sys.stderr",
                        "formatter": None,
                    },
                },
                "loggers": {
                    "aiohttp.access": {
                        "handlers": ["stderr.debug"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "django": {"handlers": [], "level": "CRITICAL", "propagate": True},
                    "django.db": {
                        "handlers": [],
                        "level": "CRITICAL",
                        "propagate": True,
                    },
                    "django.db.backends": {
                        "handlers": [],
                        "level": "CRITICAL",
                        "propagate": True,
                    },
                    "django.request": {
                        "handlers": [],
                        "level": "ERROR",
                        "propagate": True,
                    },
                    "django.server": {
                        "handlers": ["stderr.debug"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "django.security": {
                        "handlers": [],
                        "level": "CRITICAL",
                        "propagate": True,
                    },
                    "djangofloor.signals": {
                        "handlers": [],
                        "level": "ERROR",
                        "propagate": True,
                    },
                    "geventwebsocket.handler": {
                        "handlers": ["stderr.debug"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "gunicorn.access": {
                        "handlers": ["stderr.debug"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "gunicorn.error": {
                        "handlers": [],
                        "level": "ERROR",
                        "propagate": True,
                    },
                    "pip.vcs": {
                        "handlers": [],
                        "level": "CRITICAL",
                        "propagate": True,
                    },
                    "py.warnings": {
                        "handlers": [],
                        "level": "CRITICAL",
                        "propagate": True,
                        "filters": ["remove_duplicate_warnings"],
                    },
                },
                "root": {"handlers": ["stdout.info"], "level": "ERROR"},
            },
            r,
        )
