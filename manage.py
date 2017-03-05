# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

from djangofloor.scripts import django, set_env

__author__ = 'Matthieu Gallet'

set_env(command_name='djangofloor-django')
django()
