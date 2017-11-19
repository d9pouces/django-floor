"""Callables settings
==================

Dynamically build smart settings related to the authentication system,
taking into account other settings or installed packages.
"""


import grp
import os
# noinspection PyMethodMayBeStatic,PyUnusedLocal
import pwd

from django.core.checks import Error
from django.utils.module_loading import import_string
from pkg_resources import get_distribution, DistributionNotFound

from djangofloor.checks import missing_package, settings_check_results


# noinspection PyMethodMayBeStatic
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
            settings_check_results.append(missing_package('django-radius', ' to use RADIUS authentication'))
            return []
        return ['radiusauth.backends.RADIUSBackend']

    def process_django_ldap(self, settings_dict):
        if not settings_dict['AUTH_LDAP_SERVER_URI']:
            return []
        try:
            get_distribution('django-auth-ldap')
        except DistributionNotFound:
            settings_check_results.append(missing_package('django-auth-ldap', ' to use LDAP authentication'))
            return []
        return ['django_auth_ldap.backend.LDAPBackend']

    def process_pam(self, settings_dict):
        if not settings_dict['USE_PAM_AUTHENTICATION']:
            return []
        try:
            get_distribution('django_pam')
        except DistributionNotFound:
            settings_check_results.append(missing_package('django-pam', ' to use PAM authentication'))
            return []
        # check if the current user is in the shadow group
        username = pwd.getpwuid(os.getuid()).pw_name
        if not any(x.gr_name == 'shadow' and username in x.gr_mem for x in grp.getgrall()):
            settings_check_results.append(Error('The user "%s" must belong to the "shadow" group to use PAM '
                                                'authentication.' % username, obj='configuration'))
            return []
        return ['django_pam.auth.backends.PAMBackend']

    def __repr__(self):
        return '%s.%s' % (self.__module__, 'authentication_backends')


authentication_backends = AuthenticationBackends()


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
