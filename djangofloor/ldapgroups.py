# coding=utf-8
from __future__ import unicode_literals
import logging
from django.utils.six.moves.urllib.parse import urlparse
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.importlib import import_module
from django.utils.translation import ugettext as _
from django.core.cache import cache

__author__ = 'flanker'


class LdapGroupsMiddleware(object):
    group_cache = {}

    def set_connection(self):
        self.connection = self.connection_cls(self.servers, user=settings.LDAP_GROUPS_BIND_DN,
                                              password=settings.LDAP_GROUPS_BIND_PASSWORD, auto_bind=True)

    def __init__(self):
        self.servers = None
        self.connection = None
        self.scope = None
        self.exception = None
        self.connection_cls = None
        self.formatter = lambda x: x
        self.logger = logging.getLogger('django.request')

        if settings.LDAP_GROUPS_URL:
            from ldap3 import Server, Connection, SEARCH_SCOPE_WHOLE_SUBTREE, LDAPExceptionError, \
                SEARCH_SCOPE_BASE_OBJECT, SEARCH_SCOPE_SINGLE_LEVEL
            self.connection_cls = Connection
            self.servers = []
            for url in settings.LDAP_GROUPS_URL.split(','):
                url = url.strip()
                parsed_url = urlparse(url)
                port = parsed_url.port if parsed_url.port else (636 if parsed_url.scheme == 'ldaps' else 389)
                self.servers.append(Server(host=parsed_url.hostname, port=port, use_ssl=parsed_url.scheme == 'ldaps',
                                           tls=settings.LDAP_GROUPS_TLS))
            self.set_connection()
            if settings.LDAP_GROUPS_SEARCH_SCOPE.upper() == 'BASE':
                self.scope = SEARCH_SCOPE_BASE_OBJECT
            elif settings.LDAP_GROUPS_SEARCH_SCOPE.upper() == 'SINGLE_LEVEL':
                self.scope = SEARCH_SCOPE_SINGLE_LEVEL
            else:
                self.scope = SEARCH_SCOPE_WHOLE_SUBTREE
            self.exception = LDAPExceptionError
            formatter_name = settings.LDAP_GROUPS_FORMAT_GROUP_NAME
            if formatter_name is not None:
                module_name, sep, fn_name = formatter_name.rpartition('.')
                module = import_module(module_name)
                self.formatter = getattr(module, fn_name)

    # noinspection PyMethodMayBeStatic
    def get_filter(self, request):
        """ Return the LDAP filter from the request. The filter is a string, like '(samAccountName=username)'

        :param request:
        :return:
        """
        return settings.LDAP_GROUPS_SEARCH_FILTER % {'username': request.user.username, 'email': request.user.email}

    def get_groups_from_ldap(self, request, user):
        """Fetch the groups from the LDAP server, and return the list of the formatted group names.
        Cache is used here.

        :param request:
        :param user:
        :return:
        """
        username = user.username
        try_count = 0
        groups = []
        while try_count < 3:
            try:
                code = self.connection.search(search_base=settings.LDAP_GROUPS_SEARCH_BASE,
                                              search_filter=self.get_filter(request),
                                              search_scope=self.scope, paged_size=5,
                                              attributes=[settings.LDAP_GROUPS_SEARCH_GROUP_ATTRIBUTE])
                response = self.connection.response
                if not code:
                    self.logger.warning(_('Unable to perform LDAP search for %(username)s.') %
                                        {'username': username})
                elif len(response) != 1:
                    self.logger.warning(_('%(len)d LDAP results for user %(username)s.') %
                                        {'username': username})
                else:
                    groups = response[0]['attributes'][settings.LDAP_GROUPS_SEARCH_GROUP_ATTRIBUTE]
                    groups = [self.formatter(x) for x in groups]
            except self.exception:
                self.set_connection()
                try_count += 1
        if settings.LDAP_GROUPS_CACHE_GROUPS_TIME > 0:
            cache.set(self.cache_key(user), groups, settings.LDAP_GROUPS_CACHE_GROUPS_TIME)
        return groups

    # noinspection PyMethodMayBeStatic
    def cache_key(self, user):
        """ generate a cache key (string) from the username

        :param user:
        :return:
        """
        return 'ldap_groups_%s' % user.username

    def process_request(self, request):
        user = request.user
        """:type user: :class:`django.contrib.auth.models.User`"""
        if user.is_anonymous() or self.servers is None:
            return

        if settings.LDAP_GROUPS_CACHE_GROUPS_TIME > 0:
            groups = cache.get(self.cache_key(user))
            if groups is None:
                groups = self.get_groups_from_ldap(request, user)
        else:
            groups = self.get_groups_from_ldap(request, user)
        for group_name in groups:
            if group_name not in self.group_cache:
                group, created = Group.objects.get_or_create(name=group_name)
                self.group_cache[group_name] = group
            else:
                group = self.group_cache[group_name]
            user.groups.add(group)


if __name__ == '__main__':
    import doctest

    doctest.testmod()