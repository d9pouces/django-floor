"""Callables settings
==================


"""

# noinspection PyUnresolvedReferences
from urllib.parse import urlparse

from django.utils.crypto import get_random_string


from djangofloor.utils import is_package_present

__author__ = 'Matthieu Gallet'

_default_engines = {'mysql': 'django.db.backends.mysql',
                    'oracle': 'django.db.backends.oracle',
                    'postgresql': 'django.db.backends.postgresql',
                    'sqlite3': 'django.db.backends.sqlite3', }


def database_engine(settings_dict):
    """Allow to use aliases for database engines, as well as the default dotted name"""
    return _default_engines.get(settings_dict['DATABASE_ENGINE'].lower(), settings_dict['DATABASE_ENGINE'])


database_engine.required_settings = ['DATABASE_ENGINE']


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


def project_name(settings_dict):
    """Transform the base module name into a nicer project name

    >>> project_name({'DF_MODULE_NAME': 'my_project'})
    'My Project'

    :param settings_dict:
    :return:
    """

    return ' '.join([x.capitalize() for x in settings_dict['DF_MODULE_NAME'].replace('_', ' ').split()])


project_name.required_settings = ['DF_MODULE_NAME']


def authentication_backends(settings_dict):
    result = []
    if settings_dict['DF_REMOTE_USER_HEADER']:
        result.append('djangofloor.backends.DefaultGroupsRemoteUserBackend')
    if settings_dict['AUTH_LDAP_SERVER_URI'] and is_package_present('django_auth_ldap'):
        result.append('django_auth_ldap.backend.LDAPBackend')
    result.append('django.contrib.auth.backends.ModelBackend')
    if settings_dict['ALLAUTH_PROVIDERS'] and settings_dict['USE_ALL_AUTH']:
        result.append('allauth.account.auth_backends.AuthenticationBackend')
    return result


authentication_backends.required_settings = ['ALLAUTH_PROVIDERS', 'DF_REMOTE_USER_HEADER', 'AUTH_LDAP_SERVER_URI',
                                             'USE_ALL_AUTH']


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
    if settings_dict['AUTH_LDAP_SERVER_URI']:
        if not is_package_present('django_auth_ldap'):
            print("Package django-auth-ldap must be installed to use LDAP authentication.")
            return None
        # noinspection PyUnresolvedReferences
        import ldap
        # noinspection PyUnresolvedReferences
        from django_auth_ldap.config import LDAPSearch
        return LDAPSearch(settings_dict['AUTH_LDAP_SEARCH_BASE'], ldap.SCOPE_SUBTREE, settings_dict['AUTH_LDAP_FILTER'])
    return None


ldap_user_search.required_settings = ['AUTH_LDAP_SEARCH_BASE', 'AUTH_LDAP_SERVER_URI', 'AUTH_LDAP_FILTER']


def allauth_installed_apps(settings_dict):
    if not settings_dict['USE_ALL_AUTH']:
        return []
    elif not is_package_present('allauth'):
        print("Package django-allauth must be installed to use OAuth2 authentication.")
        return []
    return ['allauth', 'allauth.account', 'allauth.socialaccount'] + \
           ['allauth.socialaccount.providers.%s' % k for k in settings_dict['ALLAUTH_PROVIDERS']
            if k in allauth_providers]


allauth_installed_apps.required_settings = ['ALLAUTH_PROVIDERS', 'USE_ALL_AUTH']
allauth_providers = {'amazon', 'angellist', 'asana', 'auth0', 'baidu', 'basecamp', 'bitbucket', 'bitbucket_oauth2',
                     'bitly', 'coinbase', 'daum', 'digitalocean', 'discord', 'douban', 'draugiem', 'dropbox',
                     'dropbox_oauth2', 'edmodo', 'eveonline', 'evernote', 'facebook', 'feedly', 'fivehundredpx',
                     'flickr', 'foursquare', 'fxa', 'github', 'gitlab', 'google', 'hubic', 'instagram', 'kakao',
                     'line', 'linkedin', 'linkedin_oauth2', 'mailru', 'mailchimp', 'naver', 'odnoklassniki',
                     'openid', 'orcid', 'paypal', 'persona', 'pinterest', 'reddit', 'robinhood', 'shopify',
                     'slack', 'soundcloud', 'spotify', 'stackexchange', 'stripe', 'tumblr', 'twentythreeandme',
                     'twitch', 'twitter', 'untappd', 'vimeo', 'vk', 'weibo', 'weixin', 'windowslive', 'xing'}


def generate_secret_key(django_ready, length=60):
    if not django_ready:
        return get_random_string(length=length)
    from django.conf import settings
    return settings.SECRET_KEY
