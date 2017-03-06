# -*- coding: utf-8 -*-
"""Miscelaneous backends
=====================

The provided authentication backend  for :mod:`django.contrib.auth` only overrides the default Django one for remote users
(users that are authenticated using a HTTP header like HTTP_REMOTE_USER).
It automatically add several groups to newly-created users.
Setting `DF_DEFAULT_GROUPS` is expected to be a list of group names.


"""
from __future__ import unicode_literals, print_function, absolute_import

import logging
from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import Group
from django.utils.encoding import force_text
# noinspection PyUnresolvedReferences
from django.utils.six.moves.urllib.parse import unquote, urlsplit

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

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified; only add it to the default group.
        """
        for group_name in settings.DF_DEFAULT_GROUPS:
            if group_name not in _CACHED_GROUPS:
                _CACHED_GROUPS[group_name] = Group.objects.get_or_create(name=force_text(group_name))[0]
            user.groups.add(_CACHED_GROUPS[group_name])
        return user

if PipelineCachedStorage:
    # noinspection PyClassHasNoInit
    class DjangofloorPipelineCachedStorage(PipelineCachedStorage):
        def hashed_name(self, name, content=None):
            parsed_name = urlsplit(unquote(name))
            clean_name = parsed_name.path.strip()
            if content is None and not self.exists(clean_name):
                raise ValueError("The file '%s' could not be found with %r. Did you run the command 'collectstatic'?" %
                                 (clean_name, self))
            return super(DjangofloorPipelineCachedStorage, self).hashed_name(name, content=content)
