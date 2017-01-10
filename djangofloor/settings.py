# coding=utf-8
""" Django settings for DjangoFloor.

Settings come from 3 modules and one .ini file:

    * djangofloor.defaults
    * project-specific settings, defined in the environment variable DJANGOFLOOR_PROJECT_SETTINGS
    * user-specific settings, defined in the environment variable DJANGOFLOOR_USER_SETTINGS
    * .ini file, whose path is defined in the environment variable DJANGOFLOOR_INI_SETTINGS


djangofloor.defaults settings are overridden by project-specific settings, which are of course overridden by
    user-specific settings.

Only variables in uppercase (like INSTALLED_APPS) are taken into account.
Only variables defined in djangofloor.defaults or in project-specific settings are taken into account.

If VARIABLE is uppercase and if VARIABLE_HELP exists, then VARIABLE is shown with command `manage.py config`.

"""
from __future__ import unicode_literals
import os

from djangofloor.utils import SettingMerger

__author__ = 'Matthieu Gallet'

PROJECT_SETTINGS_MODULE_NAME = os.environ.get('DJANGOFLOOR_PROJECT_DEFAULTS', '')
USER_SETTINGS_PATH = os.environ.get('DJANGOFLOOR_PYTHON_SETTINGS', '')
DJANGOFLOOR_CONFIG_PATH = os.environ.get('DJANGOFLOOR_INI_SETTINGS', '')
DJANGOFLOOR_MAPPING = os.environ.get('DJANGOFLOOR_MAPPING', '')
PROJECT_NAME = os.environ.get('DJANGOFLOOR_PROJECT_NAME', 'djangofloor')


merger = SettingMerger(PROJECT_NAME, 'djangofloor.defaults', PROJECT_SETTINGS_MODULE_NAME, USER_SETTINGS_PATH,
                       DJANGOFLOOR_CONFIG_PATH, DJANGOFLOOR_MAPPING)
merger.process()
merger.post_process()

__settings = globals()
__settings_origin = merger.settings_origin
__settings_original_value = merger.settings_original_value
__settings.update(merger.settings)
