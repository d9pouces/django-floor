# coding=utf-8
"""Default values for your Django project
======================================

Define all DjangoFloor default settings. The goal is to define valid settings out-of-the-box.

"""
from __future__ import unicode_literals
import os

from django.utils.translation import ugettext_lazy as _

from djangofloor.utils import DirectoryPath, FilePath, SettingReference, ExpandIterable, CallableSetting, guess_version


__author__ = 'Matthieu Gallet'

try:
    import ws4redis

    FLOOR_USE_WS4REDIS = True
except ImportError:
    ws4redis = None
    FLOOR_USE_WS4REDIS = False
try:
    # noinspection PyPackageRequirements
    import scss
    USE_SCSS = True
except ImportError:
    scss = None
    USE_SCSS = False
# define a root path for misc. Django data (SQLite database, static files, ...)
LOCAL_PATH = './django_data'
split_path = __file__.split(os.path.sep)
if 'lib' in split_path:
    prefix = os.path.join(*split_path[:split_path.index('lib')])
    LOCAL_PATH = DirectoryPath('/%s/var/{PROJECT_NAME}' % prefix)
LOCAL_PATH_HELP = 'Base path for all data'
SERVER_NAME = 'localhost'
SERVER_NAME_HELP = 'the name of your webserver (should be a DNS name, but can be an IP address)'
PROTOCOL = 'http'
PROTOCOL_HELP = 'Protocol (or scheme) used by your webserver (apache/nginx/…, can be http or https)'
LOG_PATH = DirectoryPath('{LOCAL_PATH}/log')
DATA_PATH = DirectoryPath('{LOCAL_PATH}/data')
DEBUG = False
DEBUG_HELP = 'A boolean that turns on/off debug mode.'
ADMIN_EMAIL = 'admin@{SERVER_NAME}'
ADMIN_EMAIL_HELP = 'error logs are sent to this e-mail address'
ADMINS = (("admin", "{ADMIN_EMAIL}"),)
ADMINS_HELP = 'A tuple that lists people who get code error notifications.'
MANAGERS = ADMINS
MANAGERS_HELP = ('A tuple in the same format as ADMINS that specifies who should get broken link notifications '
                 'when BrokenLinkEmailsMiddleware is enabled.')
DEFAULT_FROM_EMAIL = '{ADMIN_EMAIL}'
DEFAULT_FROM_EMAIL_HELP = 'Default email address to use for various automated correspondence from the site manager(s).'
# noinspection PyUnresolvedReferences

DATABASE_ENGINE = 'django.db.backends.sqlite3'
DATABASE_ENGINE_HELP = "SQL database engine, can be 'django.db.backends.[postgresql_psycopg2|mysql|sqlite3|oracle]'."
DATABASE_NAME = FilePath('{DATA_PATH}/database.sqlite3')
DATABASE_NAME_HELP = 'Name of your database, or path to database file if using sqlite3.'
DATABASE_USER = ''
DATABASE_USER_HELP = 'Database user (not used with sqlite3)'
DATABASE_PASSWORD = ''
DATABASE_PASSWORD_HELP = 'Database password (not used with sqlite3)'
DATABASE_HOST = ''
DATABASE_HOST_HELP = 'Empty for localhost through domain sockets or "127.0.0.1" for localhost + TCP'
DATABASE_PORT = ''
DATABASE_PORT_HELP = 'Database port, leave it empty for default (not used with sqlite3)'
DATABASES = {
    'default': {
        'ENGINE': '{DATABASE_ENGINE}',
        'NAME': '{DATABASE_NAME}',
        # The following settings are not used with sqlite3:
        'USER': '{DATABASE_USER}',
        'PASSWORD': '{DATABASE_PASSWORD}',
        'HOST': '{DATABASE_HOST}',
        'PORT': '{DATABASE_PORT}',
    },
}
DATABASES_HELP = 'A dictionary containing the settings for all databases to be used with Django.'
CONN_MAX_AGE = 600
FLOOR_BACKUP_SINGLE_TRANSACTION = False
TIME_ZONE = 'Europe/Paris'
TIME_ZONE_HELP = 'A string representing the time zone for this installation, or None. '
BIND_ADDRESS = '127.0.0.1:9000'
BIND_ADDRESS_HELP = 'The socket (IP address:port) to bind to.'
REDIS_HOST = 'localhost'
REDIS_HOST_HELP = 'hostname of your Redis database for Redis-based services (cache, Celery, websockets, sessions)'
REDIS_PORT = '6379'
REDIS_PORT_HELP = 'port of your Redis database'
THREADS = 1
THREADS_HELP = 'The number of worker threads for handling requests.'
WORKERS = 1
WORKERS_HELP = 'The number of worker process for handling requests.'

USE_X_SEND_FILE = False
USE_X_SEND_FILE_HELP = 'Apache and LightHTTPd only. Use the XSendFile header for sending large files.'
X_ACCEL_REDIRECT = []
X_ACCEL_REDIRECT_HELP = 'Use the X-Accel-Redirect header in NGinx. List of tuples (/directory_path/, /alias_url/).'
INTERNAL_IPS = ('127.0.0.1',)
ALLOWED_HOSTS = ['{SERVER_NAME}', '127.0.0.1', ]
ALLOWED_HOSTS_HELP = 'A list of strings representing the host/domain names that this Django site can serve.'
MAX_REQUESTS = 10000
MAX_REQUESTS_HELP = 'The maximum number of requests a worker will process before restarting.'

REVERSE_PROXY_IPS = ['127.0.0.1', ]
REVERSE_PROXY_IPS_HELP = 'List of IP addresses of the reverse proxies'
REVERSE_PROXY_TIMEOUT = 300
REVERSE_PROXY_TIMEOUT_HELP = 'Timeout for reverse proxy'
# Workers silent for more than this many seconds are killed and restarted.
REVERSE_PROXY_SSL_KEY_FILE = None
REVERSE_PROXY_SSL_KEY_FILE_HELP = 'Key file of reverse proxy (apache/nginx). ' \
                                  'Can be set to None if the key is with the certificate.'
REVERSE_PROXY_SSL_CRT_FILE = None
REVERSE_PROXY_SSL_CRT_FILE_hep = 'SSL certificate file of reverse proxy (apache/nginx). Required if you use SSL'
REVERSE_PROXY_PORT = None  #
REVERSE_PROXY_PORT_HELP = 'Reverse proxy (apache/nginx) port (if None, defaults to 80 or 443 if you use SSL)'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-fr'
LANGUAGE_CODE_HELP = 'A string representing the language code for this installation.'
# Make this unique, and don't share it with anybody.
SECRET_KEY = 'NEZ6ngWX0JihNG2wepl1uxY7bkPOWrTEo27vxPGlUM3eBAYfPT'
SECRET_KEY_HELP = ('A secret key for a particular Django installation. This is used to provide cryptographic signing, '
                   'and should be set to a unique, unpredictable value.')

ACCOUNT_EMAIL_VERIFICATION = None
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[{SERVER_NAME}] '
# iterable of URL of your application. 'my_app.root_urls.urls'
FLOOR_URL_CONF = None
FLOOR_INSTALLED_APPS = []
FLOOR_EXTRA_APPS = []
FLOOR_EXTRA_APPS_HELP = 'List of extra Django apps, allowing you to further customize the behaviour.'
FLOOR_INDEX = None
FLOOR_PROJECT_NAME = 'DjangoFloor'

FLOOR_DEFAULT_GROUP_NAME = _('Users')
FLOOR_DEFAULT_GROUP_NAME_HELP = 'Name of the default group for newly-created users.'

EMAIL_SUBJECT_PREFIX = '[{FLOOR_PROJECT_NAME} / {SERVER_NAME}] '
SERVER_EMAIL = 'root@{SERVER_NAME}'
FILE_CHARSET = 'utf-8'
# The character encoding used to decode any files read from disk. This includes template files and
# initial SQL data files
FILE_UPLOAD_TEMP_DIR = None
# The directory to store data temporarily while uploading files. If None, Django will use
# the standard temporary directory for the operating system. For example, this will
# default to ‘/tmp’ on *nix-style operating systems.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True
DEFAULT_CHARSET = 'utf-8'
DEFAULT_CONTENT_TYPE = 'text/html'
# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
# noinspection PyUnresolvedReferences
MEDIA_ROOT = DirectoryPath('{DATA_PATH}/media')
MEDIA_ROOT_HELP = 'Absolute filesystem path to the directory that will hold user-uploaded files.'
# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
# noinspection PyUnresolvedReferences
STATIC_ROOT = DirectoryPath('{LOCAL_PATH}/static')
STATIC_ROOT_HELP = 'The absolute path to the directory where collectstatic will collect static files for deployment.'
# Additional locations of static files
STATICFILES_DIRS = []

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = ['django.contrib.staticfiles.finders.AppDirectoriesFinder',
                       'django.contrib.staticfiles.finders.FileSystemFinder',
                       'pipeline.finders.PipelineFinder', ]

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'
# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'
LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
LOGIN_REDIRECT_URL = '/'
WEBSOCKET_URL = '/ws/'

FLOOR_EXTRA_CSS = []
PIPELINE_CSS = {
    'default': {
        'source_filenames': ['bootstrap3/css/bootstrap.min.css', 'css/font-awesome.min.css',
                             'css/bootstrap-select.min.css', 'css/djangofloor.css',
                             ExpandIterable('FLOOR_EXTRA_CSS'), ],
        'output_filename': 'css/default.css',
        'extra_context': {
            'media': 'all',
        },
    },
}
FLOOR_EXTRA_JS = []
PIPELINE_JS = {
    'default': {
        'source_filenames': ['js/jquery.min.js', 'bootstrap3/js/bootstrap.min.js',
                             'js/bootstrap-notify.min.js', 'js/djangofloor.js', 'js/bootstrap-select.min.js',
                             'js/ws4redis.js', ExpandIterable('FLOOR_EXTRA_JS'), ],
        'output_filename': 'js/default.js',
    },
    'ie9': {
        'source_filenames': ['js/html5shiv.js', 'js/respond.min.js', ],
        'output_filename': 'js/ie9.js',
    }
}
PIPELINE_ENABLED = False
PIPELINE = {
    'PIPELINE_ENABLED': SettingReference('PIPELINE_ENABLED'),
    'JAVASCRIPT': SettingReference('PIPELINE_JS'),
    'STYLESHEETS': SettingReference('PIPELINE_CSS'),
    'CSS_COMPRESSOR': SettingReference('PIPELINE_CSS_COMPRESSOR'),
    'JS_COMPRESSOR': SettingReference('PIPELINE_JS_COMPRESSOR'),
    'MIMETYPES': SettingReference('PIPELINE_MIMETYPES'),
}

PIPELINE_MIMETYPES = (
    (b'text/coffeescript', '.coffee'),
    (b'text/less', '.less'),
    (b'text/javascript', '.js'),
    (b'text/x-sass', '.sass'),
    (b'text/x-scss', '.scss')
)
# these two cmpressors are not the best ones, but are installed with DjangoFloor as dependencies
PIPELINE_JS_COMPRESSOR = None  # 'pipeline.compressors.slimit.SlimItCompressor'
PIPELINE_CSS_COMPRESSOR = 'djangofloor.middleware.RCSSMinCompressor'
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
if USE_SCSS:
    PIPELINE_COMPILERS = (
        'djangofloor.middleware.PyScssCompiler',
    )

MIDDLEWARE_CLASSES = ['django.middleware.cache.UpdateCacheMiddleware',
                      'django.middleware.common.CommonMiddleware',
                      'debug_toolbar.middleware.DebugToolbarMiddleware',
                      'django.contrib.sessions.middleware.SessionMiddleware',
                      'django.middleware.csrf.CsrfViewMiddleware',
                      'django.middleware.security.SecurityMiddleware',
                      'django.contrib.auth.middleware.AuthenticationMiddleware',
                      'django.contrib.messages.middleware.MessageMiddleware',
                      'django.middleware.clickjacking.XFrameOptionsMiddleware',
                      'djangofloor.middleware.IEMiddleware',
                      'djangofloor.middleware.RemoteUserMiddleware',
                      'djangofloor.middleware.BasicAuthMiddleware',
                      'djangofloor.middleware.FakeAuthenticationMiddleware',
                      'django.middleware.cache.FetchFromCacheMiddleware', ]

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]
DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_CONFIG = {'JQUERY_URL': None, }
TEMPLATE_DEBUG = False
TEMPLATE_DEBUG_HELP = 'A boolean that turns on/off template debug mode.'
# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
]
FLOOR_TEMPLATE_CONTEXT_PROCESSORS = []
TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'djangofloor.context_processors.context_base',
    ExpandIterable('FLOOR_TEMPLATE_CONTEXT_PROCESSORS'),
]
if FLOOR_USE_WS4REDIS:
    # noinspection PyUnresolvedReferences
    TEMPLATE_CONTEXT_PROCESSORS += ['ws4redis.context_processors.default', ]

TEMPLATE_DIRS = []
TEMPLATES = [
    {
        'NAME': 'default',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'OPTIONS': {
            'context_processors': SettingReference('TEMPLATE_CONTEXT_PROCESSORS'),
            'loaders': SettingReference('TEMPLATE_LOADERS'),
        },
    },
]
ROOT_URLCONF = 'djangofloor.root_urls'
# noinspection PyUnresolvedReferences
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.admin',
    'djangofloor',
    'bootstrap3',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'pipeline',
    'debug_toolbar',
    ExpandIterable('FLOOR_EXTRA_APPS'),
    ExpandIterable('OTHER_ALLAUTH'),
    ExpandIterable('FLOOR_INSTALLED_APPS'),
]

if FLOOR_USE_WS4REDIS:
    # noinspection PyUnresolvedReferences
    INSTALLED_APPS += ['ws4redis', ]


OTHER_ALLAUTH = []
OTHER_ALLAUTH_HELP = 'Other allauth authentication providers, merely a list of allauth.socialaccount.providers.*'

BOOTSTRAP3 = {
    'jquery_url': '{STATIC_URL}js/jquery.min.js',
    'base_url': '{STATIC_URL}bootstrap3/',
    'css_url': None,
    'theme_url': None,
    'javascript_url': None,
    'horizontal_label_class': 'col-md-4',
    'horizontal_field_class': 'col-md-8',
}
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
FLOOR_AUTHENTICATION_HEADER = 'HTTP_REMOTE_USER'
FLOOR_AUTHENTICATION_HEADER_HELP = 'HTTP header corresponding to the username when using HTTP authentication.' \
                                   'Should be "HTTP_REMOTE_USER". Leave it empty to disable HTTP authentication.'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_PROXY_SSL_HEADER_HELP = 'A tuple representing a HTTP header/value combination that signifies a request is ' \
                               'secure. This controls the behavior of the request object’s is_secure() method.'
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_HOST_HELP = 'A boolean that specifies whether to use the X-Forwarded-Host header in preference to ' \
                            'the Host header. '
AUTHENTICATION_BACKENDS = [
    'djangofloor.backends.DefaultGroupRemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
FLOOR_FAKE_AUTHENTICATION_USERNAME = None
# used to fake a reverse proxy authentication for development purpose
FLOOR_FAKE_AUTHENTICATION_GROUPS = ['group1', 'group2']
# used to fake LDAP groups, added to the remotely-authenticated user

########################################################################################################################
# sessions
########################################################################################################################
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

########################################################################################################################
# caching
# CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', }}
CACHE_BACKEND = 'django.core.cache.backends.dummy.DummyCache'
CACHES = {
    'default': {'BACKEND': '{CACHE_BACKEND}', },
}
CACHES_HELP = 'A dictionary containing the settings for all caches to be used with Django.'

########################################################################################################################
# django-redis-websocket
########################################################################################################################
WS4REDIS_DB = 15
WS4REDIS_CONNECTION = {'host': '{REDIS_HOST}', 'port': '{REDIS_PORT}', 'db': SettingReference('WS4REDIS_DB'), }
WS4REDIS_CONNECTION_HELP = 'If the Redis datastore uses connection settings other than the defaults.'
WS4REDIS_EXPIRE = 0
WS4REDIS_EMULATION_INTERVAL = 0
# number of milliseconds between HTTP requests to emulate websockets
# should not be less than 1000
# leave it to 0 to desactivate this behavior
WS4REDIS_PREFIX = 'ws'
WS4REDIS_HEARTBEAT = '--HEARTBEAT--'
# Python dotted path to the WSGI application used by Django's runserver.
# WSGI_APPLICATION = 'djangofloor.wsgi_http.application'
WSGI_APPLICATION = 'djangofloor.wsgi_http.application'
if FLOOR_USE_WS4REDIS:
    WSGI_APPLICATION = 'ws4redis.django_runserver.application'
WS4REDIS_SUBSCRIBER = 'djangofloor.df_ws4redis.Subscriber'
FLOOR_WS_FACILITY = 'djangofloor'
FLOOR_SIGNAL_ENCODER = 'django.core.serializers.json.DjangoJSONEncoder'
FLOOR_SIGNAL_DECODER = 'json.JSONDecoder'
########################################################################################################################
# celery
########################################################################################################################
USE_CELERY = False
CELERY_TIMEZONE = '{TIME_ZONE}'
CELERY_RESULT_EXCHANGE = '{PROJECT_NAME}_results'
CELERY_ACCEPT_CONTENT = ['json', 'yaml', 'msgpack']
BROKER_DB = 13
BROKER_DB_HELP = 'database name of your Celery instance'
BROKER_URL = 'redis://{REDIS_HOST}:{REDIS_PORT}/{BROKER_DB}'
CELERY_APP = 'djangofloor'
CELERY_CREATE_DIRS = True
CELERY_TASK_SERIALIZER = 'json'

########################################################################################################################
# logging
########################################################################################################################
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'djangofloor.log.FloorAdminEmailHandler',
            'min_interval': 600,
        },
        'stream': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'logging.StreamHandler',
        },
        'debug': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': [
                'stream',
                'mail_admins',
            ],
            'level': 'ERROR',
            'propagate': False,
        },
        'djangofloor.signals': {
            'handlers': [
                'debug',
                ],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}
LOGGING_HELP = 'A data structure containing configuration information.' \
               ' The contents of this data structure will be passed as the argument to the configuration method' \
               ' described in LOGGING_CONFIG.'

########################################################################################################################
# Raven
########################################################################################################################
SENTRY_DSN_URL = ''
SENTRY_DSN_URL_HELP = 'Sentry URL to send data to. https://docs.getsentry.com/'

RAVEN_CONFIG = {
    'dsn': '{SENTRY_DSN_URL}',
    'release': '{FLOOR_PROJECT_VERSION}',
}

FLOOR_PROJECT_VERSION = CallableSetting(guess_version)
