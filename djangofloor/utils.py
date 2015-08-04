# coding=utf-8
from __future__ import unicode_literals, absolute_import
try:
    # noinspection PyCompatibility
    from configparser import ConfigParser
except ImportError:
    # noinspection PyUnresolvedReferences,PyCompatibility
    from ConfigParser import ConfigParser
import os
import string
import sys
from django.utils import six
from django.utils.module_loading import import_string


__author__ = 'Matthieu Gallet'


class Path(object):
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return str(self.path)


class DirectoryPath(Path):
    pass


class FilePath(Path):
    pass


def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in range(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level package")
    return "%s.%s" % (package[:dot], name)


if six.PY3:
    # noinspection PyUnresolvedReferences
    from importlib import import_module
else:
    def import_module(name, package=None):
        """Import a module.

        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.

        """
        if name.startswith('.'):
            if not package:
                raise TypeError("relative imports require the 'package' argument")
            level = 0
            for character in name:
                if character != '.':
                    break
                level += 1
            name = _resolve_name(name[level:], package, level)
        __import__(name)
        return sys.modules[name]


class SettingMerger(object):

    def __init__(self, project_name,
                 default_settings_module_name,
                 project_settings_module_name,
                 user_settings_path,
                 djangofloor_config_path, djangofloor_mapping):
        self.project_name = project_name
        self.project_settings_module_name = project_settings_module_name
        self.default_settings_module_name = default_settings_module_name
        self.user_settings_path = user_settings_path
        self.djangofloor_config_path = djangofloor_config_path
        self.djangofloor_mapping = djangofloor_mapping
        self.__formatter = string.Formatter()

        self.settings = {'PROJECT_NAME': project_name}
        self.settings_origin = {}
        self.settings_original_value = {}

        self.default_settings_module = None
        self.project_settings_module = None
        self.user_settings_module = None
        self.ini_config_mapping = None

    @staticmethod
    def import_file(filepath):
        """import the Python source file as a Python module.

        :param filepath: absolute path of the Python module
        :type filepath: :class:`str`
        :return:
        """
        if filepath and os.path.isfile(filepath):
            dirname = os.path.dirname(filepath)
            if dirname not in sys.path:
                sys.path.insert(0, dirname)
            conf_module = os.path.splitext(os.path.basename(filepath))[0]
            module_ = import_module(conf_module)
        elif filepath:
            import djangofloor.empty
            module_ = djangofloor.empty
        else:
            import djangofloor.empty
            module_ = djangofloor.empty
        return module_

    @staticmethod
    def ensure_dir(path_, parent_=True):
        """ ensure that the given directory exists
        :param path_: the path to check
        :param parent_: only ensure the existence of the parent directory
        """
        dirname_ = os.path.dirname(path_) if parent_ else path_
        if not os.path.isdir(dirname_):
            try:
                os.makedirs(dirname_)
                print('Directory %s created.' % dirname_)
            except IOError:
                print('Unable to create directory %s.' % dirname_)

    def load_settings(self):
        for module in self.default_settings_module, self.project_settings_module, self.user_settings_module:
            for setting_name in module.__dict__:
                if setting_name == setting_name.upper():
                    self.get_setting_value(setting_name)

    def load_settings_providers(self):
        """ Load the different sources of settings and set the corresponding attributes
        :return: `None`
        :rtype: :class:`NoneType`
        """
        self.default_settings_module = import_module(self.default_settings_module_name)
        # default settings for the project
        if self.project_settings_module_name:
            self.project_settings_module = import_module(self.project_settings_module_name)
        else:
            import djangofloor.empty
            self.project_settings_module = djangofloor.empty

        # settings for the installation
        self.user_settings_module = self.import_file(self.user_settings_path)

        # load settings from the .ini configuration file
        self.ini_config_mapping = {}
        if self.djangofloor_mapping:
            try:
                ini_values = import_string(self.djangofloor_mapping)
                if os.path.isfile(self.djangofloor_config_path):
                    parser = ConfigParser()
                    parser.read([self.djangofloor_config_path])
                    for option_parser in ini_values:
                        option_parser(parser, self.ini_config_mapping)
            except ImportError:
                pass

    def parse_setting(self, obj):
        """Parse the object for replacing variables by their values.
        If `obj` is a string like "THIS_IS_{TEXT}", search for a setting named "TEXT" and replace {TEXT} by its value (say, "VALUE").
        The returned object is then equal to "THIS_IS_VALUE".
        If `obj` is a list, a set, a tuple or a dict, their components are recursively parsed.
        If `obj` is a DirectoryPath or a FilePath, required parent directories are automatically created and the name is returned.
        Otherwise, `obj` is returned as-is.


        :param obj: object to analyze
        :return: the parsed setting
        """
        if isinstance(obj, six.string_types):
            values = {'PROJECT_NAME': self.project_name}
            for (literal_text, field_name, format_spec, conversion) in self.__formatter.parse(obj):
                if field_name is not None:
                    values[field_name] = self.get_setting_value(field_name)
            if values:
                return self.__formatter.format(obj, **values)
        elif isinstance(obj, DirectoryPath):
            obj = self.parse_setting(obj.path)
            self.ensure_dir(obj, parent_=False)
            return obj
        elif isinstance(obj, FilePath):
            obj = self.parse_setting(obj.path)
            self.ensure_dir(obj, parent_=True)
            return obj
        elif isinstance(obj, list) or isinstance(obj, tuple):
            return [self.parse_setting(x_) for x_ in obj]
        elif isinstance(obj, set):
            return {self.parse_setting(x_) for x_ in obj}
        elif isinstance(obj, dict):
            return dict([(self.parse_setting(x_), self.parse_setting(y_)) for (x_, y_) in obj.items()])
        return obj

    def get_setting_value(self, setting_name):
        """ import setting_name_ from user-specific settings, or project-specific settings, or django-floor settings.
        Also add it to globals(), so this function is idempotent.

        :param setting_name: name of the setting to import
        :return: the imported setting :)
        """
        if setting_name in self.settings:
            return self.settings[setting_name]
        if hasattr(self.user_settings_module, setting_name):
            value = getattr(self.user_settings_module, setting_name)
            self.settings_origin[setting_name] = self.user_settings_path
        elif setting_name in self.ini_config_mapping:
            value = self.ini_config_mapping[setting_name]
            self.settings_origin[setting_name] = self.djangofloor_config_path
        elif hasattr(self.project_settings_module, setting_name):
            value = getattr(self.project_settings_module, setting_name)
            self.settings_origin[setting_name] = self.project_settings_module_name
        else:
            value = getattr(self.default_settings_module, setting_name)
            self.settings_origin[setting_name] = 'djangofloor.defaults'
        self.settings_original_value[setting_name] = value
        self.settings[setting_name] = self.parse_setting(value)
        return self.settings[setting_name]

    def process(self):
        self.load_settings_providers()
        self.load_settings()
