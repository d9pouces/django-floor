"""Default values for all Django settings
======================================

Define settings for deploying most of djangofloor-based websites or for running them in `DEBUG` mode.
Most of them are used by Django, some of them by common third-party packages and the other ones are
used by DjangoFloor.

DjangoFloor also allows references between settings: for example, you only defines `SERVER_BASE_URL`
(like 'https://www.example.com/site/' ) and `SERVER_NAME` ('www.example.com'), `SERVER_PORT` ('443'),
`USE_SSL` ('True'), `SERVER_PROTOCOL` ('https') and `URL_PREFIX` ('/site/') are deduced.

These settings are defined in :mod:`djangofloor.conf.defaults`.
Settings that should be customized on each installation (like the server name or the database password) can be
written in .ini files. The mapping between the Python setting and the [section/option] system is defined in
:mod:`djangofloor.conf.mapping`.

.. literalinclude:: ../../../../../djangofloor/conf/defaults.py
   :language: python
   :lines: 41-1000

"""

import os

from django.utils.translation import ugettext_lazy as _

from djangofloor.conf.auth import (
    authentication_backends,
    ldap_group_class,
    ldap_group_search,
    ldap_boolean_attribute_map,
    ldap_attribute_map,
    ldap_user_search,
)
from djangofloor.conf.callables import (
    url_parse_server_name,
    url_parse_server_protocol,
    url_parse_server_port,
    url_parse_prefix,
    url_parse_ssl,
    project_name,
    allowed_hosts,
    cache_setting,
    template_setting,
    generate_secret_key,
    use_x_forwarded_for,
    required_packages,
    installed_apps,
    databases,
    excluded_django_commands,
    celery_redis_url,
    websocket_redis_dict,
    cache_redis_url,
    session_redis_dict,
    smart_hostname,
    DefaultListenAddress,
    allauth_provider_apps,
    secure_hsts_seconds,
)
from djangofloor.conf.config_values import (
    Path,
    Directory,
    SettingReference,
    ExpandIterable,
    CallableSetting,
    AutocreateFileContent,
    AutocreateFile,
)
from djangofloor.conf.pipeline import static_storage, pipeline_enabled
from djangofloor.log import log_configuration
from djangofloor.utils import is_package_present, guess_version

__author__ = "Matthieu Gallet"

# ######################################################################################################################
#
# detect if some external packages are available, to automatically customize some settings
#
# ######################################################################################################################
try:
    import django_redis  # does not work with is_package_present (???)

    USE_REDIS_CACHE = True
except ImportError:
    django_redis = None
    USE_REDIS_CACHE = False
USE_CELERY = is_package_present("celery")
USE_REDIS_SESSIONS = is_package_present("redis_sessions")
USE_PIPELINE = is_package_present("pipeline")
USE_DEBUG_TOOLBAR = is_package_present("debug_toolbar")
USE_REST_FRAMEWORK = is_package_present("rest_framework")
USE_ALL_AUTH = is_package_present("allauth")

# ######################################################################################################################
#
# settings that could be kept as-is for most projects
# of course, you can override them in your default settings
#
# ######################################################################################################################
ADMINS = (("admin", "{ADMIN_EMAIL}"),)
ALLOWED_HOSTS = CallableSetting(allowed_hosts)
CACHE_URL = CallableSetting(cache_redis_url)
CACHES = CallableSetting(cache_setting)
CSRF_COOKIE_DOMAIN = "{SERVER_NAME}"
CSRF_TRUSTED_ORIGINS = ["{SERVER_NAME}", "{SERVER_NAME}:{SERVER_PORT}"]
DATABASES = CallableSetting(databases)

DEBUG = False
# you should create a "local_settings.py" with "DEBUG = True" at the root of your project
DEVELOPMENT = True
# display all commands (like "migrate" or "runserver") in manage.py
# if False, development-specific commands are hidden

DEFAULT_FROM_EMAIL = "webmaster@{SERVER_NAME}"
FILE_UPLOAD_TEMP_DIR = Directory("{LOCAL_PATH}/tmp-uploads")
INSTALLED_APPS = CallableSetting(installed_apps)
LOGGING = CallableSetting(log_configuration)
MANAGERS = SettingReference("ADMINS")
MEDIA_ROOT = Directory("{LOCAL_PATH}/media")
MEDIA_URL = "/media/"
MIDDLEWARE = [
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "djangofloor.middleware.DjangoFloorMiddleware",
    ExpandIterable("DF_MIDDLEWARE"),
    "django.middleware.cache.FetchFromCacheMiddleware",
]
if USE_DEBUG_TOOLBAR:
    MIDDLEWARE.insert(-3, "debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "djangofloor.root_urls"
SECRET_KEY = AutocreateFileContent(
    "{LOCAL_PATH}/secret_key.txt", generate_secret_key, mode=0o600, length=60
)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = SettingReference("USE_SSL")
SECURE_HSTS_PRELOAD = SettingReference("USE_SSL")
SECURE_HSTS_SECONDS = CallableSetting(secure_hsts_seconds)
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)  # X-Forwarded-Proto or None
SECURE_SSL_REDIRECT = SettingReference("USE_SSL")
SECURE_FRAME_DENY = SettingReference("USE_SSL")
SERVER_EMAIL = "{ADMIN_EMAIL}"
SESSION_COOKIE_AGE = 1209600
TEMPLATES = CallableSetting(template_setting)
TEMPLATE_DEBUG = SettingReference("DEBUG")
TEMPLATE_DIRS = ()
TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.debug",
    "django.template.context_processors.i18n",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.template.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "djangofloor.context_processors.context_base",
    ExpandIterable("DF_TEMPLATE_CONTEXT_PROCESSORS"),
]
TEST_RUNNER = "django.test.runner.DiscoverRunner"
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
USE_TZ = True
USE_X_FORWARDED_HOST = True  # X-Forwarded-Host
X_FRAME_OPTIONS = "SAMEORIGIN"
WSGI_APPLICATION = "djangofloor.wsgi.django_runserver.django_application"

# django.contrib.auth
AUTHENTICATION_BACKENDS = CallableSetting(authentication_backends)
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "{URL_PREFIX}"
# LOGOUT_REDIRECT_URL = '{URL_PREFIX}'

# django.contrib.sessions
if USE_REDIS_SESSIONS:
    SESSION_ENGINE = "redis_sessions.session"
SESSION_COOKIE_SECURE = SettingReference("USE_SSL")
CSRF_COOKIE_SECURE = SettingReference("USE_SSL")

# django.contrib.sites
SITE_ID = 1

# django.contrib.staticfiles
STATIC_ROOT = Directory("{LOCAL_PATH}/static")
STATIC_URL = "/static/"
STATICFILES_STORAGE = CallableSetting(static_storage)
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
if USE_PIPELINE:
    STATICFILES_FINDERS.append("pipeline.finders.PipelineFinder")

# celery
BROKER_URL = CallableSetting(celery_redis_url)
CELERY_DEFAULT_QUEUE = "celery"
CELERY_TIMEZONE = "{TIME_ZONE}"
CELERY_RESULT_EXCHANGE = "{DF_MODULE_NAME}_results"
CELERY_RESULT_BACKEND = "{BROKER_URL}"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json", "yaml", "msgpack"]
CELERY_APP = "djangofloor"
CELERY_CREATE_DIRS = True
CELERY_TASK_SERIALIZER = "json"

# django-npm
NPM_EXECUTABLE_PATH = "npm"
NPM_ROOT_PATH = Directory("{LOCAL_PATH}/npm")
NPM_STATIC_FILES_PREFIX = "vendor"

# djangofloor
DATA_PATH = Directory("{LOCAL_PATH}/data")
SERVER_NAME = CallableSetting(url_parse_server_name)  # ~ www.example.org
SERVER_PORT = CallableSetting(url_parse_server_port)  # ~ 443
SERVER_PROTOCOL = CallableSetting(url_parse_server_protocol)  # ~ "https"
URL_PREFIX = CallableSetting(
    url_parse_prefix
)  # something like "/prefix/" (most probably just "/")
USE_HTTP_BASIC_AUTH = False  # HTTP-Authorization
USE_SSL = CallableSetting(url_parse_ssl)  # ~ True
USE_X_FORWARDED_FOR = CallableSetting(use_x_forwarded_for)  # X-Forwarded-For
USE_X_SEND_FILE = False  # Apache module
X_ACCEL_REDIRECT = []  # paths used by nginx
DF_FAKE_AUTHENTICATION_USERNAME = None
DF_PROJECT_VERSION = CallableSetting(guess_version)
DF_REMOVED_DJANGO_COMMANDS = CallableSetting(excluded_django_commands)
DF_CHECKED_REQUIREMENTS = CallableSetting(required_packages)
DF_PUBLIC_SIGNAL_LIST = True
# do not check for each WS signal/function before sending its name to the client
DF_SYSTEM_CHECKS = [
    "djangofloor.views.monitoring.RequestCheck",
    "djangofloor.views.monitoring.AuthenticationCheck",
    "djangofloor.views.monitoring.System",
    "djangofloor.views.monitoring.CeleryStats",
    "djangofloor.views.monitoring.Packages",
    "djangofloor.views.monitoring.LogAndExceptionCheck",
    "djangofloor.views.monitoring.LogLastLines",
]
WINDOW_INFO_MIDDLEWARES = [
    "djangofloor.middleware.WindowKeyMiddleware",
    "djangofloor.middleware.DjangoAuthMiddleware",
    "djangofloor.middleware.Djangoi18nMiddleware",
    "djangofloor.middleware.BrowserMiddleware",
]
DF_SERVER_TIMEOUT = 35
DF_SERVER_GRACEFUL_TIMEOUT = 25
DF_SERVER_THREADS = 2
DF_SERVER_PROCESSES = 2
DF_SERVER_KEEPALIVE = 5
DF_SERVER_MAX_REQUESTS = 10000
DF_SERVER_SSL_KEY = None
DF_SERVER_SSL_CERTIFICATE = None
DF_ALLOW_USER_CREATION = True
DF_ALLOW_LOCAL_USERS = True

WEBSOCKET_URL = "/ws/"  # set to None if you do not use websockets
WEBSOCKET_REDIS_CONNECTION = CallableSetting(websocket_redis_dict)
WEBSOCKET_TOPIC_SERIALIZER = "djangofloor.wsgi.topics.serialize_topic"
WEBSOCKET_HEARTBEAT = "--HEARTBEAT--"
WEBSOCKET_SIGNAL_DECODER = "json.JSONDecoder"
WEBSOCKET_SIGNAL_ENCODER = "django.core.serializers.json.DjangoJSONEncoder"
WEBSOCKET_REDIS_PREFIX = "ws"
WEBSOCKET_REDIS_EXPIRE = 36000
WEBSOCKET_CONNECTION_EXPIRE = 3600  # by default, close a connection after one hour
# (but the client transparently reopen it
WEBSOCKET_HEADER = (
    "WINDOW_KEY"
)  # header used in AJAX requests (thus they have the same window identifier)

# django-pipeline
PIPELINE = {
    "PIPELINE_ENABLED": SettingReference("PIPELINE_ENABLED"),
    "JAVASCRIPT": SettingReference("PIPELINE_JS"),
    "STYLESHEETS": SettingReference("PIPELINE_CSS"),
    "CSS_COMPRESSOR": SettingReference("PIPELINE_CSS_COMPRESSOR"),
    "JS_COMPRESSOR": SettingReference("PIPELINE_JS_COMPRESSOR"),
    "COMPILERS": SettingReference("PIPELINE_COMPILERS"),
}
PIPELINE_COMPILERS = []
PIPELINE_CSS_COMPRESSOR = "pipeline.compressors.NoopCompressor"
PIPELINE_JS_COMPRESSOR = "pipeline.compressors.NoopCompressor"
PIPELINE_CSS = {
    "default": {
        "source_filenames": SettingReference("DF_CSS"),
        "output_filename": "css/default-all.css",
        "extra_context": {"media": "all"},
    },
    "django": {
        "source_filenames": [
            "vendor/font-awesome/css/font-awesome.min.css",
            "admin/css/forms.css",
            "css/djangofloor-django.css",
        ],
        "output_filename": "css/django-all.css",
        "extra_context": {"media": "all"},
    },
    "bootstrap3": {
        "source_filenames": [
            "vendor/bootstrap3/dist/css/bootstrap.min.css",
            "vendor/bootstrap3/dist/css/bootstrap-theme.min.css",
            "vendor/font-awesome/css/font-awesome.min.css",
            "css/djangofloor-bootstrap3.css",
            ExpandIterable("DF_CSS"),
        ],
        "output_filename": "css/bootstrap3-all.css",
        "extra_context": {"media": "all"},
    },
    "ie9": {
        "source_filenames": [],
        "output_filename": "css/ie9.css",
        "extra_context": {"media": "all"},
    },
}
PIPELINE_ENABLED = CallableSetting(pipeline_enabled)
PIPELINE_JS = {
    "default": {
        "source_filenames": [
            "vendor/jquery/dist/jquery.min.js",
            "js/djangofloor-base.js",
            ExpandIterable("DF_JS"),
        ],
        "output_filename": "js/default.js",
    },
    "django": {
        "source_filenames": [
            "vendor/jquery/dist/jquery.min.js",
            "js/djangofloor-base.js",
            "vendor/bootstrap-notify/bootstrap-notify.js",
            "js/djangofloor-django.js",
            ExpandIterable("DF_JS"),
        ],
        "output_filename": "js/django.js",
    },
    "bootstrap3": {
        "source_filenames": [
            "vendor/jquery/dist/jquery.js",
            "vendor/bootstrap3/dist/js/bootstrap.js",
            "js/djangofloor-base.js",
            "vendor/bootstrap-notify/bootstrap-notify.js",
            "js/djangofloor-bootstrap3.js",
            ExpandIterable("DF_JS"),
        ],
        "output_filename": "js/bootstrap3.js",
    },
    "ie9": {
        "source_filenames": [
            "vendor/html5shiv/dist/html5shiv.js",
            "vendor/respond.js/dest/respond.src.js",
        ],
        "output_filename": "js/ie9.js",
    },
}
PIPELINE_MIMETYPES = (
    (b"text/coffeescript", ".coffee"),
    (b"text/less", ".less"),
    (b"text/javascript", ".js"),
    (b"text/x-sass", ".sass"),
    (b"text/x-scss", ".scss"),
)
LIVE_SCRIPT_BINARY = "lsc"
LESS_BINARY = "lessc"
SASS_BINARY = "sass"
STYLUS_BINARY = "stylus"
BABEL_BINARY = "babel"
YUGLIFY_BINARY = "yuglify"
YUI_BINARY = "yuicompressor"
CLOSURE_BINARY = "closure"
UGLIFYJS_BINARY = "uglifyjs"
CSSTIDY_BINARY = "csstidy"
CSSMIN_BINARY = "cssmin"
TYPESCRIPT_BINARY = "tsc"
TYPESCRIPT_ARGUMENTS = []
# Django-All-Auth
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[{SERVER_NAME}] "
ACCOUNT_EMAIL_VERIFICATION = None
ALLAUTH_PROVIDER_APPS = CallableSetting(allauth_provider_apps)
ALLAUTH_APPLICATIONS_CONFIG = AutocreateFile("{LOCAL_PATH}/social_auth.ini", mode=0o600)
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "{SERVER_PROTOCOL}"
ACCOUNT_ADAPTER = "djangofloor.views.allauth.AccountAdapter"

# Django-Debug-Toolbar
DEBUG_TOOLBAR_CONFIG = {"JQUERY_URL": "{STATIC_URL}vendor/jquery/dist/jquery.min.js"}
DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
]
INTERNAL_IPS = ("127.0.0.1", "::1", "localhost")

# Django-Bootstrap3
BOOTSTRAP3 = {
    "jquery_url": "{STATIC_URL}vendor/jquery/dist/jquery.min.js",
    "base_url": "{STATIC_URL}vendor/bootstrap3/dist/",
    "theme_url": None,
    "include_jquery": False,
    "horizontal_label_class": "col-md-3",
    "horizontal_field_class": "col-md-9",
    "set_disabled": True,
    "set_placeholder": False,
    "formset_renderers": {"default": "bootstrap3.renderers.FormsetRenderer"},
    "form_renderers": {"default": "bootstrap3.renderers.FormRenderer"},
    "field_renderers": {
        "default": "bootstrap3.renderers.FieldRenderer",
        "inline": "bootstrap3.renderers.InlineFieldRenderer",
    },
}

# django-auth-ldap
AUTH_LDAP_SERVER_URI = None
AUTH_LDAP_BIND_DN = ""
AUTH_LDAP_BIND_PASSWORD = ""
AUTH_LDAP_USER_SEARCH_BASE = "ou=users,dc=example,dc=com"
AUTH_LDAP_FILTER = "(uid=%(user)s)"
AUTH_LDAP_USER_SEARCH = CallableSetting(ldap_user_search)
AUTH_LDAP_USER_DN_TEMPLATE = None
AUTH_LDAP_START_TLS = False
AUTH_LDAP_USER_ATTR_MAP = CallableSetting(ldap_attribute_map)
AUTH_LDAP_USER_FLAGS_BY_GROUP = CallableSetting(ldap_boolean_attribute_map)
AUTH_LDAP_MIRROR_GROUPS = False
AUTH_LDAP_USER_IS_ACTIVE = None
AUTH_LDAP_USER_IS_STAFF = None
AUTH_LDAP_USER_IS_SUPERUSER = None
AUTH_LDAP_USER_FIRST_NAME = None
AUTH_LDAP_USER_LAST_NAME = None
AUTH_LDAP_USER_EMAIL = None
AUTH_LDAP_GROUP_TYPE = CallableSetting(ldap_group_class)
AUTH_LDAP_GROUP_NAME = "posix"
AUTH_LDAP_ALWAYS_UPDATE_USER = True
AUTH_LDAP_REQUIRE_GROUP = None
AUTH_LDAP_DENY_GROUP = None
# Cache group memberships for an hour to minimize LDAP traffic
AUTH_LDAP_CACHE_GROUPS = True
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600
# Use LDAP group membership to calculate group permissions.
AUTH_LDAP_FIND_GROUP_PERMS = False
AUTH_LDAP_GROUP_SEARCH = CallableSetting(ldap_group_search)
AUTH_LDAP_GROUP_SEARCH_BASE = "ou=groups,dc=example,dc=com"
AUTH_LDAP_AUTHORIZE_ALL_USERS = True
# https://bitbucket.org/illocution/django-auth-ldap/pull-requests/29/kerberos-bind-method-to-provide-multi/diff
# KRB5_CCACHE = None
# KRB5_KEYTAB = None
# KRB5_PRINCIPAL = None
# django-cors-headers
CORS_ORIGIN_WHITELIST = ("{SERVER_NAME}", "{SERVER_NAME}:{SERVER_PORT}")
CORS_REPLACE_HTTPS_REFERER = False

# django-hosts
DEFAULT_HOST = "{SERVER_NAME}"
HOST_SCHEME = "{SERVER_PROTOCOL}://"
HOST_PORT = "{SERVER_PORT}"

# django—pam
USE_PAM_AUTHENTICATION = False

# django-radius
RADIUS_SERVER = None
RADIUS_PORT = None
RADIUS_SECRET = None

# django-redis-sessions
SESSION_REDIS = CallableSetting(session_redis_dict)

# raven
RAVEN_CONFIG = {"dsn": "{RAVEN_DSN}", "release": "{DF_PROJECT_VERSION}"}

# ######################################################################################################################
#
# settings that should be customized for each project
# of course, you can redefine or override any setting
#
# ######################################################################################################################
# djangofloor
DF_CSS = []
DF_JS = []
DF_INDEX_VIEW = "djangofloor.views.IndexView"
DF_SITE_SEARCH_VIEW = None  # 'djangofloor.views.search.UserSearchView'
DF_PROJECT_NAME = CallableSetting(project_name)
DF_URL_CONF = "{DF_MODULE_NAME}.urls.urlpatterns"
DF_ADMIN_SITE = "django.contrib.admin.site"
DF_JS_CATALOG_VIEWS = ["djangofloor", "django.contrib.admin"]
# noinspection PyUnresolvedReferences
DF_INSTALLED_APPS = ["{DF_MODULE_NAME}"]  # your django app!
DF_PIP_NAME = (
    "{DF_MODULE_NAME}"
)  # anything such that "pip install {DF_PIP_NAME}" installs your project
# only used in docs
DF_MIDDLEWARE = []
DF_REMOTE_USER_HEADER = None  # HTTP_REMOTE_USER
DF_DEFAULT_GROUPS = [_("Users")]
DF_TEMPLATE_CONTEXT_PROCESSORS = []
NPM_FILE_PATTERNS = {
    "bootstrap-notify": ["*.js"],
    "bootstrap3": ["dist/*"],
    "font-awesome": ["css/*", "fonts/*"],
    "html5shiv": ["dist/*"],
    "jquery": ["dist/*"],
    "jquery-file-upload": ["css/*", "js/*"],
    # 'metro-ui': ['build/*'],
    "respond.js": ["dest/*"],
}
# used by the "npm" command: downloads these packages and copies the files matching any pattern in the list
LOG_REMOTE_ACCESS = True
LOG_DIRECTORY = Directory("{LOCAL_PATH}/log")
LOG_EXCLUDED_COMMANDS = {
    "clearsessions",
    "check",
    "compilemessages",
    "collectstatic",
    "config",
    "createcachetable",
    "changepassword",
    "createsuperuser",
    "dumpdb",
    "dbshell",
    "dumpdata",
    "flush",
    "loaddata",
    "gen_dev_files",
    "inspectdb",
    "makemessages",
    "makemigrations",
    "migrate",
    "npm",
    "packaging",
    "ping_google",
    "remove_stale_contenttypes",
    "sendtestemail",
    "shell",
    "showmigrations",
    "sqlflush",
    "sqlmigrate",
    "sqlsequencereset",
    "squashmigrations",
    "startapp",
    "test",
    "testserver",
}

# ######################################################################################################################
#
# settings that should be customized for each deployment
# {DF_MODULE_NAME}.iniconf:INI_MAPPING should be a list of ConfigField, allowing to define these settings in a .ini file
#
# ######################################################################################################################
ADMIN_EMAIL = "admin@{SERVER_NAME}"  # aliased in settings.ini as "[global]admin_email"
DATABASE_ENGINE = "sqlite3"  # aliased in settings.ini as "[database]engine"
DATABASE_NAME = Path(
    "{LOCAL_PATH}/database.sqlite3"
)  # aliased in settings.ini as "[database]name"
DATABASE_USER = ""  # aliased in settings.ini as "[database]user"
DATABASE_PASSWORD = ""  # aliased in settings.ini as "[database]password"
DATABASE_HOST = ""  # aliased in settings.ini as "[database]host"
DATABASE_PORT = ""  # aliased in settings.ini as "[database]port"
DATABASE_OPTIONS = {}
EMAIL_HOST = "localhost"  # aliased in settings.ini as "[email]host"
EMAIL_HOST_PASSWORD = ""  # aliased in settings.ini as "[email]password"
EMAIL_HOST_USER = ""  # aliased in settings.ini as "[email]user"
EMAIL_FROM = "{ADMIN_EMAIL}"  # aliased in settings.ini as "[email]from"
EMAIL_PORT = 25  # aliased in settings.ini as "[email]port"
EMAIL_SUBJECT_PREFIX = "[{SERVER_NAME}] "
EMAIL_USE_TLS = False  # aliased in settings.ini as "[email]use_tls"
EMAIL_USE_SSL = False  # aliased in settings.ini as "[email]use_ssl"
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
LANGUAGE_CODE = "fr-fr"  # aliased in settings.ini as "[global]language_code"
TIME_ZONE = "Europe/Paris"  # aliased in settings.ini as "[global]time_zone"
LOG_REMOTE_URL = None  # aliased in settings.ini as "[global]log_remote_url"
SERVER_BASE_URL = CallableSetting(
    smart_hostname
)  # aliased in settings.ini as "[global]server_url"

# djangofloor
LISTEN_ADDRESS = DefaultListenAddress(
    9000
)  # aliased in settings.ini as "[global]listen_address"
LOCAL_PATH = "./django_data"  # aliased in settings.ini as "[global]data"
__split_path = __file__.split(os.path.sep)
if "lib" in __split_path:
    prefix = os.path.join(*__split_path[: __split_path.index("lib")])
    LOCAL_PATH = Directory("/%s/var/{DF_MODULE_NAME}" % prefix)
# these Django commands do not write log (only on stdout)
# PID_DIRECTORY = Directory('{LOCAL_PATH}/run')
# PID_FILENAME = CallableSetting(pid_filename)

# django-redis-sessions
SESSION_REDIS_PROTOCOL = "redis"
SESSION_REDIS_HOST = "localhost"  # aliased in settings.ini as "[session]host"
SESSION_REDIS_PORT = 6379  # aliased in settings.ini as "[session]port"
SESSION_REDIS_DB = 1  # aliased in settings.ini as "[session]db"
SESSION_REDIS_PASSWORD = ""  # aliased in settings.ini as "[session]password"

# django_redis (cache)
CACHE_PROTOCOL = "redis"
CACHE_HOST = "localhost"  # aliased in settings.ini as "[cache]host"
CACHE_PORT = 6379  # aliased in settings.ini as "[cache]port"
CACHE_DB = 2  # aliased in settings.ini as "[cache]db"
CACHE_PASSWORD = ""  # aliased in settings.ini as "[cache]password"

# websockets
WEBSOCKET_REDIS_PROTOCOL = "redis"
WEBSOCKET_REDIS_HOST = "localhost"  # aliased in settings.ini as "[websocket]host"
WEBSOCKET_REDIS_PORT = 6379  # aliased in settings.ini as "[websocket]port"
WEBSOCKET_REDIS_DB = 3  # aliased in settings.ini as "[websocket]db"
WEBSOCKET_REDIS_PASSWORD = ""  # aliased in settings.ini as "[websocket]password"

# celery
CELERY_PROTOCOL = "redis"
CELERY_HOST = "localhost"  # aliased in settings.ini as "[celery]host"
CELERY_PORT = 6379  # aliased in settings.ini as "[celery]port"
CELERY_DB = 4  # aliased in settings.ini as "[celery]db"
CELERY_PASSWORD = ""  # aliased in settings.ini as "[celery]password"
CELERY_PROCESSES = 4

# raven
RAVEN_DSN = None
