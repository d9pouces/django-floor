# coding=utf-8
from __future__ import unicode_literals
from django.conf import settings

__author__ = 'flanker'

from django.contrib.admin import site

site.site_title = settings.FLOOR_PROJECT_NAME

if __name__ == '__main__':
    import doctest

    doctest.testmod()