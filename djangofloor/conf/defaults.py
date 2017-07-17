"""Default values for all Django settings
======================================

Tries to define settings that are valid for deploying most of djangofloor-based websites.
"""

import os

from django.utils.translation import ugettext_lazy as _

from djangofloor.conf.callables import database_engine, url_parse_server_name, \
    url_parse_server_protocol, url_parse_server_port, url_parse_prefix, url_parse_ssl, project_name, \
    authentication_backends, ldap_user_search, allauth_installed_apps, allowed_hosts, cache_setting, template_setting, \
    generate_secret_key
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
CACHES = CallableSetting(cache_setting)
CSRF_COOKIE_DOMAIN = '{SERVER_NAME}'
CSRF_TRUSTED_ORIGINS = ['{SERVER_NAME}', '{SERVER_NAME}:{SERVER_PORT}']
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
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    ExpandIterable('DF_INSTALLED_APPS'),
    ExpandIterable('ALLAUTH_INSTALLED_APPS'),
    'bootstrap3',
    'djangofloor',
    'django.contrib.staticfiles',
    'django.contrib.admin',
]
if USE_DEBUG_TOOLBAR:
    INSTALLED_APPS.append('debug_toolbar')
if USE_PIPELINE:
    INSTALLED_APPS.append('pipeline')
if USE_REST_FRAMEWORK:
    INSTALLED_APPS.append('rest_framework')
INSTALLED_APPS.append(ExpandIterable('DF_EXTRA_INSTALLED_APPS'))
LOGGING = CallableSetting(log_configuration)
MANAGERS = SettingReference('ADMINS')
MEDIA_ROOT = Directory('{LOCAL_PATH}/media')
MEDIA_URL = '/media/'
MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'djangofloor.middleware.DjangoFloorMiddleware',
    ExpandIterable('DF_MIDDLEWARE'),
    'django.middleware.cache.FetchFromCacheMiddleware',
]
if USE_DEBUG_TOOLBAR:
    MIDDLEWARE.insert(-3, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'djangofloor.root_urls'
SERVER_EMAIL = '{ADMIN_EMAIL}'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = SettingReference('USE_SSL')
SECURE_HSTS_PRELOAD = SettingReference('USE_SSL')
SECURE_HSTS_SECONDS = 0
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # X-Forwarded-Proto or None
SECURE_SSL_REDIRECT = SettingReference('USE_SSL')
SECURE_FRAME_DENY = SettingReference('USE_SSL')
TEMPLATES = CallableSetting(template_setting)
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
SESSION_COOKIE_SECURE = SettingReference('USE_SSL')

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
DF_SERVER_TIMEOUT = 30
DF_SERVER_THREADS = 2
DF_SERVER_PROCESSES = 2

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

# django-cors-headers
CORS_ORIGIN_WHITELIST = ('{SERVER_NAME}', '{SERVER_NAME}:{SERVER_PORT}')
CORS_REPLACE_HTTPS_REFERER = False

# django-hosts
DEFAULT_HOST = '{SERVER_NAME}'
HOST_SCHEME = '{SERVER_PROTOCOL}://'
HOST_PORT = '{SERVER_PORT}'

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
DF_MIDDLEWARE = []
DF_REMOTE_USER_HEADER = None  # HTTP-REMOTE-USER
DF_DEFAULT_GROUPS = [_('Users')]
DF_TEMPLATE_CONTEXT_PROCESSORS = []
DF_CHECKED_REQUIREMENTS = ['django>=1.10', 'celery', 'django-bootstrap3', 'redis', 'pip']

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
EMAIL_FROM = '{ADMIN_EMAIL}'  # aliased in settings.ini as "[email]from"
EMAIL_PORT = 25  # aliased in settings.ini as "[email]port"
EMAIL_SUBJECT_PREFIX = '[{SERVER_NAME}] '
EMAIL_USE_TLS = False  # aliased in settings.ini as "[email]use_tls"
EMAIL_USE_SSL = False  # aliased in settings.ini as "[email]use_ssl"
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
LANGUAGE_CODE = 'fr-fr'  # aliased in settings.ini as "[global]language_code"
SECRET_KEY = AutocreateFileContent('{LOCAL_PATH}/secret_key.txt', generate_secret_key, mode=0o600, length=60)
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
LOG_DIRECTORY = Directory('{LOCAL_PATH}/log')

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
WEBSOCKET_REDIS_DB = 3  # aliased in settings.ini as "[websocket]db"
WEBSOCKET_REDIS_PASSWORD = ''  # aliased in settings.ini as "[websocket]password"

# celery
CELERY_PROTOCOL = 'redis'
CELERY_HOST = 'localhost'  # aliased in settings.ini as "[celery]host"
CELERY_PORT = 6379  # aliased in settings.ini as "[celery]port"
CELERY_DB = 4  # aliased in settings.ini as "[celery]db"
CELERY_PASSWORD = ''  # aliased in settings.ini as "[celery]password"
