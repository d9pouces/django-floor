# coding=utf-8
"""
Admin module.

Only overwrite the title of the admin site (since DjangoFloor does not define any model).

"""
from __future__ import unicode_literals
from django.conf import settings

__author__ = 'Matthieu Gallet'

from django.contrib.admin import site

site.site_title = settings.FLOOR_PROJECT_NAME

if __name__ == '__main__':
    import doctest

    doctest.testmod()
