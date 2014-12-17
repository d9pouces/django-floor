#coding=utf-8
""" Django settings for DjangoFloor project. """

__author__ = 'flanker'
from os.path import join, dirname, abspath
from django.utils.translation import ugettext_lazy as _
# define a root path for misc. Django data (SQLite database, static files, ...)
LOCAL_PATH = abspath(join(dirname(dirname(__file__)), 'django_data'))
LOG_PATH = '{LOCAL_PATH}/log'
DATA_PATH = '{LOCAL_PATH}/data'
DEBUG = True
DEBUG_HELP = 'A boolean that turns on/off debug mode.'
TEMPLATE_DEBUG = False
TEMPLATE_DEBUG_HELP = 'A boolean that turns on/off template debug mode.'
ADMINS = (("admin", "admin@localhost"), )
ADMINS_HELP = 'A tuple that lists people who get code error notifications.'
MANAGERS = ADMINS
MANAGERS_HELP = ('A tuple in the same format as ADMINS that specifies who should get broken link notifications '
                 'when BrokenLinkEmailsMiddleware is enabled.')
DEFAULT_FROM_EMAIL = 'admin@localhost'
DEFAULT_FROM_EMAIL_HELP = 'Default email address to use for various automated correspondence from the site manager(s).'
# noinspection PyUnresolvedReferences
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '{DATA_PATH}/database.sqlite3',  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    },
}
DATABASES_HELP = 'A dictionary containing the settings for all databases to be used with Django.'
TIME_ZONE = 'Europe/Paris'
TIME_ZONE_HELP = 'A string representing the time zone for this installation, or None. '
BIND_ADDRESS = 'localhost:9000'
BIND_ADDRESS_HELP = 'The socket to bind.'
THREADS = 1
THREADS_HELP = 'The number of worker threads for handling requests.'
WORKERS = 1
WORKERS_HELP = 'The number of worker process for handling requests.'
GUNICORN_PID_FILE = '{LOCAL_PATH}/run/{PROJECT_NAME}_gunicorn.pid'
GUNICORN_PID_FILE_HELP = 'A filename to use for the PID file. '
GUNICORN_ERROR_LOG_FILE = '{LOG_PATH}/gunicorn_error.log'
GUNICORN_ERROR_LOG_FILE_HELP = 'The Error log file to write to (Gunicorn).'
GUNICORN_ACCESS_LOG_FILE = '{LOG_PATH}/gunicorn_access.log'
GUNICORN_ACCESS_LOG_FILE_HELP = 'The Access log file to write to (Gunicorn).'
GUNICORN_LOG_LEVEL = 'info'
GUNICORN_LOG_LEVEL_HELP = 'The granularity of Gunicorn Error log outputs.'

USE_X_SEND_FILE = False
USE_X_SEND_FILE_HELP = 'Use the XSendFile header in Apache or LightHTTPd for sending large files'
X_ACCEL_REDIRECT = []
X_ACCEL_REDIRECT_HELP = 'Use the X-Accel-Redirect header in NGinx. List of tuples (/directory_path/, /alias_url/).'
ALLOWED_HOSTS = ['127.0.0.1', ]
ALLOWED_HOSTS_HELP = 'A list of strings representing the host/domain names that this Django site can serve.'
REVERSE_PROXY_IPS = []
REVERSE_PROXY_IPS_HELP = 'List of IP addresses of reverse proxies'
REVERSE_PROXY_TIMEOUT = 30
REVERSE_PROXY_TIMEOUT_HELP = 'Workers silent for more than this many seconds are killed and restarted.'
REVERSE_PROXY_ERROR_LOG_FILE = '{LOG_PATH}/error.log'
REVERSE_PROXY_ERROR_LOG_FILE_HELP = 'Error log file to write to (Reverse proxy).'
REVERSE_PROXY_ACCESS_LOG_FILE = '{LOG_PATH}/access.log'
REVERSE_PROXY_ACCESS_LOG_FILE_HELP = 'The Access log file to write to (reverse_proxy).'
REVERSE_PROXY_SSL_KEY_FILE = None
REVERSE_PROXY_SSL_KEY_FILE_HELP = 'Key file of reverse proxy. Can be set to None if the key is with the certificate.'
REVERSE_PROXY_SSL_CRT_FILE = None
REVERSE_PROXY_SSL_CRT_FILE_hep = 'SSL certificate file of reverse proxy. Required if you use SSL'
REVERSE_PROXY_PORT = None  #
REVERSE_PROXY_PORT_HELP = 'Reverse proxy port (if None, defaults to 80 or 443 if you use SSL)'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-fr'
LANGUAGE_CODE_HELP = 'A string representing the language code for this installation.'
# Make this unique, and don't share it with anybody.
SECRET_KEY = 'NEZ6ngWX0JihNG2wepl1uxY7bkPOWrTEo27vxPGlUM3eBAYfPT'
SECRET_KEY_HELP = ('A secret key for a particular Django installation. This is used to provide cryptographic signing, '
                   'and should be set to a unique, unpredictable value.')
PIPELINE_ENABLED = False
PIPELINE_ENABLED_HELP = 'True if assets should be compressed, False if not.'
PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.slimit.SlimItCompressor'
PIPELINE_CSS_COMPRESSOR_HELP = 'Compressor class to be applied to CSS files.'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.JSMinCompressor'
PIPELINE_JS_COMPRESSOR_HELP = 'Compressor class to be applied to JavaScript files.'
AUTHENTICATION_HEADER = 'REMOTE_USER'
AUTHENTICATION_HEADER_HELP = 'Name of the header set by your reverse-proxy server (probably HTTP_REMOTE_USER).'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache', }, }
CACHES_HELP = 'A dictionary containing the settings for all caches to be used with Django.'
ACCOUNT_EMAIL_VERIFICATION = None

# iterable of URL of your application. 'my_app.root_urls.urls'
FLOOR_URLCONF = None
FLOOR_INSTALLED_APPS = []
FLOOR_INDEX = None
FLOOR_PROJECT_NAME = _('DjangoFloor')
FLOOR_ = ''
DEFAULT_GROUP_NAME = _('Users')
DEFAULT_GROUP_NAME_HELP = 'Name of the default group of newly-created users.'
PIPELINE_JS = {
    'base': {'source_filenames': ['js/jquery.min.js', 'bootstrap3/js/bootstrap.min.js',
                                  'js/django_fontawesome.js', 'select2/select2.min.js', ],
             'output_filename': 'js/base.js', },
}
PIPELINE_CSS = {
    'base': {'source_filenames': ['bootstrap3/css/bootstrap.min.css', 'select2/select2.css',
                                  'select2-bootstrap.css', 'css/font-awesome.min.css', ],
             'output_filename': 'css/base.css', 'extra_context': {'media': 'all'}, }, }


EMAIL_HOST = 'localhost'
EMAIL_HOST_HELP = 'The host to use for sending email.'
EMAIL_HOST_PASSWORD = ''
EMAIL_HOST_PASSWORD_HELP = 'Password to use for the SMTP server defined in EMAIL_HOST. This setting is used in ' \
                           'conjunction with EMAIL_HOST_USER when authenticating to the SMTP server. If either of ' \
                           'these settings is empty, Django won’t attempt authentication'
EMAIL_HOST_USER = ''
EMAIL_HOST_USER_HELP = 'Username to use for the SMTP server defined in EMAIL_HOST. If empty, Django won’t attempt ' \
                       'authentication.'
EMAIL_PORT = 25
EMAIL_PORT_HELP = 'Port to use for the SMTP server defined in EMAIL_HOST.'

EMAIL_SUBJECT_PREFIX = '[Django] '
EMAIL_SUBJECT_PREFIX_HELP = 'Subject-line prefix for email messages sent with django.core.mail.mail_admins or ' \
                            'django.core.mail.mail_managers. You’ll probably want to include the trailing space'
EMAIL_USE_TLS = False
EMAIL_USE_TLS_HELP = 'Whether to use a TLS (secure) connection when talking to the SMTP server.' \
                     ' This is used for explicit TLS connections, generally on port 587.'
EMAIL_USE_SSL = False
EMAIL_USE_SSL_HELP = 'Whether to use an implicit TLS (secure) connection when talking to the SMTP server. In most' \
                     ' email documentation this type of TLS connection is referred to as SSL. It is generally used ' \
                     'on port 465. If you are experiencing problems, see the explicit TLS setting EMAIL_USE_TLS.'
SERVER_EMAIL = 'root@localhost'
SERVER_EMAIL_HELP = 'The email address that error messages come from, such as those sent to ADMINS and MANAGERS.'
FILE_CHARSET = 'utf-8'
FILE_CHARSET_HELP = 'The character encoding used to decode any files read from disk. This includes template files and' \
                    ' initial SQL data files.'
FILE_UPLOAD_TEMP_DIR = None
FILE_UPLOAD_TEMP_DIR_HELP = 'The directory to store data temporarily while uploading files. If None, Django will use ' \
                            'the standard temporary directory for the operating system. For example, this will ' \
                            'default to ‘/tmp’ on *nix-style operating systems.'

DATABASE_ROUTERS = ['djangofloor.routers.BaseRouter', ]

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
MEDIA_ROOT = '{DATA_PATH}/media'
MEDIA_ROOT_HELP = 'Absolute filesystem path to the directory that will hold user-uploaded files.'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
# noinspection PyUnresolvedReferences
STATIC_ROOT = '{LOCAL_PATH}/static'
STATIC_ROOT_HELP = 'The absolute path to the directory where collectstatic will collect static files for deployment.'
# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    abspath(join(dirname(__file__), 'static')),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = ['django.contrib.staticfiles.finders.AppDirectoriesFinder',
                       'django.contrib.staticfiles.finders.FileSystemFinder', ]


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
]

MIDDLEWARE_CLASSES = ['django.middleware.cache.UpdateCacheMiddleware',
                      'django.middleware.common.CommonMiddleware',
                      'django.contrib.sessions.middleware.SessionMiddleware',
                      'django.middleware.csrf.CsrfViewMiddleware',
                      'django.contrib.auth.middleware.AuthenticationMiddleware',
                      'django.contrib.messages.middleware.MessageMiddleware',
                      'django.middleware.clickjacking.XFrameOptionsMiddleware',
                      'djangofloor.middleware.IEMiddleware',
                      'djangofloor.middleware.RemoteUserMiddleware',
                      'djangofloor.middleware.BasicAuthMiddleware',
                      'djangofloor.middleware.FakeAuthenticationMiddleware',
                      'pipeline.middleware.MinifyHTMLMiddleware',
                      'django.middleware.cache.FetchFromCacheMiddleware', ]
INTERNAL_IPS = ('127.0.0.1', )

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
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
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_PROXY_SSL_HEADER_HELP = 'A tuple representing a HTTP header/value combination that signifies a request is ' \
                               'secure. This controls the behavior of the request object’s is_secure() method.'
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_HOST_HELP = 'A boolean that specifies whether to use the X-Forwarded-Host header in preference to ' \
                            'the Host header. '
AUTHENTICATION_BACKENDS = [
    'djangofloor.backends.DefaultGroupRemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
]

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'djangofloor.context_processors.context_base',
    'allauth.account.context_processors.account',
    'allauth.socialaccount.context_processors.socialaccount',
)
ROOT_URLCONF = 'djangofloor.root_urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'djangofloor.wsgi.application'

TEMPLATE_DIRS = (
    abspath(join(dirname(__file__), 'templates')),
)

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
    'django_admin_bootstrapped.bootstrap3',
    'django_admin_bootstrapped',
    'django.contrib.admin',
    'pipeline',
    'bootstrap3',
    'fontawesome',
    'djangofloor',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
]

OTHER_ALLAUTH = []
OTHER_ALLAUTH_HELP = 'Other allauth authentication providers, merely a list of allauth.socialaccount.providers.*'

BOOTSTRAP3 = {
    'jquery_url': '{STATIC_URL}js/jquery.min.js',
    'base_url': '{STATIC_URL}bootstrap3/',
    'css_url': None,
    'theme_url': None,
    'javascript_url': None,
    'horizontal_label_class': 'col-md-2',
    'horizontal_field_class': 'col-md-4',
}
FONTAWESOME_CSS_URL = 'css/font-awesome.min.css'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
# Pipeline configuration

PIPELINE_MIMETYPES = (
    ('text/coffeescript', '.coffee'),
    ('text/less', '.less'),
    ('text/javascript', '.js'),  # required for IE8
    ('text/x-sass', '.sass'),
    ('text/x-scss', '.scss')
)
PIPELINE_DISABLE_WRAPPER = True
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        # 'rotating_file': {
        #     'level': 'INFO',
        #     'filters': ['require_debug_false'],
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': '{LOG_PATH}/django.log',
        #     'maxBytes': 10000000,  # 10 MB
        #     'backupCount': 2,
        #     'encoding': 'utf-8',
        # }
    },
    'loggers': {
        'django.request': {
            'handlers': [
                'mail_admins',
                # 'rotating_file'
            ],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
LOGGING_HELP = 'A data structure containing configuration information.' \
               ' The contents of this data structure will be passed as the argument to the configuration method' \
               ' described in LOGGING_CONFIG.'

FAKE_AUTHENTICATION_USERNAME = 'test'
# used to fake a reverse proxy authentication for development purpose
FAKE_AUTHENTICATION_GROUPS = ['group1', 'group2']
# used to fake LDAP groups, added to the remotely-authenticated user

MAX_REQUESTS = 10000
MAX_REQUESTS_HELP = 'The maximum number of requests a worker will process before restarting.'

LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
LOGIN_REDIRECT_URL = '/'

########################################################################################################################
# django-redis-websocket
########################################################################################################################
WEBSOCKET_URL = '/ws/'
WS4REDIS_CONNECTION = {}
WS4REDIS_CONNECTION_HELP = 'If the Redis datastore uses connection settings other than the defaults ' \
                           '(keys are "host"/"port"/"db"/"password").'

########################################################################################################################
# ldap_groups
########################################################################################################################
LDAP_GROUPS_URL = None
LDAP_GROUPS_URL_HELP = 'the complete url in the scheme://hostname:hostport format of the server. ' \
                       'Can use several servers, separated by commas.'
LDAP_GROUPS_TLS = None
LDAP_GROUPS_TLS_HELP = 'Tls object that contains information about the certificates and the trusted roots needed to' \
                       'establish a secure connection (defaults to None). If None any server certificate will be ' \
                       'accepted.'
LDAP_GROUPS_BIND_DN = ''
LDAP_GROUPS_BIND_DN_HELP = 'The distinguished name to use when binding to the LDAP server. ' \
                           'Use the empty string (the default) for an anonymous bind.'
LDAP_GROUPS_BIND_PASSWORD = ''
LDAP_GROUPS_BIND_PASSWORD_HELP = 'The password to use with LDAP_GROUPS_BIND_DN.'
LDAP_GROUPS_CACHE_GROUPS_TIME = 0
LDAP_GROUPS_CACHE_GROUPS_TIME_HELP = 'If non-zero, LDAP group membership will be cached using Django’s cache ' \
                                     'framework. Otherwhise, this is the cache timeout (in seconds).'
LDAP_GROUPS_SEARCH_BASE = 'CN=Users,DC=example,DC=org'
LDAP_GROUPS_SEARCH_BASE_HELP = 'The base DN for the search'
LDAP_GROUPS_SEARCH_FILTER = '(cn=%(username)s)'
LDAP_GROUPS_SEARCH_FILTER_HELP = 'Filter to use for the search. %(username)s and %(email)s are available.'
LDAP_GROUPS_SEARCH_SCOPE = 'SUBTREE'
LDAP_GROUPS_SEARCH_SCOPE_HELP = 'Either SUBTREE (default), BASE or SINGLE_LEVEL'
LDAP_GROUPS_SEARCH_GROUP_ATTRIBUTE = 'memberOf'
LDAP_GROUPS_SEARCH_GROUP_ATTRIBUTE_HELP = 'Name of the attribute with the list of the user groups.'
LDAP_GROUPS_FORMAT_GROUP_NAME = None
LDAP_GROUPS_FORMAT_GROUP_NAME_HELP = 'If not None, the name of a Python function ("package.module.function"), ' \
                                     'my_function(request, LDAP_group_name) must return a nicely-formatted name.'

########################################################################################################################
# celery
########################################################################################################################
USE_CELERY = True
CELERY_TIMEZONE = '{TIME_ZONE}'
CELERY_RESULT_EXCHANGE = '{PROJECT_NAME}_results'
CELERY_ACCEPT_CONTENT = ['json', 'yaml', 'msgpack']
BROKER_URL = 'redis://localhost:6379/0'
CELERY_PID_FILE = '{LOCAL_PATH}/run/{PROJECT_NAME}_celery.pid'
CELERY_PID_FILE_HELP = 'A filename to use for the PID file. '
CELERY_APP = 'djangofloor'
CELERY_CREATE_DIRS = True
CELERY_LOG_FILE = '{LOG_PATH}/celerybeat.log'
CELERY_TASK_SERIALIZER = 'json'