"""Miscelaneous backends
=====================

The provided authentication backend  for :mod:`django.contrib.auth` only overrides the default Django one
for remote users (users that are authenticated using a HTTP header like HTTP_REMOTE_USER).
It automatically add several groups to newly-created users.
Setting `DF_DEFAULT_GROUPS` is expected to be a list of group names.


"""

import logging

from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import Group
from django.utils.functional import cached_property

try:
    # noinspection PyPackageRequirements
    from pipeline.storage import PipelineCachedStorage
except ImportError:
    PipelineCachedStorage = None
__author__ = 'Matthieu Gallet'
logger = logging.getLogger('django.requests')

_CACHED_GROUPS = {}


class DefaultGroupsRemoteUserBackend(RemoteUserBackend):
    """Add groups to new users.
    Based on :class:`django.contrib.auth.backends.RemoteUserBackend`.
    Only overrides the `configure_user` method to add the required groups.

     """

    @property
    def create_unknown_user(self):
        return settings.DF_ALLOW_USER_CREATION

    @cached_property
    def ldap_backend(self):
        # noinspection PyUnresolvedReferences
        from django_auth_ldap.backend import LDAPBackend
        return LDAPBackend()

    def authenticate(self, *args, **kwargs):
        remote_user = kwargs.get('remote_user')
        if remote_user and settings.AUTH_LDAP_SERVER_URI and settings.AUTH_LDAP_ALWAYS_UPDATE_USER:
            user = self.ldap_backend.populate_user(remote_user)
            if user:
                return user
        return super().authenticate(*args, remote_user)

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified; only add it to the default group.
        """
        for group_name in settings.DF_DEFAULT_GROUPS:
            if group_name not in _CACHED_GROUPS:
                _CACHED_GROUPS[group_name] = Group.objects.get_or_create(name=str(group_name))[0]
            user.groups.add(_CACHED_GROUPS[group_name])
        return user


if PipelineCachedStorage:

    # noinspection PyClassHasNoInit
    class DjangofloorPipelineCachedStorage(PipelineCachedStorage):
        def hashed_name(self, name, content=None, filename=None):
            try:
                return super(DjangofloorPipelineCachedStorage, self).hashed_name(name, content=content)
            except ValueError as e:
                raise ValueError("%s. Did you run the command 'collectstatic'?" % e.args[0])
