"""Callables settings
==================


"""

import grp
import os
import pwd
import re
# noinspection PyUnresolvedReferences
from collections import OrderedDict
from urllib.parse import urlparse

from django.core.checks import Error
from django.utils.crypto import get_random_string
from django.utils.module_loading import import_string
from pkg_resources import get_distribution, DistributionNotFound

from djangofloor.checks import settings_check_results, missing_package
from djangofloor.conf.config_values import ExpandIterable

__author__ = 'Matthieu Gallet'

_default_engines = {'mysql': 'django.db.backends.mysql',
                    'mariadb': 'django.db.backends.mysql',
                    'oracle': 'django.db.backends.oracle',
                    'postgres': 'django.db.backends.postgresql',
                    'postgresql': 'django.db.backends.postgresql',
                    'sqlite': 'django.db.backends.sqlite3',
                    'sqlite3': 'django.db.backends.sqlite3', }


def database_engine(settings_dict):
    """Allow to use aliases for database engines, as well as the default dotted name"""
    engine = _default_engines.get(settings_dict['DATABASE_ENGINE'].lower(), settings_dict['DATABASE_ENGINE'])
    if engine == 'django.db.backends.postgresql':
        try:
            get_distribution('psycopg2')
        except DistributionNotFound:
            missing_package('psycopg2', ' to use PostgreSQL database')
    elif engine == 'django.db.backends.oracle':
        try:
            get_distribution('cx_Oracle')
        except DistributionNotFound:
            missing_package('cx_Oracle', ' to use Oracle database')
    elif engine == 'django.db.backends.mysql':
        try:
            get_distribution('mysqlclient')
        except DistributionNotFound:
            missing_package('mysqlclient', ' to use MySQL or MariaDB database')
    return engine


database_engine.required_settings = ['DATABASE_ENGINE']


def databases(settings_dict):
    engine = database_engine(settings_dict)
    name = settings_dict['DATABASE_NAME']
    user = settings_dict['DATABASE_USER']
    options = settings_dict['DATABASE_OPTIONS']
    password = settings_dict['DATABASE_PASSWORD']
    host = settings_dict['DATABASE_HOST']
    port = settings_dict['DATABASE_PORT']
    if 'DATABASE_URL' in os.environ:  # Used on Heroku environment
        parsed = urlparse(os.environ['DATABASE_URL'])
        engine = database_engine({'DATABASE_ENGINE': parsed.scheme})
        user = parsed.username
        name = parsed.path[1:]
        password = parsed.password
        host = parsed.hostname
        port = parsed.port
    return {'default': {'ENGINE': engine, 'NAME': name, 'USER': user, 'OPTIONS': options, 'PASSWORD': password,
                        'HOST': host, 'PORT': port}}


databases.required_settings = ['DATABASE_ENGINE', 'DATABASE_NAME', 'DATABASE_USER', 'DATABASE_OPTIONS',
                               'DATABASE_PASSWORD', 'DATABASE_HOST', 'DATABASE_PORT']


def allowed_hosts(settings_dict):
    result = {'127.0.0.1', '::1', 'localhost'}
    listened_ip, sep, port = settings_dict['LISTEN_ADDRESS'].rpartition(':')
    if sep == ':' and listened_ip not in ('::', '0.0.0.0'):
        result.add(listened_ip)
    result.add(settings_dict['SERVER_NAME'])
    return list(sorted(result))


allowed_hosts.required_settings = ['SERVER_NAME', 'LISTEN_ADDRESS']


def cache_setting(settings_dict):
    """Automatically compute cache settings:
      * if debug mode is set, then caching is disabled
      * if django_redis is available, then Redis is used for caching
      * else memory is used

    :param settings_dict:
    :return:
    """
    if settings_dict['DEBUG']:
        return {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
    elif settings_dict['USE_REDIS_CACHE']:
        return {'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': '{CACHE_REDIS_PROTOCOL}://:{CACHE_REDIS_PASSWORD}@{CACHE_REDIS_HOST}:{CACHE_REDIS_PORT}/'
                        '{CACHE_REDIS_DB}',
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}
        }
        }
    return {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-snowflake'}}


cache_setting.required_settings = ['USE_REDIS_CACHE', 'DEBUG']


def url_parse_server_name(settings_dict):
    """Return the public hostname, given the public base URL

    >>> url_parse_server_name({'SERVER_BASE_URL': 'https://demo.example.org/'})
    'demo.example.org'

    """
    return urlparse(settings_dict['SERVER_BASE_URL']).hostname


url_parse_server_name.required_settings = ['SERVER_BASE_URL']


def url_parse_server_port(settings_dict):
    """Return the public port, given the public base URL

    >>> url_parse_server_port({'SERVER_BASE_URL': 'https://demo.example.org/', 'USE_SSL': True})
    443
    >>> url_parse_server_port({'SERVER_BASE_URL': 'http://demo.example.org/', 'USE_SSL': False})
    80
    >>> url_parse_server_port({'SERVER_BASE_URL': 'https://demo.example.org:8010/', 'USE_SSL': True})
    8010

    """
    return urlparse(settings_dict['SERVER_BASE_URL']).port or (settings_dict['USE_SSL'] and 443) or 80


url_parse_server_port.required_settings = ['SERVER_BASE_URL', 'USE_SSL']


def url_parse_server_protocol(settings_dict):
    """Return the public HTTP protocol, given the public base URL

    >>> url_parse_server_protocol({'USE_SSL': True})
    'https'

    >>> url_parse_server_protocol({'USE_SSL': False})
    'http'

    """
    return 'https' if settings_dict['USE_SSL'] else 'http'


url_parse_server_protocol.required_settings = ['USE_SSL']


def url_parse_prefix(settings_dict):
    """Return the public URL prefix, given the public base URL

    >>> url_parse_prefix({'SERVER_BASE_URL': 'https://demo.example.org/demo/'})
    '/demo/'
    >>> url_parse_prefix({'SERVER_BASE_URL': 'http://demo.example.org/'})
    '/'
    >>> url_parse_prefix({'SERVER_BASE_URL': 'https://demo.example.org:8010'})
    '/'

    """
    p = urlparse(settings_dict['SERVER_BASE_URL']).path
    if not p.endswith('/'):
        p += '/'
    return p


url_parse_prefix.required_settings = ['SERVER_BASE_URL']


def url_parse_ssl(settings_dict):
    """Return True if the public URL uses https

    >>> url_parse_ssl({'SERVER_BASE_URL': 'https://demo.example.org/demo/'})
    True
    >>> url_parse_ssl({'SERVER_BASE_URL': 'http://demo.example.org/'})
    False

    """
    return urlparse(settings_dict['SERVER_BASE_URL']).scheme == 'https'


url_parse_ssl.required_settings = ['SERVER_BASE_URL']


def use_x_forwarded_for(settings_dict):
    """Return `True` if this server is assumed to be behind a reverse proxy.
     Heuristic: the external port (in SERVER_PORT) is different from the actually listened port (in LISTEN_ADDRESS).

     >>> use_x_forwarded_for({'SERVER_PORT': 8000, 'LISTEN_ADDRESS': 'localhost:8000'})
     False
     >>> use_x_forwarded_for({'SERVER_PORT': 443, 'LISTEN_ADDRESS': 'localhost:8000'})
     True

    """
    listen_address, sep, listen_port = settings_dict['LISTEN_ADDRESS'].rpartition(':')
    if not re.match(r'\d+', listen_port):
        raise ValueError('Invalid LISTEN_ADDRESS port %s' % listen_port)
    return int(listen_port) != settings_dict['SERVER_PORT']


use_x_forwarded_for.required_settings = ['SERVER_PORT', 'LISTEN_ADDRESS']


def project_name(settings_dict):
    """Transform the base module name into a nicer project name

    >>> project_name({'DF_MODULE_NAME': 'my_project'})
    'My Project'

    :param settings_dict:
    :return:
    """

    return ' '.join([x.capitalize() for x in settings_dict['DF_MODULE_NAME'].replace('_', ' ').split()])


project_name.required_settings = ['DF_MODULE_NAME']


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class AuthenticationBackends:
    required_settings = ['ALLAUTH_PROVIDERS', 'DF_REMOTE_USER_HEADER', 'AUTH_LDAP_SERVER_URI',
                         'USE_PAM_AUTHENTICATION', 'DF_ALLOW_LOCAL_USERS', 'USE_ALL_AUTH', 'RADIUS_SERVER']

    def __call__(self, settings_dict):
        backends = []
        backends += self.process_remote_user(settings_dict)
        backends += self.process_radius(settings_dict)
        backends += self.process_django(settings_dict)
        backends += self.process_django_ldap(settings_dict)
        backends += self.process_allauth(settings_dict)
        backends += self.process_pam(settings_dict)
        return backends

    def process_django(self, settings_dict):
        if settings_dict['DF_ALLOW_LOCAL_USERS']:
            return ['django.contrib.auth.backends.ModelBackend']
        return []

    def process_remote_user(self, settings_dict):
        if settings_dict['DF_REMOTE_USER_HEADER']:
            return ['djangofloor.backends.DefaultGroupsRemoteUserBackend']
        return []

    def process_allauth(self, settings_dict):
        if not settings_dict['USE_ALL_AUTH'] and not settings_dict['ALLAUTH_PROVIDERS']:
            return []
        try:
            get_distribution('django-allauth')
            return ['allauth.account.auth_backends.AuthenticationBackend']
        except DistributionNotFound:
            return []

    def process_radius(self, settings_dict):
        if not settings_dict['RADIUS_SERVER']:
            return []
        try:
            get_distribution('django-radius')
        except DistributionNotFound:
            missing_package('django-radius', ' to use RADIUS authentication')
            return []
        return ['radiusauth.backends.RADIUSBackend']

    def process_django_ldap(self, settings_dict):
        if not settings_dict['AUTH_LDAP_SERVER_URI']:
            return []
        try:
            get_distribution('django-auth-ldap')
        except DistributionNotFound:
            missing_package('django-auth-ldap', ' to use LDAP authentication')
            return []
        return ['django_auth_ldap.backend.LDAPBackend']

    def process_pam(self, settings_dict):
        if not settings_dict['USE_PAM_AUTHENTICATION']:
            return []
        try:
            get_distribution('django_pam')
        except DistributionNotFound:
            missing_package('django-pam', ' to use PAM authentication')
            return []
        # check if the current user is in the shadow group
        username = pwd.getpwuid(os.getuid()).pw_name
        if not any(x.gr_name == 'shadow' and username in x.gr_mem for x in grp.getgrall()):
            settings_check_results.append(Error('The user "%s" must belong to the "shadow" group to use PAM '
                                                'authentication.' % username,
                                                obj='djangofloor.conf.settings', id='djangofloor.E004'))
            return []
        return ['django_pam.auth.backends.PAMBackend']


authentication_backends = AuthenticationBackends()


def template_setting(settings_dict):
    loaders = ['django.template.loaders.filesystem.Loader', 'django.template.loaders.app_directories.Loader']
    if settings_dict['DEBUG']:
        backend = {'BACKEND': 'django.template.backends.django.DjangoTemplates', 'NAME': 'default',
                   'DIRS': settings_dict['TEMPLATE_DIRS'],
                   'OPTIONS': {'context_processors': settings_dict['TEMPLATE_CONTEXT_PROCESSORS'],
                               'loaders': loaders, 'debug': True}}
    else:
        backend = {'BACKEND': 'django.template.backends.django.DjangoTemplates', 'NAME': 'default',
                   'DIRS': settings_dict['TEMPLATE_DIRS'],
                   'OPTIONS': {
                       'context_processors': settings_dict['TEMPLATE_CONTEXT_PROCESSORS'],
                       'debug': False,
                       'loaders': [('django.template.loaders.cached.Loader', loaders)]
                   }}
    return [backend]


template_setting.required_settings = ['DEBUG', 'TEMPLATE_DIRS', 'TEMPLATE_CONTEXT_PROCESSORS']


def ldap_user_search(settings_dict):
    if settings_dict['AUTH_LDAP_SERVER_URI'] and settings_dict['AUTH_LDAP_USER_SEARCH_BASE']:
        try:
            # noinspection PyPackageRequirements,PyUnresolvedReferences
            import ldap
            # noinspection PyUnresolvedReferences
            from django_auth_ldap.config import LDAPSearch
        except ImportError:
            return None
        return LDAPSearch(settings_dict['AUTH_LDAP_USER_SEARCH_BASE'], ldap.SCOPE_SUBTREE,
                          settings_dict['AUTH_LDAP_FILTER'])
    return None


ldap_user_search.required_settings = ['AUTH_LDAP_USER_SEARCH_BASE', 'AUTH_LDAP_SERVER_URI', 'AUTH_LDAP_FILTER']


def ldap_group_search(settings_dict):
    if settings_dict['AUTH_LDAP_SERVER_URI'] and settings_dict['AUTH_LDAP_GROUP_SEARCH_BASE']:
        try:
            # noinspection PyPackageRequirements,PyUnresolvedReferences
            import ldap
            # noinspection PyUnresolvedReferences
            from django_auth_ldap.config import LDAPSearch
        except ImportError:
            return None
        return LDAPSearch(settings_dict['AUTH_LDAP_GROUP_SEARCH_BASE'], ldap.SCOPE_SUBTREE, '(objectClass=*)')
    return None


ldap_group_search.required_settings = ['AUTH_LDAP_GROUP_SEARCH_BASE', 'AUTH_LDAP_SERVER_URI']


def ldap_attribute_map(settings_dict):
    result = {}
    if settings_dict['AUTH_LDAP_USER_FIRST_NAME']:
        result['first_name'] = settings_dict['AUTH_LDAP_USER_FIRST_NAME']
    if settings_dict['AUTH_LDAP_USER_LAST_NAME']:
        result['last_name'] = settings_dict['AUTH_LDAP_USER_LAST_NAME']
    if settings_dict['AUTH_LDAP_USER_EMAIL']:
        result['email'] = settings_dict['AUTH_LDAP_USER_EMAIL']
    return result


ldap_attribute_map.required_settings = ['AUTH_LDAP_USER_FIRST_NAME', 'AUTH_LDAP_USER_LAST_NAME', 'AUTH_LDAP_USER_EMAIL']


def ldap_boolean_attribute_map(settings_dict):
    result = {}
    if settings_dict['AUTH_LDAP_USER_IS_ACTIVE']:
        result['is_active'] = settings_dict['AUTH_LDAP_USER_IS_ACTIVE']
    if settings_dict['AUTH_LDAP_USER_IS_STAFF']:
        result['is_staff'] = settings_dict['AUTH_LDAP_USER_IS_STAFF']
    if settings_dict['AUTH_LDAP_USER_IS_ACTIVE']:
        result['is_superuser'] = settings_dict['AUTH_LDAP_USER_IS_SUPERUSER']
    return result


ldap_boolean_attribute_map.required_settings = ['AUTH_LDAP_USER_IS_ACTIVE', 'AUTH_LDAP_USER_IS_STAFF',
                                                'AUTH_LDAP_USER_IS_SUPERUSER']


def ldap_group_class(settings_dict):
    if settings_dict['AUTH_LDAP_SERVER_URI']:
        try:
            cls = import_string(settings_dict['AUTH_LDAP_GROUP_NAME'])
            return cls()
        except ImportError:
            return None
    return None


ldap_group_class.required_settings = ['AUTH_LDAP_GROUP_NAME', 'AUTH_LDAP_SERVER_URI']


class InstalledApps:
    """Provide a complete `INSTALLED_APPS` list, transparently adding common third-party packages.
     Specifically handle apps required by django-allauth (one by allowed method).

    """
    default_apps = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.humanize',
        'django.contrib.sitemaps',
        'django.contrib.sites',
        ExpandIterable('DF_INSTALLED_APPS'),
        'bootstrap3',
        'djangofloor',
        'django.contrib.staticfiles',
        'django.contrib.admin',
    ]
    common_third_parties = OrderedDict([
        ('USE_DEBUG_TOOLBAR', 'debug_toolbar',),
        ('USE_PIPELINE', 'pipeline',),
        ('USE_REST_FRAMEWORK', 'rest_framework',),
        ('USE_PAM_AUTHENTICATION', 'django_pam'),
    ])
    required_settings = ['ALLAUTH_PROVIDERS', 'USE_ALL_AUTH'] + list(common_third_parties)
    allauth_providers = {'amazon', 'angellist', 'asana', 'auth0', 'baidu', 'basecamp', 'bitbucket', 'bitbucket_oauth2',
                         'bitly', 'coinbase', 'daum', 'digitalocean', 'discord', 'douban', 'draugiem', 'dropbox',
                         'dropbox_oauth2', 'edmodo', 'eveonline', 'evernote', 'facebook', 'feedly', 'fivehundredpx',
                         'flickr', 'foursquare', 'fxa', 'github', 'gitlab', 'google', 'hubic', 'instagram', 'kakao',
                         'line', 'linkedin', 'linkedin_oauth2', 'mailru', 'mailchimp', 'naver', 'odnoklassniki',
                         'openid', 'orcid', 'paypal', 'persona', 'pinterest', 'reddit', 'robinhood', 'shopify',
                         'slack', 'soundcloud', 'spotify', 'stackexchange', 'stripe', 'tumblr', 'twentythreeandme',
                         'twitch', 'twitter', 'untappd', 'vimeo', 'vk', 'weibo', 'weixin', 'windowslive', 'xing'}

    def __call__(self, settings_dict):
        apps = self.default_apps
        apps += self.process_django_allauth(settings_dict)
        apps += self.process_third_parties(settings_dict)
        return apps

    def process_third_parties(self, settings_dict):
        return [v for (k, v) in self.common_third_parties.items() if settings_dict[k]]

    def process_django_allauth(self, settings_dict):
        if not settings_dict['USE_ALL_AUTH'] and not settings_dict['ALLAUTH_PROVIDERS']:
            return []
        try:
            get_distribution('django-allauth')
        except DistributionNotFound:
            missing_package('django-allauth', ' to use OAuth2 or OpenID authentication')
            return []
        if 'django.contrib.sites' not in self.default_apps:
            settings_check_results.append(
                Error('"django.contrib.sites" app must be enabled.', obj='djangofloor.conf.settings',
                      id='djangofloor.E003'))
            return []
        result = ['allauth', 'allauth.account', 'allauth.socialaccount']
        if settings_dict['ALLAUTH_PROVIDERS']:
            result += ['allauth.socialaccount.providers.%s' % k for k in settings_dict['ALLAUTH_PROVIDERS']
                       if k in self.allauth_providers]
        return result


installed_apps = InstalledApps()


def generate_secret_key(django_ready, length=60):
    if not django_ready:
        return get_random_string(length=length)
    from django.conf import settings
    return settings.SECRET_KEY


def required_packages(settings_dict):
    def get_requirements(package_name):
        try:
            yield str(package_name)
            d = get_distribution(package_name)
            for r in d.requires():
                for required_package in get_requirements(r):
                    yield required_package
        except DistributionNotFound:
            pass

    return list(set(get_requirements(settings_dict['DF_MODULE_NAME'])))


required_packages.required_settings = ['DF_MODULE_NAME']
