# -*- coding: utf-8 -*-
from djangofloor.utils import SettingReference, CallableSetting, ExpandIterable

S_DEFAULT = True
S_DEFAULT_PROJECT = False
S_DEFAULT_USER = False
S_DEFAULT_PROJECT_USER = False

S_DEFAULT_INI = False
S_DEFAULT_PROJECT_INI = False
S_DEFAULT_INI_USER = False
S_DEFAULT_PROJECT_INI_USER = False

S_LIST = [SettingReference('S_DEFAULT'),
          SettingReference('S_DEFAULT_PROJECT'),
          SettingReference('S_DEFAULT_USER'),
          SettingReference('S_DEFAULT_PROJECT_USER'), ]
S_DICT = {0: 1, SettingReference('S_DEFAULT'): SettingReference('S_DEFAULT_PROJECT'), }
S_SET = {0, 1, SettingReference('S_DEFAULT'), SettingReference('S_DEFAULT_PROJECT'), }
S_BASE_LIST = [0, ]
S_EXPANDED_LIST = [1, ExpandIterable('S_BASE_LIST'), 2, ]
Z_CALLABLE = CallableSetting(lambda kwargs: kwargs['S_DEFAULT_USER'])
S_TUPLE = (SettingReference('S_DEFAULT'),
           SettingReference('S_DEFAULT_PROJECT'),
           SettingReference('S_DEFAULT_USER'),
           SettingReference('S_DEFAULT_PROJECT_USER'),)
