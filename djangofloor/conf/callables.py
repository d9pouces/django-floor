# -*- coding: utf-8 -*-
"""Callables settings
==================


"""
from __future__ import unicode_literals, print_function, absolute_import
# noinspection PyUnresolvedReferences
from django.utils.six.moves.urllib.parse import urlparse

from djangofloor.utils import is_package_present

__author__ = 'Matthieu Gallet'

_default_engines = {'mysql': 'django.db.backends.mysql',
                    'oracle': 'django.db.backends.oracle',
                    'postgresql': 'django.db.backends.postgresql_psycopg2',
                    'sqlite3': 'django.db.backends.sqlite3', }


def database_engine(settings_dict):
    """Allow to use aliases for database engines, as well as the default dotted name"""
    return _default_engines.get(settings_dict['DATABASE_ENGINE'].lower(), settings_dict['DATABASE_ENGINE'])
database_engine.required_settings = ['DATABASE_ENGINE']


def url_parse_server_name(settings_dict):
    """"""
    return urlparse(settings_dict['SERVER_BASE_URL']).hostname
url_parse_server_name.required_settings = ['SERVER_BASE_URL']


def url_parse_server_port(settings_dict):
    """"""
    return urlparse(settings_dict['SERVER_BASE_URL']).port or (settings_dict['USE_SSL'] and 443) or 80
url_parse_server_port.required_settings = ['SERVER_BASE_URL', 'USE_SSL']


def url_parse_server_protocol(settings_dict):
    """"""
    return 'https' if settings_dict['USE_SSL'] else 'http'
url_parse_server_protocol.required_settings = ['USE_SSL']


def url_parse_prefix(settings_dict):
    p = urlparse(settings_dict['SERVER_BASE_URL']).path
    if not p.endswith('/'):
        p += '/'
    return p
url_parse_prefix.required_settings = ['SERVER_BASE_URL']


def url_parse_ssl(settings_dict):
    return urlparse(settings_dict['SERVER_BASE_URL']).scheme == 'https'
url_parse_ssl.required_settings = ['SERVER_BASE_URL']


def project_name(settings_dict):
    return settings_dict['DF_MODULE_NAME'].capitalize()
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
    return ['allauth', 'allauth.account', 'allauth.socialaccount'] +\
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
