# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Allow to define Django settings in a .ini configuration file instead of plain Python files.

Only define a dictionnary, whose keys are the settings variables, and the values must be of the form [section].[key]

For example, you can write the following configuration file::

  cat /etc/myproject/myproject.ini
  [database]
  engine = django.db.backends.sqlite3
  name = /var/myproject/database.db

It is equivalent to::

  cat /etc/myproject/myproject.py
  DATABASE_ENGINE = 'django.db.backends.sqlite3'
  DATABASE_NAME = '/var/myproject/database.db'


"""
__author__ = 'flanker'

INI_MAPPING = {
    'DATABASE_ENGINE': 'database.engine',
    'DATABASE_NAME': 'database.name',
    'DATABASE_USER': 'database.user',
    'DATABASE_PASSWORD': 'database.password',
    'DATABASE_HOST': 'database.host',
    'DATABASE_PORT': 'database.port',
}
