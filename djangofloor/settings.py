#coding=utf-8
""" Django settings for DjangoFloor.

Settings come from 3 modules:

  * djangofloor.defaults
  * project-specific settings, defined in the environment variable DJANGOFLOOR_PROJECT_SETTINGS
  * user-specific settings, defined in the environment variable DJANGOFLOOR_USER_SETTINGS

djangofloor.defaults settings are overridden by project-specific settings, which are of course overridden by
    user-specific settings.

Only variables in uppercase (like INSTALLED_APPS) are taken into account.
Only variables defined in djangofloor.defaults or in project-specific settings are taken into account.

If VARIABLE is uppercase and if VARIABLE_help exists, then VARIABLE is shown with command `manage.py config`.

"""
import os
import string
import sys
from django.utils.importlib import import_module
from djangofloor import defaults as floor_settings

__author__ = 'flanker'

PROJECT_SETTINGS_PATH = os.environ.get('DJANGOFLOOR_PROJECT_SETTINGS', '')
USER_SETTINGS_PATH = os.environ.get('DJANGOFLOOR_USER_SETTINGS', '')
PROJECT_NAME = os.environ.get('DJANGOFLOOR_PROJECT_NAME', 'djangofloor')


def import_file(filepath):
    """import the Python source file as a Python module.

    :param filepath:
    :return:
    """
    if filepath and os.path.isfile(filepath):
        dirname = os.path.dirname(filepath)
        if dirname not in sys.path:
            sys.path.insert(0, dirname)
        conf_module = os.path.splitext(filepath)[0]
        module = import_module(conf_module)
    else:
        import djangofloor.empty
        module = djangofloor.empty
    return module

project_settings = import_file(PROJECT_SETTINGS_PATH)
user_settings = import_file(USER_SETTINGS_PATH)


__settings = globals()
__formatter = string.Formatter()


def __parse_setting(obj):
    if isinstance(obj, str):
        values = {'PROJECT_NAME': PROJECT_NAME}
        for (literal_text, field_name, format_spec, conversion) in __formatter.parse(obj):
            if field_name is not None:
                values[field_name] = __setting_value(field_name)
        if values:
            return __formatter.format(obj, **values)
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [__parse_setting(x) for x in obj]
    elif isinstance(obj, dict):
        return dict([(__parse_setting(x), __parse_setting(y)) for (x, y) in obj.items()])
    return obj


def __setting_value(setting_name_):
    """ import setting_name_ from user-specific settings, or project-specific settings, or django-floor settings.
    Also add it to globals(), so this function is idempotent.

    :param setting_name_: name of the setting to import
    :return: the imported setting :)
    """
    if setting_name_ in __settings:
        return __settings[setting_name_]
    if hasattr(user_settings, setting_name_):
        value = getattr(user_settings, setting_name_)
    elif hasattr(project_settings, setting_name_):
        value = getattr(project_settings, setting_name_)
    else:
        value = getattr(floor_settings, setting_name_)
    __settings[setting_name_] = __parse_setting(value)
    return __settings[setting_name_]


def __ensure_dir(path_, parent_=True):
    dirname_ = os.path.dirname(path_) if parent_ else path_
    if not os.path.isdir(dirname_):
        os.makedirs(dirname_)


for setting_name in floor_settings.__dict__:
    if setting_name == setting_name.upper():
        __setting_value(setting_name)

for setting_name in project_settings.__dict__:
    if setting_name == setting_name.upper():
        __setting_value(setting_name)

for setting_name in user_settings.__dict__:
    if setting_name == setting_name.upper():
        __setting_value(setting_name)


# noinspection PyUnresolvedReferences,PyUnboundLocalVariable
INSTALLED_APPS += OTHER_ALLAUTH
# noinspection PyUnresolvedReferences
INSTALLED_APPS += FLOOR_INSTALLED_APPS

# noinspection PyUnresolvedReferences
for db_dict in DATABASES.values():
    if db_dict['ENGINE'] == 'django.db.backends.sqlite3':
        __ensure_dir(db_dict['NAME'])
# noinspection PyUnresolvedReferences
for db_dict in CACHES.values():
    if db_dict['BACKEND'] == 'django.core.cache.backends.filebased.FileBasedCache':
        __ensure_dir(db_dict['LOCATION'], False)
# noinspection PyUnresolvedReferences
for db_dict in LOGGING['handlers'].values():
    if 'RotatingFileHandler' in db_dict['class']:
        __ensure_dir(db_dict['filename'])
# noinspection PyUnresolvedReferences
__ensure_dir(MEDIA_ROOT, False)
# noinspection PyUnresolvedReferences
__ensure_dir(STATIC_ROOT, False)
# noinspection PyUnresolvedReferences
for path in (PID_FILE, GUNICORN_ERROR_LOG_FILE, GUNICORN_ACCESS_LOG_FILE, REVERSE_PROXY_ERROR_LOG_FILE,
             REVERSE_PROXY_ACCESS_LOG_FILE, ):
    __ensure_dir(path)


if __name__ == '__main__':
    import doctest

    doctest.testmod()