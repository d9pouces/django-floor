# -*- coding: utf-8 -*-
"""Mapping between .ini config files and Django settings
=====================================================

This mapping can be overriden in `yourproject.iniconf:INI_MAPPING`.
The `INI_MAPPING` must be a list of :class:`djangofloor.conf.fields.ConfigField`, giving where to search in a .ini file,
the corresponding Django setting value and how to convert from one format to the another.
"""
from __future__ import unicode_literals, print_function, absolute_import

from djangofloor.conf.callables import allauth_providers
from djangofloor.conf.fields import CharConfigField, IntegerConfigField, BooleanConfigField, ConfigField, bool_setting, \
    ListConfigField

__author__ = 'Matthieu Gallet'


def x_accel_converter(value):
    if bool_setting(value):
        return [('{MEDIA_ROOT}/', '{MEDIA_URL}'), ]
    return []


REDIS_MAPPING = [
    IntegerConfigField('cache.db', 'CACHE_REDIS_DB',
                       help_str='Database number of the Redis Cache DB.\n'
                                'Python package "django-redis" is required.'),
    CharConfigField('cache.host', 'CACHE_REDIS_HOST', help_str='Redis Cache DB host'),
    CharConfigField('cache.password', 'CACHE_REDIS_PASSWORD', help_str='Redis Cache DB password (if required)'),
    IntegerConfigField('cache.port', 'CACHE_REDIS_PORT', help_str='Redis Cache DB port'),
    IntegerConfigField('sessions.db', 'SESSION_REDIS_DB',
                       help_str='Database number of the Redis sessions DB\n'
                                'Python package "django-redis-sessions" is required.'),
    CharConfigField('sessions.host', 'SESSION_REDIS_HOST', help_str='Redis sessions DB host'),
    CharConfigField('sessions.password', 'SESSION_REDIS_PASSWORD', help_str='Redis sessions DB password (if required)'),
    IntegerConfigField('sessions.port', 'SESSION_REDIS_PORT', help_str='Redis sessions DB port'),
]

CELERY_MAPPING = [
    IntegerConfigField('websocket.db', 'WEBSOCKET_REDIS_DB', help_str='Database number of the Redis websocket DB'),
    CharConfigField('websocket.host', 'WEBSOCKET_REDIS_HOST', help_str='Redis websocket DB host'),
    CharConfigField('websocket.password', 'WEBSOCKET_REDIS_PASSWORD',
                    help_str='Redis websocket DB password (if required)'),
    IntegerConfigField('websocket.port', 'WEBSOCKET_REDIS_PORT', help_str='Redis websocket DB port'),

    IntegerConfigField('celery.db', 'CELERY_DB',
                       help_str='Database number of the Redis Celery DB\n'
                                'Celery is used for processing background tasks and websockets.'),
    CharConfigField('celery.host', 'CELERY_HOST', help_str='Redis Celery DB host'),
    CharConfigField('celery.password', 'CELERY_PASSWORD', help_str='Redis Celery DB password (if required)'),
    IntegerConfigField('celery.port', 'CELERY_PORT', help_str='Redis Celery DB port'),
]

BASE_MAPPING = [
    CharConfigField('global.admin_email', 'ADMIN_EMAIL',
                    help_str='e-mail address for receiving logged errors'),
    CharConfigField('global.data', 'LOCAL_PATH',
                    help_str='where all data will be stored '
                             '(static/uploaded/temporary files, …)'
                             'If you change it, you must run the collectstatic and migrate commands again.\n'),
    CharConfigField('global.language_code', 'LANGUAGE_CODE', help_str='default to fr_FR'),
    CharConfigField('global.listen_address', 'LISTEN_ADDRESS',
                    help_str='address used by your web server.'),
    CharConfigField('global.server_url', 'SERVER_BASE_URL',
                    help_str='Public URL of your website. \n'
                             'Default to "http://listen_address" but should '
                             'be ifferent if you use a reverse proxy like '
                             'Apache or Nginx. Example: http://www.example.org.'),
    CharConfigField('global.time_zone', 'TIME_ZONE', help_str='default to Europe/Paris'),
    CharConfigField('global.log_remote_url', 'LOG_REMOTE_URL',
                    help_str='Send logs to a syslog or systemd log daemon. \n'
                             'Examples: syslog+tcp://localhost:514/user, syslog:///local7, '
                             'syslog:///dev/log/daemon, logd:///project_name'),

    CharConfigField('database.db', 'DATABASE_NAME', help_str='Main database name (or path of the sqlite3 database)'),
    CharConfigField('database.engine', 'DATABASE_ENGINE',
                    help_str='Main database engine ("mysql", "postgresql", "sqlite3", "oracle", or the dotted name of '
                             'the Django backend)'),
    CharConfigField('database.host', 'DATABASE_HOST', help_str='Main database host'),
    CharConfigField('database.password', 'DATABASE_PASSWORD', help_str='Main database password'),
    IntegerConfigField('database.port', 'DATABASE_PORT', help_str='Main database port'),
    CharConfigField('database.user', 'DATABASE_USER', help_str='Main database user'),

    CharConfigField('email.host', 'EMAIL_HOST', help_str='SMTP server'),
    CharConfigField('email.password', 'EMAIL_HOST_PASSWORD', help_str='SMTP password'),
    IntegerConfigField('email.port', 'EMAIL_PORT', help_str='SMTP port (often 25, 465 or 587)'),
    CharConfigField('email.user', 'EMAIL_HOST_USER', help_str='SMTP user'),
    BooleanConfigField('email.use_tls', 'EMAIL_USE_TLS', help_str='"true" if your SMTP uses STARTTLS '
                                                                  '(often on port 587)'),
    BooleanConfigField('email.use_ssl', 'EMAIL_USE_SSL', help_str='"true" if your SMTP uses SSL (often on port 465)'),

]

SENDFILE_MAPPING = [
    BooleanConfigField('global.use_apache', 'USE_X_SEND_FILE',
                       help_str='"true" if Apache is used as reverse-proxy and mod_xsendfile.'),
    ConfigField('global.use_nginx', 'X_ACCEL_REDIRECT', from_str=x_accel_converter,
                to_str=lambda x: 'True' if x else 'False',
                help_str='"true" is nginx is used as reverse-proxy and x-accel-redirect.'),
]

AUTH_MAPPING = [
    CharConfigField('auth.remote_user_header', 'DF_REMOTE_USER_HEADER',
                    help_str='Set it if you want to use HTTP authentication, a common value is "HTTP-REMOTE-USER".'),
    ListConfigField('auth.remote_user_groups', 'DF_DEFAULT_GROUPS',
                    help_str='Comma-separated list of groups of new users, authenticated by a HTTP header.'),
    BooleanConfigField('auth.allow_basic_auth', 'USE_HTTP_BASIC_AUTH',
                       help_str='Set to "true" if you want to allow HTTP basic auth, using the Django database.'),
    CharConfigField('auth.ldap_server_url', 'AUTH_LDAP_SERVER_URI',
                    help_str='URL of your LDAP server, like "ldap://ldap.example.com". '
                             'Python packages "pyldap" and "django-auth-ldap" must be installed.'),
    CharConfigField('auth.ldap_bind_dn', 'AUTH_LDAP_BIND_DN', help_str='Bind dn for LDAP authentication'),
    CharConfigField('auth.ldap_bind_password', 'AUTH_LDAP_BIND_PASSWORD',
                    help_str='Bind password for LDAP authentication'),
    CharConfigField('auth.ldap_search_base', 'AUTH_LDAP_SEARCH_BASE',
                    help_str='Search base for LDAP authentication, like "ou=users,dc=example,dc=com".'),
    CharConfigField('auth.ldap_filter', 'AUTH_LDAP_FILTER',
                    help_str='Filter for LDAP authentication, like "(uid=%(user)s)".'),
    CharConfigField('auth.ldap_direct_bind', 'AUTH_LDAP_USER_DN_TEMPLATE',
                    help_str='Set it for a direct LDAP bind, like "uid=%(user)s,ou=users,dc=example,dc=com"'),
    BooleanConfigField('auth.ldap_start_tls', 'AUTH_LDAP_START_TLS', 'Set to "true" if you want to use StartTLS.'),

]
ALLAUTH_MAPPING = [
    ListConfigField('auth.oauth2_providers', 'ALLAUTH_PROVIDERS',
                    help_str='Comma-separated OAuth2 providers, among "%s". "django-allauth" package must be installed.'
                             % '","'.join(allauth_providers)),
]

INI_MAPPING = BASE_MAPPING + REDIS_MAPPING + CELERY_MAPPING + AUTH_MAPPING
