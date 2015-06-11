# -*- coding: utf-8 -*-
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
from __future__ import unicode_literals
__author__ = 'flanker'


class OptionParser(object):
    def __init__(self, setting_name, option, converter=str):
        """class that maps an option in a .ini file to a setting.

        :param setting_name: the name of the setting (like "DATABASE_ENGINE")
        :type setting_name: `str`
        :param option: the section and the option in a .ini file (like "database.engine")
        :type option: `str`
        :param converter: any callable that takes a text value and returns an object. Default to `str`
        :type converter: `callable`
        """
        self.setting_name = setting_name
        self.option = option
        self.converter = converter

    def has_value(self, parser):
        section, sep, option = self.option.partition('.')
        return parser.has_option(section=section, option=option)

    def __call__(self, parser, ini_values):
        section, sep, option = self.option.partition('.')
        if not self.has_value(parser):
            return
        value = parser.get(section=section, option=option)
        ini_values[self.setting_name] = self.converter(value)


def bool_setting(value):
    return str(value).lower() in {'1', 'ok', 'yes', 'true'}


INI_MAPPING = [
    OptionParser('DATABASE_ENGINE', 'database.engine'),
    OptionParser('DATABASE_NAME', 'database.name'),
    OptionParser('DATABASE_USER', 'database.user'),
    OptionParser('DATABASE_PASSWORD', 'database.password'),
    OptionParser('DATABASE_HOST', 'database.host'),
    OptionParser('DATABASE_PORT', 'database.port'),
]
