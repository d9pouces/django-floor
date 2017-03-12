# -*- coding: utf-8 -*-
"""Default values for all Django settings
======================================

Tries to define settings that are valid for deploying most of djangofloor-based websites.
"""
from __future__ import unicode_literals, print_function, absolute_import

import os

from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

from djangofloor.conf.callables import database_engine, url_parse_server_name, \
    url_parse_server_protocol, url_parse_server_port, url_parse_prefix, url_parse_ssl, project_name, \
    authentication_backends, ldap_user_search, allauth_installed_apps, allowed_hosts
from djangofloor.conf.config_values import Path, Directory, SettingReference, ExpandIterable, \
    CallableSetting, AutocreateFileContent
from djangofloor.log import log_configuration
from djangofloor.utils import is_package_present, guess_version

__author__ = 'Matthieu Gallet'

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
USE_CELERY = is_package_present('celery')
USE_REDIS_SESSIONS = is_package_present('redis_sessions')
USE_SCSS = is_package_present('scss')
USE_PIPELINE = is_package_present('pipeline')
USE_DEBUG_TOOLBAR = is_package_present('debug_toolbar')
USE_REST_FRAMEWORK = is_package_present('rest_framework')
USE_ALL_AUTH = is_package_present('allauth')
# ######################################################################################################################
#
# settings that can be kept as-is
# of course, you can override them in your default settings
#
# ######################################################################################################################
ADMINS = (('admin', '{ADMIN_EMAIL}'),)
ALLOWED_HOSTS = CallableSetting(allowed_hosts)
if USE_REDIS_CACHE:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': '{CACHE_REDIS_PROTOCOL}://:{CACHE_REDIS_PASSWORD}@{CACHE_REDIS_HOST}:{CACHE_REDIS_PORT}/'
                        '{CACHE_REDIS_DB}',
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}
        }
    }
else:
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-snowflake'}}
CSRF_COOKIE_DOMAIN = '{SERVER_NAME}'
CSRF_TRUSTED_ORIGINS = ['{SERVER_NAME}']
DATABASES = {'default': {
    'ENGINE': CallableSetting(database_engine), 'NAME': '{DATABASE_NAME}', 'USER': '{DATABASE_USER}',
    'OPTIONS': SettingReference('DATABASE_OPTIONS'),
    'PASSWORD': '{DATABASE_PASSWORD}', 'HOST': '{DATABASE_HOST}', 'PORT': '{DATABASE_PORT}'},
}
DEBUG = False
# you should create a "local_settings.py" with "DEBUG = True" at the root of your project
DEFAULT_FROM_EMAIL = 'webmaster@{SERVER_NAME}'
FILE_UPLOAD_TEMP_DIR = Directory('{LOCAL_PATH}/tmp-uploads')
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
    ExpandIterable('DF_INSTALLED_APPS'),
    ExpandIterable('ALLAUTH_INSTALLED_APPS'),
    'bootstrap3',
]
if USE_DEBUG_TOOLBAR:
    INSTALLED_APPS.append('debug_toolbar')
if USE_PIPELINE:
    INSTALLED_APPS.append('pipeline')
if USE_REST_FRAMEWORK:
    INSTALLED_APPS.append('rest_framework')
INSTALLED_APPS.append('djangofloor')
INSTALLED_APPS.append(ExpandIterable('DF_EXTRA_INSTALLED_APPS'))
LOGGING = CallableSetting(log_configuration)
MANAGERS = SettingReference('ADMINS')
MEDIA_ROOT = Directory('{LOCAL_PATH}/media')
MEDIA_URL = '/media/'
MIDDLEWARE_CLASSES = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'djangofloor.middleware.DjangoFloorMiddleware',
    ExpandIterable('DF_MIDDLEWARE_CLASSES'),
    'django.middleware.cache.FetchFromCacheMiddleware',
]
if USE_DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES.insert(-3, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'djangofloor.root_urls'
SERVER_EMAIL = 'root@{SERVER_NAME}'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 0
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # X-Forwarded-Proto or None
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': SettingReference('TEMPLATE_DIRS'),
        'OPTIONS': {'context_processors': SettingReference('TEMPLATE_CONTEXT_PROCESSORS'),
                    'loaders': SettingReference('TEMPLATE_LOADERS')},
    },
]
TEMPLATE_DEBUG = False  # SettingReference('DEBUG')
TEMPLATE_DIRS = ()
TEMPLATE_CONTEXT_PROCESSORS = ['django.contrib.auth.context_processors.auth',
                               'django.template.context_processors.debug',
                               'django.template.context_processors.i18n',
                               'django.template.context_processors.media',
                               'django.template.context_processors.static',
                               'django.template.context_processors.tz',
                               'django.contrib.messages.context_processors.messages',
                               'djangofloor.context_processors.context_base',
                               ExpandIterable('DF_TEMPLATE_CONTEXT_PROCESSORS'),
                               ]
TEMPLATE_LOADERS = ('django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader')
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
USE_TZ = True
USE_X_FORWARDED_HOST = True  # X-Forwarded-Host
X_FRAME_OPTIONS = 'SAMEORIGIN'
WSGI_APPLICATION = 'djangofloor.wsgi.django_runserver.django_application'

# django.contrib.auth
AUTHENTICATION_BACKENDS = CallableSetting(authentication_backends)
LOGIN_URL = '/admin/login/'

# django.contrib.sessions
if USE_REDIS_SESSIONS:
    SESSION_ENGINE = 'redis_sessions.session'

# django.contrib.sites
SITE_ID = 1

# django.contrib.staticfiles
STATIC_ROOT = Directory('{LOCAL_PATH}/static')
STATIC_URL = '/static/'
if USE_PIPELINE:
    STATICFILES_STORAGE = 'djangofloor.backends.DjangofloorPipelineCachedStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATICFILES_FINDERS = ['django.contrib.staticfiles.finders.FileSystemFinder',
                       'django.contrib.staticfiles.finders.AppDirectoriesFinder']
if USE_PIPELINE:
    STATICFILES_FINDERS.append('pipeline.finders.PipelineFinder')

# celery
BROKER_URL = '{CELERY_PROTOCOL}://{CELERY_HOST}:{CELERY_PORT}/{CELERY_DB}'
CELERY_DEFAULT_QUEUE = 'celery'
CELERY_TIMEZONE = '{TIME_ZONE}'
CELERY_RESULT_EXCHANGE = '{DF_MODULE_NAME}_results'
CELERY_ACCEPT_CONTENT = ['json', 'yaml', 'msgpack']
CELERY_APP = 'djangofloor'
CELERY_CREATE_DIRS = True
CELERY_TASK_SERIALIZER = 'json'

# django-npm
NPM_EXECUTABLE_PATH = 'npm'
NPM_ROOT_PATH = Directory('{LOCAL_PATH}/npm')
NPM_STATIC_FILES_PREFIX = 'vendor'

# djangofloor
DATA_PATH = Directory('{LOCAL_PATH}/data')
SERVER_NAME = CallableSetting(url_parse_server_name)  # ~ www.example.org
SERVER_PORT = CallableSetting(url_parse_server_port)  # ~ 443
SERVER_PROTOCOL = CallableSetting(url_parse_server_protocol)  # ~ "https"
URL_PREFIX = CallableSetting(url_parse_prefix)  # ~ /prefix/
USE_HTTP_BASIC_AUTH = True  # HTTP-Authorization
USE_SSL = CallableSetting(url_parse_ssl)  # ~ True
USE_X_FORWARDED_FOR = True  # X-Forwarded-For
USE_X_SEND_FILE = False  # Apache module
X_ACCEL_REDIRECT = []  # paths used by nginx
DF_FAKE_AUTHENTICATION_USERNAME = None
DF_PROJECT_VERSION = CallableSetting(guess_version)
DF_REMOVED_DJANGO_COMMANDS = {'startapp', 'startproject'}
DF_PUBLIC_SIGNAL_LIST = True
# do not check for each WS signal/function before sending its name to the client
DF_EXTRA_INSTALLED_APPS = []
DF_SYSTEM_CHECKS = ['djangofloor.views.monitoring.RequestCheck',
                    'djangofloor.views.monitoring.System',
                    'djangofloor.views.monitoring.CeleryStats',
                    'djangofloor.views.monitoring.Packages',
                    'djangofloor.views.monitoring.LogLastLines', ]
WINDOW_INFO_MIDDLEWARES = ['djangofloor.middleware.WindowKeyMiddleware',
                           'djangofloor.middleware.DjangoAuthMiddleware',
                           'djangofloor.middleware.Djangoi18nMiddleware',
                           'djangofloor.middleware.BrowserMiddleware', ]

WEBSOCKET_URL = '/ws/'
WEBSOCKET_REDIS_CONNECTION = {'host': '{WEBSOCKET_REDIS_HOST}', 'port': SettingReference('WEBSOCKET_REDIS_PORT'),
                              'db': SettingReference('WEBSOCKET_REDIS_DB'), 'password': '{WEBSOCKET_REDIS_PASSWORD}'}
WEBSOCKET_TOPIC_SERIALIZER = 'djangofloor.wsgi.topics.serialize_topic'
WEBSOCKET_HEARTBEAT = '--HEARTBEAT--'
WEBSOCKET_SIGNAL_DECODER = 'json.JSONDecoder'
WEBSOCKET_SIGNAL_ENCODER = 'django.core.serializers.json.DjangoJSONEncoder'
WEBSOCKET_REDIS_PREFIX = 'ws'
WEBSOCKET_REDIS_EXPIRE = 36000

# django-pipeline
PIPELINE = {
    'PIPELINE_ENABLED': SettingReference('PIPELINE_ENABLED'),
    'JAVASCRIPT': SettingReference('PIPELINE_JS'),
    'STYLESHEETS': SettingReference('PIPELINE_CSS'),
    'CSS_COMPRESSOR': SettingReference('PIPELINE_CSS_COMPRESSOR'),
    'JS_COMPRESSOR': SettingReference('PIPELINE_JS_COMPRESSOR'),
}
if USE_SCSS:
    PIPELINE_COMPILERS = ('djangofloor.middleware.PyScssCompiler',)
PIPELINE_CSS = {
    'default': {
        'source_filenames': SettingReference('DF_CSS'),
        'output_filename': 'css/default-all.css', 'extra_context': {'media': 'all'},
    },
    'bootstrap3': {
        'source_filenames': ['vendor/bootstrap3/dist/css/bootstrap.min.css',
                             'vendor/bootstrap3/dist/css/bootstrap-theme.min.css',
                             'vendor/font-awesome/css/font-awesome.min.css',
                             'css/djangofloor-bootstrap3.css', ExpandIterable('DF_CSS')],
        'output_filename': 'css/bootstrap3-all.css', 'extra_context': {'media': 'all'},
    },
    # 'metro-ui': {
    #     'source_filenames': ['vendor/metro-ui/build/css/metro.min.css',
    #                          'vendor/metro-ui/build/css/metro-icons.min.css',
    #                          'vendor/metro-ui/build/css/metro-responsive.min.css',
    #                          'vendor/font-awesome/css/font-awesome.min.css',
    #                          'css/djangofloor-metro-ui.css', ExpandIterable('DF_CSS')],
    #     'output_filename': 'css/metro-ui-all.css', 'extra_context': {'media': 'all'},
    # },
    'ie9': {
        'source_filenames': [],
        'output_filename': 'css/ie9.css', 'extra_context': {'media': 'all'},
    },
}
PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yuglify.YuglifyCompressor'
PIPELINE_ENABLED = True
PIPELINE_JS = {
    'default': {
        'source_filenames': [
            'vendor/jquery/dist/jquery.min.js',
            'js/djangofloor-base.js',
            ExpandIterable('DF_JS')
        ],
        'output_filename': 'js/default.js',
    },
    'bootstrap3': {
        'source_filenames': [
            'vendor/jquery/dist/jquery.js',
            'vendor/bootstrap3/dist/js/bootstrap.js',
            'js/djangofloor-base.js',
            'vendor/bootstrap-notify/bootstrap-notify.js',
            'js/djangofloor-bootstrap3.js',
            ExpandIterable('DF_JS')
        ],
        'output_filename': 'js/bootstrap3.js',
    },
    # 'metro-ui': {
    #     'source_filenames': ['vendor/jquery/dist/jquery.min.js', 'vendor/metro-ui/build/js/metro.min.js',
    #                          'js/djangofloor-base.js', 'js/djangofloor-metro-ui.js', ExpandIterable('DF_JS')],
    #     'output_filename': 'js/metro-ui.js',
    # },
    'ie9': {
        'source_filenames': ['vendor/html5shiv/dist/html5shiv.js', 'vendor/respond.js/dest/respond.src.js', ],
        'output_filename': 'js/ie9.js',
    }
}
PIPELINE_MIMETYPES = ((b'text/coffeescript', '.coffee'),
                      (b'text/less', '.less'),
                      (b'text/javascript', '.js'),
                      (b'text/x-sass', '.sass'),
                      (b'text/x-scss', '.scss'))
# PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yuglify.YuglifyCompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.JSMinCompressor'

# Django-All-Auth
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[{SERVER_NAME}] '
ACCOUNT_EMAIL_VERIFICATION = None
ALLAUTH_PROVIDERS = []
ALLAUTH_INSTALLED_APPS = CallableSetting(allauth_installed_apps)

# Django-Debug-Toolbar
DEBUG_TOOLBAR_CONFIG = {'JQUERY_URL': '{STATIC_URL}vendor/jquery/dist/jquery.min.js', }
DEBUG_TOOLBAR_PATCH_SETTINGS = False
INTERNAL_IPS = ('127.0.0.1', '::1', 'localhost', )

# Django-Bootstrap3
BOOTSTRAP3 = {
    'jquery_url': '{STATIC_URL}vendor/jquery/dist/jquery.min.js',
    'base_url': '{STATIC_URL}vendor/bootstrap3/dist/',
    'theme_url': None, 'include_jquery': False, 'horizontal_label_class': 'col-md-3',
    'horizontal_field_class': 'col-md-9', 'set_disabled': True, 'set_placeholder': False,
    'formset_renderers': {'default': 'bootstrap3.renderers.FormsetRenderer'},
    'form_renderers': {'default': 'bootstrap3.renderers.FormRenderer'},
    'field_renderers': {'default': 'bootstrap3.renderers.FieldRenderer',
                        'inline': 'bootstrap3.renderers.InlineFieldRenderer'},
}
# django-auth-ldap
AUTH_LDAP_SERVER_URI = None
AUTH_LDAP_BIND_DN = ""
AUTH_LDAP_BIND_PASSWORD = ""
AUTH_LDAP_SEARCH_BASE = 'ou=users,dc=example,dc=com'
AUTH_LDAP_FILTER = '(uid=%(user)s)'
AUTH_LDAP_USER_SEARCH = CallableSetting(ldap_user_search)
AUTH_LDAP_USER_DN_TEMPLATE = None
AUTH_LDAP_START_TLS = False

# ######################################################################################################################
#
# settings that should be customized for each project
# of course, you can redefine or override any setting
#
# ######################################################################################################################
# djangofloor
DF_CSS = []
DF_JS = []
DF_INDEX_VIEW = 'djangofloor.views.IndexView'
DF_SITE_SEARCH_VIEW = 'djangofloor.views.search.UserSearchView'
DF_LOGIN_VIEW = 'djangofloor.views.auth.LoginView'
DF_USER_SELF_REGISTRATION = True  # allow user to create their account themselves
DF_PROJECT_NAME = CallableSetting(project_name)
DF_URL_CONF = '{DF_MODULE_NAME}.urls.urlpatterns'
DF_INSTALLED_APPS = ['{DF_MODULE_NAME}']
DF_MIDDLEWARE_CLASSES = []
DF_REMOTE_USER_HEADER = None  # HTTP-REMOTE-USER
DF_DEFAULT_GROUPS = [_('Users')]
DF_TEMPLATE_CONTEXT_PROCESSORS = []
DF_CHECKED_REQUIREMENTS = ['django>=1.10', 'celery', 'django-bootstrap3', 'pip', 'psutil']

NPM_FILE_PATTERNS = {
    'bootstrap-notify': ['*.js'],
    'bootstrap3': ['dist/*'],
    'font-awesome': ['css/*', 'fonts/*'],
    'html5shiv': ['dist/*'],
    'jquery': ['dist/*'],
    'jquery-file-upload': ['css/*', 'js/*'],
    # 'metro-ui': ['build/*'],
    'respond.js': ['dest/*'],
}

# ######################################################################################################################
#
# settings that should be customized for each deployment
# {DF_MODULE_NAME}.iniconf:INI_MAPPING should be a list of ConfigField, allowing to define these settings in a .ini file
#
# ######################################################################################################################
ADMIN_EMAIL = 'admin@{SERVER_NAME}'  # aliased in settings.ini as "[global]admin_email"
DATABASE_ENGINE = 'sqlite3'  # aliased in settings.ini as "[database]engine"
DATABASE_NAME = Path('{LOCAL_PATH}/database.sqlite3')  # aliased in settings.ini as "[database]name"
DATABASE_USER = ''  # aliased in settings.ini as "[database]user"
DATABASE_PASSWORD = ''  # aliased in settings.ini as "[database]password"
DATABASE_HOST = ''  # aliased in settings.ini as "[database]host"
DATABASE_PORT = ''  # aliased in settings.ini as "[database]port"
DATABASE_OPTIONS = {}
EMAIL_HOST = 'localhost'  # aliased in settings.ini as "[email]host"
EMAIL_HOST_PASSWORD = ''  # aliased in settings.ini as "[email]password"
EMAIL_HOST_USER = ''  # aliased in settings.ini as "[email]user"
EMAIL_PORT = 25  # aliased in settings.ini as "[email]port"
EMAIL_SUBJECT_PREFIX = '{SERVER_NAME}'
EMAIL_USE_TLS = False  # aliased in settings.ini as "[email]use_tls"
EMAIL_USE_SSL = False  # aliased in settings.ini as "[email]use_ssl"
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
LANGUAGE_CODE = 'fr-fr'  # aliased in settings.ini as "[global]language_code"
SECRET_KEY = AutocreateFileContent('{LOCAL_PATH}/secret_key.txt', get_random_string, length=60, makedirs=False)
TIME_ZONE = 'Europe/Paris'  # aliased in settings.ini as "[global]time_zone"
LOG_REMOTE_URL = None  # aliased in settings.ini as "[global]log_remote_url"
LOG_SLOW_QUERIES_DURATION = None  # aliased in settings.ini as "[global]log_slow_queries_duration"

# djangofloor
LISTEN_ADDRESS = 'localhost:9000'  # aliased in settings.ini as "[global]listen_address"
LOCAL_PATH = './django_data'  # aliased in settings.ini as "[global]data"
__split_path = __file__.split(os.path.sep)
if 'lib' in __split_path:
    prefix = os.path.join(*__split_path[:__split_path.index('lib')])
    LOCAL_PATH = Directory('/%s/var/{DF_MODULE_NAME}' % prefix)
SERVER_BASE_URL = 'http://{LISTEN_ADDRESS}/'  # aliased in settings.ini as "[global]server_url"
LOG_DIRECTORY = '{LOCAL_PATH}/logs'

# django_redis
CACHE_REDIS_PROTOCOL = 'redis'  # aliased in settings.ini as "[cache]protocol"
CACHE_REDIS_HOST = 'localhost'  # aliased in settings.ini as "[cache]host"
CACHE_REDIS_PORT = 6379  # aliased in settings.ini as "[cache]port"
CACHE_REDIS_DB = 2  # aliased in settings.ini as "[cache]db"
CACHE_REDIS_PASSWORD = ''  # aliased in settings.ini as "[cache]password"

# django-redis-sessions
SESSION_REDIS_HOST = 'localhost'  # aliased in settings.ini as "[session]host"
SESSION_REDIS_PORT = 6379  # aliased in settings.ini as "[session]port"
SESSION_REDIS_DB = 3  # aliased in settings.ini as "[session]db"
SESSION_REDIS_PASSWORD = ''  # aliased in settings.ini as "[session]password"

# ws4redis
WEBSOCKET_REDIS_HOST = 'localhost'  # aliased in settings.ini as "[websocket]host"
WEBSOCKET_REDIS_PORT = 6379  # aliased in settings.ini as "[websocket]port"
WEBSOCKET_REDIS_DB = 11  # aliased in settings.ini as "[websocket]db"
WEBSOCKET_REDIS_PASSWORD = ''  # aliased in settings.ini as "[websocket]password"

# celery
CELERY_PROTOCOL = 'redis'
CELERY_HOST = 'localhost'  # aliased in settings.ini as "[celery]host"
CELERY_PORT = 6379  # aliased in settings.ini as "[celery]port"
CELERY_DB = 13  # aliased in settings.ini as "[celery]db"
CELERY_PASSWORD = ''  # aliased in settings.ini as "[celery]password"

# ######################################################################################################################
#
# deprecated settings
#
# ######################################################################################################################

# LISTEN_ADDRESS = SettingReference('LISTEN_ADDRESS')
# BROKER_DB = SettingReference('CELERY_DB')
# DF_EXTRA_APPS = DeprecatedSetting('FLOOR_EXTRA_APPS', msg='FLOOR_EXTRA_APPS should be merged to DF_INSTALLED_APPS.')
# DF_OTHER_ALLAUTH = DeprecatedSetting('OTHER_ALLAUTH', msg='OTHER_ALLAUTH should be merged to DF_INSTALLED_APPS.')
# FLOOR_AUTHENTICATION_HEADER = SettingReference('DF_REMOTE_USER_HEADER')
# FLOOR_BACKUP_SINGLE_TRANSACTION = False
# FLOOR_DEFAULT_GROUP_NAME = _('Users')
# FLOOR_FAKE_AUTHENTICATION_USERNAME = SettingReference('DF_FAKE_AUTHENTICATION_USERNAME')
# FLOOR_INDEX = None
# FLOOR_PROJECT_NAME = SettingReference('DF_PROJECT_NAME')
# FLOOR_PROJECT_VERSION = CallableSetting(guess_version)
# FLOOR_SIGNAL_DECODER = SettingReference('WEBSOCKET_SIGNAL_DECODER')
# FLOOR_SIGNAL_ENCODER = SettingReference('WEBSOCKET_SIGNAL_ENCODER')
# FLOOR_URL_CONF = SettingReference('DF_URL_CONF')
# FLOOR_USE_WS4REDIS = False
# FLOOR_WS_FACILITY = 'djangofloor'
# LOG_PATH = Path('{LOCAL_PATH}/log')
# LOGOUT_URL = '/df/logout/'
# MAX_REQUESTS = 10000
# PROTOCOL = SettingReference('SERVER_PROTOCOL')
# REDIS_HOST = SettingReference('CELERY_HOST')
# REDIS_PORT = SettingReference('CELERY_PORT')
# REVERSE_PROXY_IPS = ['127.0.0.1', ]
# REVERSE_PROXY_PORT = None  #
# REVERSE_PROXY_SSL_KEY_FILE = None
# REVERSE_PROXY_SSL_CRT_FILE = None
# REVERSE_PROXY_TIMEOUT = 300
# THREADS = 20
# USE_SCSS = False
# WORKERS = 1
# WEBSOCKET_REDIS_EMULATION_INTERVAL = 0
# WEBSOCKET_REDIS_SUBSCRIBER = 'djangofloor.df_ws4redis.Subscriber'
