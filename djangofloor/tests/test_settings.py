# -*- coding: utf-8 -*-
from django.test import TestCase
from djangofloor.iniconf import OptionParser, bool_setting
import pkg_resources

from djangofloor.utils import SettingMerger
from djangofloor.tests import user_settings_module

__author__ = 'Matthieu Gallet'

ini_mapping = [
    OptionParser('S_INI', 's.ini', bool_setting),
    OptionParser('S_DEFAULT_INI', 's.default_ini', bool_setting),
    OptionParser('S_DEFAULT_PROJECT_INI', 's.default_project_ini', bool_setting),
    OptionParser('S_PROJECT_INI', 's.project_ini', bool_setting),
    OptionParser('S_DEFAULT_PROJECT_INI_USER', 's.default_project_ini_user', bool_setting),
    OptionParser('S_DEFAULT_INI_USER', 's.default_ini_user', bool_setting),
    OptionParser('S_PROJECT_INI_USER', 's.project_ini_user', bool_setting),
    OptionParser('S_INI_USER', 's.ini_user', bool_setting),
]


class TestSettings(TestCase):
    def test_load_settings(self):
        merger = SettingMerger('test_project', 'djangofloor.empty',
                               'djangofloor.empty', 'djangofloor.empty', None, None)
        merger.process()
        self.assertEqual({'PROJECT_NAME': 'test_project'}, merger.settings)

    def test_merge_settings(self):
        ini_filename = pkg_resources.resource_filename('djangofloor.tests', 'test_conf.ini')
        merger = SettingMerger('test_project', 'djangofloor.tests.default_settings_module',
                               'djangofloor.tests.project_settings_module', user_settings_module.__file__,
                               ini_filename, 'djangofloor.tests.test_settings.ini_mapping')
        merger.process()
        expected_dict = {'PROJECT_NAME': 'test_project', 'S_DEFAULT': True, 'S_USER': True, 'S_PROJECT': True,
                         'S_PROJECT_USER': True, 'S_DEFAULT_USER': True, 'S_DEFAULT_PROJECT_USER': True,
                         'S_DEFAULT_PROJECT': True, 'S_DEFAULT_INI': True, 'S_DEFAULT_INI_USER': True,
                         'S_DEFAULT_PROJECT_INI': True, 'S_DEFAULT_PROJECT_INI_USER': True, 'S_INI_USER': True,
                         'S_PROJECT_INI': True, 'S_PROJECT_INI_USER': True,
                         'S_BASE_LIST': [1], 'S_EXPANDED_LIST': [1, 1, 2],
                         'S_LIST': [True, True, True, True, ], 'Z_CALLABLE': True,
                         'S_DICT': {0: 1, True: True}, 'S_SET': {0, 1, True},
                         'S_TUPLE': (True, True, True, True),
                         }
        for key in expected_dict:
            self.assertTrue(key in merger.settings)
        for key in merger.settings:
            self.assertTrue(key in expected_dict)
        for key in expected_dict:
            self.assertEqual(expected_dict[key], merger.settings[key])
        self.assertEqual(expected_dict, merger.settings)

    def test_get_ini_options(self):
        ini_filename = pkg_resources.resource_filename('djangofloor.tests', 'test_conf.ini')
        merger = SettingMerger('test_project', 'djangofloor.tests.default_settings_module',
                               'djangofloor.tests.project_settings_module', user_settings_module.__file__,
                               ini_filename, 'djangofloor.tests.test_settings.ini_mapping')
        merger.process()
        print(merger.all_ini_options)
