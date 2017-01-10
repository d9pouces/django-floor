# coding=utf-8
from __future__ import unicode_literals
from demo.views import test
from django.conf.urls import url

__author__ = 'Matthieu Gallet'

urls = [
    url(r'^test.html$', test),
]
