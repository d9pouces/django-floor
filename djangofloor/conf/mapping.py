"""Mapping between .ini config files and Django settings
=====================================================

This mapping can be overriden in `yourproject.iniconf:INI_MAPPING`.
The `INI_MAPPING` must be a list of :class:`djangofloor.conf.fields.ConfigField`, giving where to search in a .ini file,
the corresponding Django setting value and how to convert from one format to the another.
"""

from djangofloor.conf.fields import (
    CharConfigField,
    IntegerConfigField,
    BooleanConfigField,
    ConfigField,
    bool_setting,
    ListConfigField,
    ChoiceConfigFile,
)
from djangofloor.conf.social_providers import SOCIAL_PROVIDER_APPS

__author__ = "Matthieu Gallet"


def x_accel_converter(value):
    if bool_setting(value):
        return [("{MEDIA_ROOT}/", "{MEDIA_URL}")]
    return []


REDIS_MAPPING = [
    IntegerConfigField(
        "cache.db",
        "CACHE_DB",
        help_str="Database number (redis only). \n"
        'Python package "django-redis" is also required to use Redis.',
    ),
    CharConfigField(
        "cache.host", "CACHE_HOST", help_str="cache server host (redis or memcache)"
    ),
    CharConfigField(
        "cache.password",
        "CACHE_PASSWORD",
        help_str="cache server password (if required by redis)",
    ),
    IntegerConfigField(
        "cache.port", "CACHE_PORT", help_str="cache server port (redis or memcache)"
    ),
    ChoiceConfigFile(
        "cache.engine",
        "CACHE_PROTOCOL",
        choices={
            "redis": "redis",
            "memcache": "memcache",
            "locmem": "locmem",
            "file": "file",
        },
        help_str='cache storage engine ("locmem", "redis" or "memcache")',
    ),
    IntegerConfigField(
        "sessions.db",
        "SESSION_REDIS_DB",
        help_str="Database number of the Redis sessions DB\n"
        'Python package "django-redis-sessions" is required.',
    ),
    CharConfigField(
        "sessions.host", "SESSION_REDIS_HOST", help_str="Redis sessions DB host"
    ),
    CharConfigField(
        "sessions.password",
        "SESSION_REDIS_PASSWORD",
        help_str="Redis sessions DB password (if required)",
    ),
    IntegerConfigField(
        "sessions.port", "SESSION_REDIS_PORT", help_str="Redis sessions DB port"
    ),
]

CELERY_MAPPING = [
    IntegerConfigField(
        "websocket.db",
        "WEBSOCKET_REDIS_DB",
        help_str="Database number of the Redis websocket DB",
    ),
    CharConfigField(
        "websocket.host", "WEBSOCKET_REDIS_HOST", help_str="Redis websocket DB host"
    ),
    CharConfigField(
        "websocket.password",
        "WEBSOCKET_REDIS_PASSWORD",
        help_str="Redis websocket DB password (if required)",
    ),
    IntegerConfigField(
        "websocket.port", "WEBSOCKET_REDIS_PORT", help_str="Redis websocket DB port"
    ),
    IntegerConfigField(
        "celery.db",
        "CELERY_DB",
        help_str="Database number of the Redis Celery DB\n"
        "Celery is used for processing background tasks and websockets.",
    ),
    CharConfigField("celery.host", "CELERY_HOST", help_str="Redis Celery DB host"),
    CharConfigField(
        "celery.password",
        "CELERY_PASSWORD",
        help_str="Redis Celery DB password (if required)",
    ),
    IntegerConfigField("celery.port", "CELERY_PORT", help_str="Redis Celery DB port"),
    IntegerConfigField(
        "celery.processes", "CELERY_PROCESSES", help_str="number of Celery processes"
    ),
]

BASE_MAPPING = [
    CharConfigField(
        "global.admin_email",
        "ADMIN_EMAIL",
        help_str="e-mail address for receiving logged errors",
    ),
    CharConfigField(
        "global.data",
        "LOCAL_PATH",
        help_str="where all data will be stored (static/uploaded/temporary files, …). "
        "If you change it, you must run the collectstatic and migrate commands again.\n",
    ),
    CharConfigField(
        "global.language_code", "LANGUAGE_CODE", help_str="default to fr_FR"
    ),
    CharConfigField(
        "global.listen_address",
        "LISTEN_ADDRESS",
        help_str="address used by your web server.",
    ),
    CharConfigField(
        "global.ssl_keyfile",
        "DF_SERVER_SSL_KEY",
        help_str="Private SSL key (if you do not use a reverse proxy with SSL)",
    ),
    CharConfigField(
        "global.ssl_certfile",
        "DF_SERVER_SSL_CERTIFICATE",
        help_str="Public SSL certificate (if you do not use a reverse proxy with SSL)",
    ),
    CharConfigField(
        "global.server_url",
        "SERVER_BASE_URL",
        help_str="Public URL of your website. \n"
        'Default to "http://{listen_address}/" but should '
        "be different if you use a reverse proxy like "
        "Apache or Nginx. Example: http://www.example.org/.",
    ),
    IntegerConfigField(
        "server.timeout",
        "DF_SERVER_TIMEOUT",
        help_str="Web workers silent for more than this many seconds are killed and restarted.",
    ),
    IntegerConfigField(
        "server.graceful_timeout",
        "DF_SERVER_GRACEFUL_TIMEOUT",
        help_str="After receiving a restart signal, workers have this much time to finish serving "
        "requests. Workers still alive after the timeout (starting from the receipt of "
        "the restart signal) are force killed.",
    ),
    IntegerConfigField(
        "server.keepalive",
        "DF_SERVER_KEEPALIVE",
        help_str="After receiving a restart signal, workers have this much time to finish serving "
        "requests. Workers still alive after the timeout (starting from the receipt of "
        "the restart signal) are force killed.",
    ),
    IntegerConfigField(
        "server.max_requests",
        "DF_SERVER_MAX_REQUESTS",
        help_str="The maximum number of requests a worker will process before restarting.",
    ),
    IntegerConfigField(
        "server.threads",
        "DF_SERVER_THREADS",
        help_str="The number of web server threads for handling requests.",
    ),
    IntegerConfigField(
        "server.processes",
        "DF_SERVER_PROCESSES",
        help_str="The number of web server processes for handling requests.",
    ),
    CharConfigField(
        "global.time_zone", "TIME_ZONE", help_str="default to Europe/Paris"
    ),
    CharConfigField(
        "global.log_remote_url",
        "LOG_REMOTE_URL",
        help_str="Send logs to a syslog or systemd log daemon. \n"
        "Examples: syslog+tcp://localhost:514/user, syslog:///local7, "
        "syslog:///dev/log/daemon, logd:///project_name",
    ),
    CharConfigField(
        "global.log_directory",
        "LOG_DIRECTORY",
        help_str="Write all local logs to this directory.",
    ),
    CharConfigField(
        "global.log_raven_dsn",
        "RAVEN_DSN",
        help_str='Use the Raven service to capture logs. Require the "raven" package. \n'
        'Should look like "https://xxx...xxx:yyy...yyy@sentry.io/zzzzz"',
    ),
    BooleanConfigField(
        "global.log_remote_access",
        "LOG_REMOTE_ACCESS",
        help_str="If true, log of HTTP connections are also sent to syslog/logd",
    ),
    CharConfigField(
        "database.db",
        "DATABASE_NAME",
        help_str="Main database name (or path of the sqlite3 database)",
    ),
    CharConfigField(
        "database.engine",
        "DATABASE_ENGINE",
        help_str='Main database engine ("mysql", "postgresql", "sqlite3", "oracle", or the dotted name of '
        "the Django backend)",
    ),
    CharConfigField("database.host", "DATABASE_HOST", help_str="Main database host"),
    CharConfigField(
        "database.password", "DATABASE_PASSWORD", help_str="Main database password"
    ),
    IntegerConfigField("database.port", "DATABASE_PORT", help_str="Main database port"),
    CharConfigField("database.user", "DATABASE_USER", help_str="Main database user"),
    CharConfigField("email.host", "EMAIL_HOST", help_str="SMTP server"),
    CharConfigField("email.password", "EMAIL_HOST_PASSWORD", help_str="SMTP password"),
    IntegerConfigField(
        "email.port", "EMAIL_PORT", help_str="SMTP port (often 25, 465 or 587)"
    ),
    CharConfigField("email.user", "EMAIL_HOST_USER", help_str="SMTP user"),
    CharConfigField("email.from", "EMAIL_FROM", help_str="Displayed sender email"),
    BooleanConfigField(
        "email.use_tls",
        "EMAIL_USE_TLS",
        help_str='"true" if your SMTP uses STARTTLS ' "(often on port 587)",
    ),
    BooleanConfigField(
        "email.use_ssl",
        "EMAIL_USE_SSL",
        help_str='"true" if your SMTP uses SSL (often on port 465)',
    ),
]

SENDFILE_MAPPING = [
    BooleanConfigField(
        "global.use_apache",
        "USE_X_SEND_FILE",
        help_str='"true" if Apache is used as reverse-proxy with mod_xsendfile.'
        "The X-SENDFILE header must be allowed from file directories",
    ),
    ConfigField(
        "global.use_nginx",
        "X_ACCEL_REDIRECT",
        from_str=x_accel_converter,
        to_str=lambda x: "True" if x else "False",
        help_str='"true" is nginx is used as reverse-proxy with x-accel-redirect.'
        "The media directory (and url) must be allowed in the Nginx configuration.",
    ),
]

AUTH_MAPPING = [
    BooleanConfigField(
        "auth.local_users",
        "DF_ALLOW_LOCAL_USERS",
        help_str='Set to "false" to deactivate local database of users.',
    ),
    BooleanConfigField(
        "auth.pam",
        "USE_PAM_AUTHENTICATION",
        help_str='Set to "true" if you want to activate PAM authentication',
    ),
    BooleanConfigField(
        "auth.create_users",
        "DF_ALLOW_USER_CREATION",
        help_str='Set to "false" if users cannot create their account themselvers, or '
        "only if existing users can by authenticated by the reverse-proxy.",
    ),
    IntegerConfigField(
        "auth.session_duration",
        "SESSION_COOKIE_AGE",
        help_str="Duration of the connection sessions "
        "(in seconds, default to 1,209,600 s / 14 days)",
    ),
    CharConfigField(
        "auth.remote_user_header",
        "DF_REMOTE_USER_HEADER",
        help_str='Set it if the reverse-proxy authenticates users, a common value is "HTTP_REMOTE_USER". '
        "Note: the HTTP_ prefix is automatically added, just set REMOTE_USER in the "
        "reverse-proxy configuration. ",
    ),
    ListConfigField(
        "auth.remote_user_groups",
        "DF_DEFAULT_GROUPS",
        help_str="Comma-separated list of groups, for new users that are automatically created "
        "when authenticated by remote_user_header. Ignored if groups are read from a LDAP "
        "server. ",
    ),
    CharConfigField(
        "auth.radius_server",
        "RADIUS_SERVER",
        help_str="IP or FQDN of the Radius server. "
        'Python package "django-radius" is required.',
    ),
    IntegerConfigField(
        "auth.radius_port", "RADIUS_PORT", help_str="port of the Radius server."
    ),
    CharConfigField(
        "auth.radius_secret",
        "RADIUS_SECRET",
        help_str="Shared secret if the Radius server",
    ),
    BooleanConfigField(
        "auth.allow_basic_auth",
        "USE_HTTP_BASIC_AUTH",
        help_str='Set to "true" if you want to allow HTTP basic auth, using the Django database.',
    ),
    CharConfigField(
        "auth.ldap_server_url",
        "AUTH_LDAP_SERVER_URI",
        help_str='URL of your LDAP server, like "ldap://ldap.example.com". '
        'Python packages "pyldap" and "django-auth-ldap" must be installed.'
        "Can be used for retrieving attributes of users authenticated by the reverse proxy",
    ),
    CharConfigField(
        "auth.ldap_bind_dn",
        "AUTH_LDAP_BIND_DN",
        help_str="Bind dn for LDAP authentication",
    ),
    CharConfigField(
        "auth.ldap_bind_password",
        "AUTH_LDAP_BIND_PASSWORD",
        help_str="Bind password for LDAP authentication",
    ),
    CharConfigField(
        "auth.ldap_user_search_base",
        "AUTH_LDAP_USER_SEARCH_BASE",
        help_str="Search base for LDAP authentication by direct after an search, "
        'like "ou=users,dc=example,dc=com".',
    ),
    CharConfigField(
        "auth.ldap_filter",
        "AUTH_LDAP_FILTER",
        help_str='Filter for LDAP authentication, like "(uid=%%(user)s)" (the default),'
        ' the double "%%" is required in .ini files.',
    ),
    CharConfigField(
        "auth.ldap_direct_bind",
        "AUTH_LDAP_USER_DN_TEMPLATE",
        help_str="Set it for a direct LDAP bind and to skip the LDAP search, "
        'like "uid=%%(user)s,ou=users,dc=example,dc=com". '
        '%%(user)s is the only allowed variable and the double "%%" is required in .ini files.',
    ),
    BooleanConfigField(
        "auth.ldap_start_tls",
        "AUTH_LDAP_START_TLS",
        help_str='Set to "true" if you want to use StartTLS.',
    ),
    CharConfigField(
        "auth.ldap_first_name_attribute",
        "AUTH_LDAP_USER_FIRST_NAME",
        help_str='LDAP attribute for the user\'s first name, like "givenName".',
    ),
    CharConfigField(
        "auth.ldap_last_name_attribute",
        "AUTH_LDAP_USER_LAST_NAME",
        help_str='LDAP attribute for the user\'s last name, like "sn".',
    ),
    CharConfigField(
        "auth.ldap_email_attribute",
        "AUTH_LDAP_USER_EMAIL",
        help_str='LDAP attribute for the user\'s email, like "email".',
    ),
    CharConfigField(
        "auth.ldap_is_active_group",
        "AUTH_LDAP_USER_IS_ACTIVE",
        help_str='LDAP group DN for active users, like "cn=active,ou=groups,dc=example,dc=com"',
    ),
    CharConfigField(
        "auth.ldap_is_staff_group",
        "AUTH_LDAP_USER_IS_STAFF",
        help_str='LDAP group DN for staff users, like "cn=staff,ou=groups,dc=example,dc=com".',
    ),
    CharConfigField(
        "auth.ldap_is_superuser_group",
        "AUTH_LDAP_USER_IS_SUPERUSER",
        help_str='LDAP group DN for superusers, like "cn=superuser,ou=groups,dc=example,dc=com".',
    ),
    CharConfigField(
        "auth.ldap_require_group",
        "AUTH_LDAP_REQUIRE_GROUP",
        help_str="only authenticates users belonging to this group. Must be something like "
        '"cn=enabled,ou=groups,dc=example,dc=com".',
    ),
    CharConfigField(
        "auth.ldap_deny_group",
        "AUTH_LDAP_DENY_GROUP",
        help_str="authentication is denied for users belonging to this group. Must be something like "
        '"cn=disabled,ou=groups,dc=example,dc=com".',
    ),
    BooleanConfigField(
        "auth.ldap_mirror_groups",
        "AUTH_LDAP_MIRROR_GROUPS",
        help_str="Mirror LDAP groups at each user login",
    ),
    CharConfigField(
        "auth.ldap_group_search_base",
        "AUTH_LDAP_GROUP_SEARCH_BASE",
        help_str='Search base for LDAP groups, like "ou=groups,dc=example,dc=com"',
    ),
    ChoiceConfigFile(
        "auth.ldap_group_type",
        "AUTH_LDAP_GROUP_NAME",
        choices={
            "posix": "django_auth_ldap.config.PosixGroupType",
            "nis": "django_auth_ldap.config.NISGroupType",
            "GroupOfNames": "django_auth_ldap.config.GroupOfNamesType",
            "NestedGroupOfNames": "django_auth_ldap.config.NestedGroupOfNamesType",
            "GroupOfUniqueNames": "django_auth_ldap.config.GroupOfUniqueNamesType",
            "NestedGroupOfUniqueNames": "django_auth_ldap.config.NestedGroupOfUniqueNamesType",
            "ActiveDirectory": "django_auth_ldap.config.ActiveDirectoryGroupType",
            "NestedActiveDirectory": "django_auth_ldap.config.NestedActiveDirectoryGroupType",
            "OrganizationalRole": "django_auth_ldap.config.OrganizationalRoleGroupType",
            "NestedOrganizationalRole": "django_auth_ldap.config.NestedOrganizationalRoleGroupType",
        },
        help_str="Type of LDAP groups.",
    ),
    # CharConfigField('auth.ldap_krb5_ccache', 'KRB5_CCACHE',
    #                 help_str='If your LDAP server needs a Kerberos authentication, '
    #                          'path of the ccache file (optional).'),
    # CharConfigField('auth.ldap_krb5_keytab', 'KRB5_KEYTAB',
    #                 help_str='If your LDAP server needs a Kerberos authentication, path of the client keytab.'),
    # CharConfigField('auth.ldap_krb5_principal', 'KRB5_PRINCIPAL',
    #                 help_str='Principal to use for Kerberos authentication on the LDAP server.'),
]
ALLAUTH_MAPPING = [
    ListConfigField(
        "auth.social_providers",
        "ALLAUTH_PROVIDER_APPS",
        help_str='Comma-separated OAuth2 providers. "django-allauth" package must be installed.'
        "Please use the `social_authentications` command to add an account provider instead "
        "of this setting.",
    )
]

INI_MAPPING = (
    BASE_MAPPING + REDIS_MAPPING + CELERY_MAPPING + AUTH_MAPPING + ALLAUTH_MAPPING
)
