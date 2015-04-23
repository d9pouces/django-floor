# coding=utf-8
from __future__ import unicode_literals
from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import Group

__author__ = 'flanker'


CACHED_GROUPS = {}


class DefaultGroupRemoteUserBackend(RemoteUserBackend):

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified; only add it to the default group.
        """
        group_name = settings.DEFAULT_GROUP_NAME
        if group_name is None:
            return user
        if group_name not in CACHED_GROUPS:
            CACHED_GROUPS[group_name] = Group.objects.get_or_create(name=str(group_name))[0]
        user.groups.add(CACHED_GROUPS[group_name])
        return user


if __name__ == '__main__':
    import doctest

    doctest.testmod()