# coding=utf-8
"""Authentication backend used for HTTP authentication
===================================================

Check :class:`django.contrib.auth.backends.RemoteUserBackend` for a more detailed explanation.

Automatically add a specified group to newly-created users. The name of this default group is defined by the setting
FLOOR_DEFAULT_GROUP_NAME.
Set it to `None` if you do not want a default group for new users.

"""
from __future__ import unicode_literals
from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import Group

__author__ = 'Matthieu Gallet'


CACHED_GROUPS = {}


class DefaultGroupRemoteUserBackend(RemoteUserBackend):

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified; only add it to the default group.
        """
        group_name = settings.FLOOR_DEFAULT_GROUP_NAME
        if group_name is None:
            return user
        if group_name not in CACHED_GROUPS:
            CACHED_GROUPS[group_name] = Group.objects.get_or_create(name=str(group_name))[0]
        user.groups.add(CACHED_GROUPS[group_name])
        return user


if __name__ == '__main__':
    import doctest

    doctest.testmod()
