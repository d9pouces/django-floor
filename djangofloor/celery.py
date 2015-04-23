# coding=utf-8
from __future__ import unicode_literals, absolute_import
from django.conf import settings
from djangofloor.scripts import set_env

__author__ = 'flanker'
from celery import Celery

project_name = set_env()
app = Celery(project_name)
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == '__main__':
    import doctest

    doctest.testmod()