# -*- coding: utf-8 -*-
"""
Allow to define Django settings in a .ini configuration file instead of plain Python files.

Only define a dictionnary, whose keys are the settings variables, and the values must be of the form [section].[key]

For example, you can write the following configuration file:

.. code-block:: bash

  cat /etc/myproject/myproject.ini
  [database]
  engine = django.db.backends.sqlite3
  name = /var/myproject/database.db

It is equivalent to:

.. code-block:: bash

  cat /etc/myproject/myproject.py
  DATABASE_ENGINE = 'django.db.backends.sqlite3'
  DATABASE_NAME = '/var/myproject/database.db'


"""
from __future__ import unicode_literals
import os
from django.utils.six import text_type

__author__ = 'Matthieu Gallet'


def bool_setting(value):
    return text_type(value).lower() in {'1', 'ok', 'yes', 'true', 'on'}


def str_or_none(text):
    return text or None


def str_or_blank(value):
    return '' if value is None else text_type(value)


def guess_relative_path(value):
    if value is None:
        return ''
    elif os.path.exists(value):
        value = os.path.abspath(value)
        return value.replace(os.path.abspath(os.getcwd()), '.')
    return value


def strip_split(value):
    """Split the value on "," and strip spaces of the result. Remove empty values.

    >>> strip_split('keyword1, keyword2 ,,keyword3')
    ["keyword1", "keyword2", "keyword3"]

    >>> strip_split('')
    []

    >>> strip_split(None)
    []

    :param value:
    :type value:
    :return:
    :rtype:
    """
    if value:
        return [x.strip() for x in value.split(',') if x.strip()]
    return []


MISSING_VALUE = [[]]


class OptionParser(object):
    def __init__(self, setting_name, option, converter=str, to_str=str_or_blank, help_str=None,
                 doc_default_value=MISSING_VALUE):
        """class that maps an option in a .ini file to a setting.

        :param setting_name: the name of the setting (like "DATABASE_ENGINE")
        :type setting_name: `str`
        :param option: the section and the option in a .ini file (like "database.engine")
        :type option: `str`
        :param converter: any callable that takes a text value and returns an object. Default to `str_or_none`
        :type converter: `callable`
        :param to_str: any callable that takes the Python value and that converts it to str
            only used for writing sample config file. Default to `str`
        :type to_str: `callable`
        :param help_str: any text that can serve has help in documentation.
            If None, then `settings.%s_HELP % setting_name` will be used as help text.
        :type help_str: `str`
        :param doc_default_value: the value that will be used in documentation.
        The current setting value will be used if left to `None`.
        :type doc_default_value: `object`
        """
        self.setting_name = setting_name
        self.option = option
        self.converter = converter
        self.to_str = to_str
        self.help_str = help_str
        self.default_value = None
        self.doc_default_value = doc_default_value

    @property
    def section(self):
        return self.option.partition('.')[0]

    @property
    def key(self):
        return self.option.partition('.')[2]

    def has_value(self, parser):
        section, sep, option = self.option.partition('.')
        return parser.has_option(section=section, option=option)

    def str_value(self):
        return self.to_str(self.default_value)

    @property
    def __name__(self):
        return self.option

    def __str__(self):
        return self.option

    def set_value(self, parser, ini_values):
        """ Given a .ini config file and a Python dict, read its value and set the dict with it

        :param parser: ConfigParser that read the .ini config file
        :type parser: :class:`configparser.ConfigParser`
        :param ini_values: a dict to fill
        :type ini_values: :class:`dict`
        :return: `True` if this value is defined in the configuration file, `False` otherwise
        :rtype: :class:`bool`
        """
        section, sep, option = self.option.partition('.')
        if not self.has_value(parser):
            return False
        value = parser.get(section=section, option=option)
        ini_values[self.setting_name] = self.converter(value)
        return True


INI_MAPPING = [
    OptionParser('ADMIN_EMAIL', 'global.admin_email', doc_default_value='admin@{SERVER_NAME}'),
    OptionParser('BIND_ADDRESS', 'global.bind_address'),
    OptionParser('DATABASE_ENGINE', 'database.engine', doc_default_value='django.db.backends.postgresql_psycopg2'),
    OptionParser('DATABASE_NAME', 'database.name', doc_default_value='{PROJECT_NAME}'),
    OptionParser('DATABASE_USER', 'database.user', doc_default_value='{PROJECT_NAME}'),
    OptionParser('DATABASE_PASSWORD', 'database.password', doc_default_value='5trongp4ssw0rd'),
    OptionParser('DATABASE_HOST', 'database.host', doc_default_value='localhost'),
    OptionParser('DATABASE_PORT', 'database.port', doc_default_value='5432'),
    OptionParser('DEBUG', 'global.debug', converter=bool_setting),
    OptionParser('FLOOR_DEFAULT_GROUP_NAME', 'global.default_group'),
    OptionParser('LANGUAGE_CODE', 'global.language_code'),
    OptionParser('LOCAL_PATH', 'global.data_path', to_str=guess_relative_path, doc_default_value='/var/{PROJECT_NAME}'),
    OptionParser('PROTOCOL', 'global.protocol', doc_default_value='http'),
    OptionParser('SECRET_KEY', 'global.secret_key'),
    OptionParser('SERVER_NAME', 'global.server_name', doc_default_value='{PROJECT_NAME}.example.org'),
    OptionParser('TIME_ZONE', 'global.time_zone'),
    OptionParser('FLOOR_AUTHENTICATION_HEADER', 'global.remote_user_header', converter=str_or_none),
    OptionParser('FLOOR_EXTRA_APPS', 'global.extra_apps', converter=strip_split, to_str=lambda x: ','.join(x),
                 help_str='List of extra installed Django apps (separated by commas).'),
    OptionParser('SENTRY_DSN_URL', 'sentry.dsn_url'),
]
