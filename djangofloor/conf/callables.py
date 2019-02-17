"""Callables settings
==================

Dynamic
"""

import os
import re
from collections import OrderedDict
from configparser import RawConfigParser
from urllib.parse import urlparse

from django.core.checks import Error
from django.utils.crypto import get_random_string
from pkg_resources import get_distribution, DistributionNotFound, VersionConflict

from djangofloor.checks import settings_check_results, missing_package
from djangofloor.conf.config_values import ExpandIterable, ConfigValue
from djangofloor.conf.social_providers import SOCIAL_PROVIDER_APPS
from djangofloor.utils import is_package_present

__author__ = "Matthieu Gallet"

_default_database_engines = {
    "mysql": "django.db.backends.mysql",
    "mariadb": "django.db.backends.mysql",
    "oracle": "django.db.backends.oracle",
    "postgres": "django.db.backends.postgresql",
    "postgresql": "django.db.backends.postgresql",
    "sqlite": "django.db.backends.sqlite3",
    "sqlite3": "django.db.backends.sqlite3",
}


def database_engine(settings_dict):
    """Allow to use aliases for database engines, as well as the default dotted name"""
    engine = _default_database_engines.get(
        settings_dict["DATABASE_ENGINE"].lower(), settings_dict["DATABASE_ENGINE"]
    )
    if engine == "django.db.backends.postgresql":
        try:
            get_distribution("psycopg2-binary")
        except DistributionNotFound:
            try:
                get_distribution("psycopg2")
            except DistributionNotFound:
                settings_check_results.append(
                    missing_package("psycopg2-binary", " to use PostgreSQL database")
                )
    elif engine == "django.db.backends.oracle":
        try:
            get_distribution("cx_Oracle")
        except DistributionNotFound:
            settings_check_results.append(
                missing_package("cx_Oracle", " to use Oracle database")
            )
    elif engine == "django.db.backends.mysql":
        try:
            get_distribution("mysqlclient")
        except DistributionNotFound:
            settings_check_results.append(
                missing_package("mysqlclient", " to use MySQL or MariaDB database")
            )
    return engine


database_engine.required_settings = ["DATABASE_ENGINE"]


def databases(settings_dict):
    """Build a complete DATABASES setting, taking into account the `DATABASE_URL` environment variable if present
     (used on the Heroku platform)."""
    engine = database_engine(settings_dict)
    name = settings_dict["DATABASE_NAME"]
    user = settings_dict["DATABASE_USER"]
    options = settings_dict["DATABASE_OPTIONS"]
    password = settings_dict["DATABASE_PASSWORD"]
    host = settings_dict["DATABASE_HOST"]
    port = settings_dict["DATABASE_PORT"]
    if "DATABASE_URL" in os.environ:  # Used on Heroku environment
        parsed = urlparse(os.environ["DATABASE_URL"])
        engine = database_engine({"DATABASE_ENGINE": parsed.scheme})
        user = parsed.username
        name = parsed.path[1:]
        password = parsed.password
        host = parsed.hostname
        port = parsed.port
    return {
        "default": {
            "ENGINE": engine,
            "NAME": name,
            "USER": user,
            "OPTIONS": options,
            "PASSWORD": password,
            "HOST": host,
            "PORT": port,
        }
    }


databases.required_settings = [
    "DATABASE_ENGINE",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_OPTIONS",
    "DATABASE_PASSWORD",
    "DATABASE_HOST",
    "DATABASE_PORT",
]


class RedisSmartSetting:
    """Handle values required for Redis configuration, as well as Heroku's standard environment variables.
    Can be used as :class:`djangofloor.conf.config_values.CallableSetting`.
    """

    config_values = ["PROTOCOL", "HOST", "PORT", "DB", "PASSWORD"]

    def __init__(
        self, prefix="", env_variable="REDIS_URL", fmt="url", extra_values=None
    ):
        self.fmt = fmt
        self.prefix = prefix
        self.env_variable = env_variable
        self.required_settings = [prefix + x for x in self.config_values]
        self.extra_values = extra_values

    def __call__(self, settings_dict):
        values = {x: settings_dict[self.prefix + x] for x in self.config_values}
        values["AUTH"] = ""
        if (
            values["PROTOCOL"] == "redis"
            and self.env_variable
            and self.env_variable in os.environ
        ):
            redis_url = urlparse(os.environ[self.env_variable])
            values["HOST"] = redis_url.hostname
            values["PORT"] = redis_url.port
            values["PASSWORD"] = redis_url.password
        if values["PASSWORD"]:
            values["AUTH"] = ":%s@" % values["PASSWORD"]
        if self.fmt == "url":
            return "%(PROTOCOL)s://%(AUTH)s%(HOST)s:%(PORT)s/%(DB)s" % values
        elif self.fmt == "dict":
            result = {
                "host": values["HOST"] or "localhost",
                "port": int(values["PORT"] or 6379),
                "db": int(values["DB"] or 0),
                "password": values["PASSWORD"] or "",
            }
            if self.extra_values:
                result.update(self.extra_values)
            return result
        raise ValueError("Unknown RedisSmartSetting format '%s'" % self.fmt)

    def __repr__(self):
        p = self.prefix
        if self.prefix.endswith("REDIS_"):
            p = self.prefix[:-6]
        return "%s.%sredis_%s" % (self.__module__, p.lower(), self.fmt)


cache_redis_url = RedisSmartSetting(prefix="CACHE_", fmt="url")
celery_redis_url = RedisSmartSetting(prefix="CELERY_", fmt="url")
session_redis_dict = RedisSmartSetting(
    prefix="SESSION_REDIS_", fmt="dict", extra_values={"prefix": "session"}
)
websocket_redis_dict = RedisSmartSetting(prefix="WEBSOCKET_REDIS_", fmt="dict")


def smart_hostname(settings_dict):
    """
    By default, use the listen address and port as server name.
    Use the "HEROKU_APP_NAME" environment variable if present.

    :param settings_dict:
    :return:
    """
    if "HEROKU_APP_NAME" in os.environ:
        return "https://%s.herokuapp.com/" % os.environ["HEROKU_APP_NAME"]
    return "http://%s/" % settings_dict["LISTEN_ADDRESS"]


smart_hostname.required_settings = ["LISTEN_ADDRESS"]


class DefaultListenAddress(ConfigValue):
    def get_value(self, merger, provider_name: str, setting_name: str):
        port = os.environ.get("PORT", "")
        if re.match(r"^\d+$", port) and 1 <= int(port) <= 65535:
            return "0.0.0.0:%s" % port
        return "localhost:%d" % self.value


def template_setting(settings_dict):
    loaders = [
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    if settings_dict["DEBUG"]:
        backend = {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "NAME": "default",
            "DIRS": settings_dict["TEMPLATE_DIRS"],
            "OPTIONS": {
                "context_processors": settings_dict["TEMPLATE_CONTEXT_PROCESSORS"],
                "loaders": loaders,
                "debug": True,
            },
        }
    else:
        backend = {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "NAME": "default",
            "DIRS": settings_dict["TEMPLATE_DIRS"],
            "OPTIONS": {
                "context_processors": settings_dict["TEMPLATE_CONTEXT_PROCESSORS"],
                "debug": False,
                "loaders": [("django.template.loaders.cached.Loader", loaders)],
            },
        }
    return [backend]


template_setting.required_settings = [
    "DEBUG",
    "TEMPLATE_DIRS",
    "TEMPLATE_CONTEXT_PROCESSORS",
]


def allowed_hosts(settings_dict):
    result = {"127.0.0.1", "::1", "localhost"}
    listened_ip, sep, port = settings_dict["LISTEN_ADDRESS"].rpartition(":")
    if sep == ":" and listened_ip not in ("::", "0.0.0.0"):
        result.add(listened_ip)
    result.add(settings_dict["SERVER_NAME"])
    return list(sorted(result))


allowed_hosts.required_settings = ["SERVER_NAME", "LISTEN_ADDRESS"]


def secure_hsts_seconds(settings_dict):
    if settings_dict["USE_SSL"]:
        return 86400
    return 0


secure_hsts_seconds.required_settings = ["USE_SSL"]


# noinspection PyUnresolvedReferences
def cache_setting(settings_dict):
    """Automatically compute cache settings:
      * if debug mode is set, then caching is disabled
      * if django_redis is available, then Redis is used for caching
      * else memory is used

    :param settings_dict:
    :return:
    """
    parsed_url = urlparse(settings_dict["CACHE_URL"])
    if settings_dict["DEBUG"]:
        return {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    elif settings_dict["USE_REDIS_CACHE"] and parsed_url.scheme == "redis":
        return {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": "{CACHE_URL}",
                "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            }
        }
    elif parsed_url.scheme == "memcache":
        location = "%s:%s" % (
            parsed_url.hostname or "localhost",
            parsed_url.port or 11211,
        )
        return {
            "default": {
                "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
                "LOCATION": location,
            }
        }
    return {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }


cache_setting.required_settings = ["USE_REDIS_CACHE", "DEBUG", "CACHE_URL"]


def url_parse_server_name(settings_dict):
    """Return the public hostname, given the public base URL

    >>> url_parse_server_name({'SERVER_BASE_URL': 'https://demo.example.org/'})
    'demo.example.org'

    """
    return urlparse(settings_dict["SERVER_BASE_URL"]).hostname


url_parse_server_name.required_settings = ["SERVER_BASE_URL"]


def url_parse_server_port(settings_dict):
    """Return the public port, given the public base URL

    >>> url_parse_server_port({'SERVER_BASE_URL': 'https://demo.example.org/', 'USE_SSL': True})
    443
    >>> url_parse_server_port({'SERVER_BASE_URL': 'http://demo.example.org/', 'USE_SSL': False})
    80
    >>> url_parse_server_port({'SERVER_BASE_URL': 'https://demo.example.org:8010/', 'USE_SSL': True})
    8010

    """
    return (
        urlparse(settings_dict["SERVER_BASE_URL"]).port
        or (settings_dict["USE_SSL"] and 443)
        or 80
    )


url_parse_server_port.required_settings = ["SERVER_BASE_URL", "USE_SSL"]


def url_parse_server_protocol(settings_dict):
    """Return the public HTTP protocol, given the public base URL

    >>> url_parse_server_protocol({'USE_SSL': True})
    'https'

    >>> url_parse_server_protocol({'USE_SSL': False})
    'http'

    """
    return "https" if settings_dict["USE_SSL"] else "http"


url_parse_server_protocol.required_settings = ["USE_SSL"]


def url_parse_prefix(settings_dict):
    """Return the public URL prefix, given the public base URL

    >>> url_parse_prefix({'SERVER_BASE_URL': 'https://demo.example.org/demo/'})
    '/demo/'
    >>> url_parse_prefix({'SERVER_BASE_URL': 'http://demo.example.org/'})
    '/'
    >>> url_parse_prefix({'SERVER_BASE_URL': 'https://demo.example.org:8010'})
    '/'

    """
    p = urlparse(settings_dict["SERVER_BASE_URL"]).path
    if not p.endswith("/"):
        p += "/"
    return p


url_parse_prefix.required_settings = ["SERVER_BASE_URL"]


def url_parse_ssl(settings_dict):
    """Return True if the public URL uses https

    >>> url_parse_ssl({'SERVER_BASE_URL': 'https://demo.example.org/demo/'})
    True
    >>> url_parse_ssl({'SERVER_BASE_URL': 'http://demo.example.org/'})
    False

    """
    return urlparse(settings_dict["SERVER_BASE_URL"]).scheme == "https"


url_parse_ssl.required_settings = ["SERVER_BASE_URL"]


def use_x_forwarded_for(settings_dict):
    """Return `True` if this server is assumed to be behind a reverse proxy.
     Heuristic: the external port (in SERVER_PORT) is different from the actually listened port (in LISTEN_ADDRESS).

     >>> use_x_forwarded_for({'SERVER_PORT': 8000, 'LISTEN_ADDRESS': 'localhost:8000'})
     False
     >>> use_x_forwarded_for({'SERVER_PORT': 443, 'LISTEN_ADDRESS': 'localhost:8000'})
     True

    """
    listen_address, sep, listen_port = settings_dict["LISTEN_ADDRESS"].rpartition(":")
    if not re.match(r"\d+", listen_port):
        raise ValueError("Invalid LISTEN_ADDRESS port %s" % listen_port)
    return int(listen_port) != settings_dict["SERVER_PORT"]


use_x_forwarded_for.required_settings = ["SERVER_PORT", "LISTEN_ADDRESS"]


def project_name(settings_dict):
    """Transform the base module name into a nicer project name

    >>> project_name({'DF_MODULE_NAME': 'my_project'})
    'My Project'

    :param settings_dict:
    :return:
    """

    return " ".join(
        [
            x.capitalize()
            for x in settings_dict["DF_MODULE_NAME"].replace("_", " ").split()
        ]
    )


project_name.required_settings = ["DF_MODULE_NAME"]


def allauth_provider_apps(settings_dict):
    parser = RawConfigParser()
    config = settings_dict["ALLAUTH_APPLICATIONS_CONFIG"]
    if not os.path.isfile(config):
        return []
    # noinspection PyBroadException
    try:
        parser.read([config])
    except Exception:
        settings_check_results.append(
            Error("Invalid config file. %s" % config, obj="configuration")
        )
        return []
    return [
        parser.get(section, "django_app")
        for section in parser.sections()
        if parser.has_option(section, "django_app")
    ]


allauth_provider_apps.required_settings = ["ALLAUTH_APPLICATIONS_CONFIG"]


class InstalledApps:
    """Provide a complete `INSTALLED_APPS` list, transparently adding common third-party packages.
     Specifically handle apps required by django-allauth (one by allowed method).

    """

    default_apps = [
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.humanize",
        "django.contrib.sitemaps",
        "django.contrib.sites",
        ExpandIterable("DF_INSTALLED_APPS"),
        "bootstrap3",
        "djangofloor",
        "django.contrib.staticfiles",
        "django.contrib.admin",
    ]
    common_third_parties = OrderedDict(
        [
            ("USE_DEBUG_TOOLBAR", "debug_toolbar"),
            ("USE_PIPELINE", "pipeline"),
            ("USE_REST_FRAMEWORK", "rest_framework"),
            ("USE_PAM_AUTHENTICATION", "django_pam"),
            ("RAVEN_DSN", "raven.contrib.django.raven_compat"),
        ]
    )
    required_settings = ["ALLAUTH_PROVIDER_APPS", "USE_ALL_AUTH"] + list(
        common_third_parties
    )
    social_apps = SOCIAL_PROVIDER_APPS

    def __call__(self, settings_dict):
        apps = self.default_apps
        apps += self.process_django_allauth(settings_dict)
        apps += self.process_third_parties(settings_dict)
        return apps

    def process_third_parties(self, settings_dict):
        result = []
        for k, v in self.common_third_parties.items():
            package_name = v.partition(".")[0]
            if not settings_dict[k]:
                continue
            elif not is_package_present(package_name):
                settings_check_results.append(missing_package(package_name, ""))
                continue
            result.append(v)
        return result

    def process_django_allauth(self, settings_dict):
        if (
            not settings_dict["USE_ALL_AUTH"]
            and not settings_dict["ALLAUTH_PROVIDER_APPS"]
        ):
            return []
        try:
            get_distribution("django-allauth")
        except DistributionNotFound:
            settings_check_results.append(
                missing_package(
                    "django-allauth", " to use OAuth2 or OpenID authentication"
                )
            )
            return []
        if "django.contrib.sites" not in self.default_apps:
            settings_check_results.append(
                Error(
                    '"django.contrib.sites" app must be enabled.',
                    obj="configuration",
                    id="djangofloor.E001",
                )
            )
            return []
        result = [
            "allauth",
            "allauth.account",
            "allauth.socialaccount",
            "allauth.socialaccount.providers.openid",
        ]
        if settings_dict["ALLAUTH_PROVIDER_APPS"]:
            result += [
                k
                for k in settings_dict["ALLAUTH_PROVIDER_APPS"]
                if k in self.social_apps
            ]
        return result

    def __repr__(self):
        return "%s.%s" % (self.__module__, "installed_apps")


installed_apps = InstalledApps()


def generate_secret_key(django_ready, length=60):
    if not django_ready:
        return get_random_string(length=length)
    from django.conf import settings

    return settings.SECRET_KEY


def required_packages(settings_dict):
    """
    Return a sorted list of the Python packages required by the current project (with their dependencies).
    A warning is added for each missing package.

    :param settings_dict:
    :return:
    """

    def get_requirements(package_name, parent=None):
        try:
            yield str(package_name)
            d = get_distribution(package_name)
            for r in d.requires():
                for required_package in get_requirements(r, parent=package_name):
                    yield str(required_package)
        except DistributionNotFound:
            settings_check_results.append(
                missing_package(str(package_name), " by %s" % parent)
            )
        except VersionConflict:
            settings_check_results.append(
                missing_package(str(package_name), " by %s" % parent)
            )

    return list(
        sorted(
            set(
                get_requirements(
                    settings_dict["DF_MODULE_NAME"],
                    parent=settings_dict["DF_MODULE_NAME"],
                )
            )
        )
    )


required_packages.required_settings = ["DF_MODULE_NAME"]


class ExcludedDjangoCommands:
    required_settings = ["DEVELOPMENT", "USE_CELERY", "DEBUG"]

    def __call__(self, settings_dict):
        result = {"startproject", "diffsettings"}
        if not settings_dict["DEVELOPMENT"]:
            result |= {
                "startapp",
                "findstatic",
                "npm",
                "packaging",
                "gen_dev_files",
                "gen_install",
                "dockerize",
                "bdist_deb_django",
                "makemigrations",
                "makemessages",
                "inspectdb",
                "compilemessages",
                "remove_stale_contenttypes",
                "squashmigrations",
            }
        if not settings_dict["USE_CELERY"]:
            result |= {"celery", "worker"}
        if not settings_dict["DEBUG"] and not settings_dict["DEVELOPMENT"]:
            result |= {"testserver", "test", "runserver"}
        return result

    def __repr__(self):
        return "%s.%s" % (self.__module__, "excluded_django_commands")


excluded_django_commands = ExcludedDjangoCommands()
