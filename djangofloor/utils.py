# coding=utf-8
"""Classes and functions used for the DjangoFloor settings system
==============================================================

Define several helpers classes and internal functions for the DjangoFloor settings system, allowing to merge
settings from different sources. This file must be importable while Django is not loaded yet.
"""
from __future__ import unicode_literals, absolute_import
from collections import OrderedDict
from distutils.version import LooseVersion
from django import get_version
from django.utils.six import text_type
import pkg_resources
from djangofloor.iniconf import OptionParser, MISSING_VALUE

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


class DjangoFloorConfig(object):
    """Base class for special setting values. When a setting is a :class:`djangofloor.utils.DjangoFloorConfig`,
      then the method `get_value(merger)` is called for getting the definitive value.
    """
    def __init__(self, value):
        self.value = value

    def get_value(self, merger):
        """ Return the intepreted value
        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :return:
        :rtype:
        """
        raise NotImplementedError


class Path(DjangoFloorConfig):

    def get_value(self, merger):
        raise NotImplementedError

    def __repr__(self):
        return str(self.value)


class DirectoryPath(Path):
    """Represent a directory that must be created on startup
    """
    def get_value(self, merger):
        assert isinstance(merger, SettingMerger)
        obj = merger.parse_setting(self.value)
        if not merger.read_only:
            merger.ensure_dir(obj, parent_=False)
        return obj


class FilePath(Path):
    """Represent a file, whose parent directory should be created on startup
    """

    def get_value(self, merger):
        assert isinstance(merger, SettingMerger)
        obj = merger.parse_setting(self.value)
        if not merger.read_only:
            merger.ensure_dir(obj, parent_=True)
        return obj


class SettingReference(DjangoFloorConfig):
    """Reference any setting object by its name.
    Allow to reuse a list defined in another setting file.

    in `defaults.py`:

    >>> SETTING_1 = True
    >>> SETTING_2 = SettingReference('SETTING_1')

    In `local_settings.py`

    >>> SETTING_1 = False

    In your code:

    >>> from django.conf import settings

    Then `settings.SETTING_2` is equal to `False`
    """

    def __init__(self, value, func=None):
        super(SettingReference, self).__init__(value)
        self.func = func

    def get_value(self, merger):
        assert isinstance(merger, SettingMerger)
        result = merger.get_setting_value(self.value)
        if self.func:
            result = self.func(result)
        return result


class CallableSetting(DjangoFloorConfig):
    """
    Require a function(kwargs) as argument, this function will be called with all

    >>> SETTING_1 = True
    >>> SETTING_2 = CallableSetting(lambda x: not x['SETTING_1'])

    In `local_settings.py`

    >>> SETTING_1 = False

    In your code:

    >>> from django.conf import settings

    Then `settings.SETTING_2` is equal to `True`

    You can provide a list of required settings that must be available before the call to your function.
    """

    def __init__(self, value, *required):
        super(CallableSetting, self).__init__(value)
        self.required = required

    def get_value(self, merger):
        assert isinstance(merger, SettingMerger)
        for required in self.required:
            merger.get_setting_value(required)
        return self.value(merger.settings)


class ExpandIterable(SettingReference):
    """Allow to import an existing list inside a list setting.
    in `defaults.py`:

    >>> LIST_1 = [0, ]
    >>> LIST_2 = [1, ExpandIterable('LIST_1'), 2, ]
    >>> DICT_1 = {0: 0, }
    >>> DICT_2 = {1: 1, None: ExpandIterable('DICT_1'), 2: 2, }

    In case of dict, the key is ignored when the referenced dict is expanded.
    In `local_settings.py`

    >>> LIST_1 = [3, ]
    >>> DICT_1 = {3: 3, }

    In your code:

    >>> from django.conf import settings

    Then `settings.LIST_2` is equal to `[1, 3, 2]`.
    `settings.DICT_2` is equal to `{1: 1, 2: 2, 3: 3, }`.

    """


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


def guess_version(defined_settings):
    """ Guesss the project version. Expect __version__ in `your_project/__init__.py`

    :param defined_settings: all already defined settings (dict)
    :type defined_settings: :class:`dict`
    :return:
    :rtype: :class:`str`
    """
    try:
        return import_string('%s.__version__' % defined_settings['PROJECT_NAME'])
    except ImportError:
        return 'no.version.defined'


class SettingMerger(object):
    """Load different settings modules and config files and merge them.
    """

    def __init__(self, project_name, default_settings_module_name, project_settings_module_name,
                 user_settings_path, djangofloor_config_path, djangofloor_mapping, doc_mode=False,
                 read_only=False):
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
        self.option_parsers = []
        self.doc_mode = doc_mode
        self.read_only = read_only

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
        """Ensure that the given directory exists

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
            keys = list(module.__dict__.keys())
            keys.sort()
            for setting_name in keys:
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
                if self.doc_mode:
                    for option_parser in ini_values:
                        assert isinstance(option_parser, OptionParser)
                        if option_parser.doc_default_value is not MISSING_VALUE:
                            self.ini_config_mapping[option_parser.setting_name] = option_parser.doc_default_value
                elif os.path.isfile(self.djangofloor_config_path):
                    parser = ConfigParser()
                    parser.read([self.djangofloor_config_path])
                    for option_parser in ini_values:
                        assert isinstance(option_parser, OptionParser)
                        option_parser.set_value(parser, self.ini_config_mapping)
                        self.option_parsers.append(option_parser)
            except ImportError:
                pass

    def parse_setting(self, obj):
        """Parse the object for replacing variables by their values.

        If `obj` is a string like "THIS_IS_{TEXT}", search for a setting named "TEXT" and replace {TEXT} by its value
        (say, "VALUE"). The returned object is then equal to "THIS_IS_VALUE".
        If `obj` is a list, a set, a tuple or a dict, its components are recursively parsed.
        If `obj` is a :class:`djangofloor.utils.DirectoryPath` or a :class:`djangofloor.utils.FilePath`,
        required parent directories are automatically created and the name is returned.
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
        elif isinstance(obj, DjangoFloorConfig):
            return obj.get_value(self)
        elif isinstance(obj, list) or isinstance(obj, tuple):
            result = []
            for sub_obj in obj:
                if isinstance(sub_obj, ExpandIterable):
                    result += self.get_setting_value(sub_obj.value)
                else:
                    result.append(self.parse_setting(sub_obj))
            if isinstance(obj, tuple):
                return tuple(result)
            return result
        elif isinstance(obj, set):
            result = set()
            for sub_obj in obj:
                if isinstance(sub_obj, ExpandIterable):
                    result |= self.get_setting_value(sub_obj.value)
                else:
                    result.add(self.parse_setting(sub_obj))
            return result
        elif isinstance(obj, dict):
            result = {}
            for sub_key, sub_obj in obj.items():
                if isinstance(sub_obj, ExpandIterable):
                    result.update(self.get_setting_value(sub_obj.value))
                else:
                    result[self.parse_setting(sub_key)] = (self.parse_setting(sub_obj))
            return result
        return obj

    def get_setting_value(self, setting_name):
        """import the required settings from user-specific settings, or project-specific settings, or django-floor settings.
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

    @property
    def all_ini_options(self):
        """Return an OrderedDict of list of available options in the .ini configuration file.

        * Keys correspond to the section names
        * Values are list of OptionParser, with help_str and default_values attributes set

        :return:
        :rtype:
        """
        result = OrderedDict()
        try:
            ini_values = import_string(self.djangofloor_mapping)
        except ImportError:
            return result
        all_options = {}
        defined_setting_names = set()  # to prevent duplicate OptionParser
        ini_values = [x for x in ini_values]
        ini_values.reverse()
        for option_parser in ini_values:
            assert isinstance(option_parser, OptionParser)
            all_options.setdefault(option_parser.section, [])
            if option_parser.help_str is None and self.settings.get('%s_HELP' % option_parser.setting_name):
                option_parser.help_str = text_type(self.settings['%s_HELP' % option_parser.setting_name])
            option_parser.default_value = self.settings[option_parser.setting_name]
            if option_parser.setting_name not in defined_setting_names:
                all_options[option_parser.section].append(option_parser)
            defined_setting_names.add(option_parser.setting_name)
        for options in all_options.values():
            options.sort(key=lambda x: x.key)
        section_names = [section_name for section_name in all_options]
        section_names.sort()
        for section_name in section_names:
            result[section_name] = all_options[section_name]
        return result

    def post_process(self):
        """Perform some cleaning on settings:

            * remove duplicates in `INSTALLED_APPS` (keeps only the first occurrence)

        """
        # remove duplicates in INSTALLED_APPS
        self.settings['INSTALLED_APPS'] = list(OrderedDict.fromkeys(self.settings['INSTALLED_APPS']))
        django_version = get_version()
        # remove deprecated settings
        if LooseVersion(django_version) >= LooseVersion('1.8'):
            if 'TEMPLATES' in self.settings:
                for key in 'TEMPLATE_DIRS', 'TEMPLATE_CONTEXT_PROCESSORS', 'TEMPLATE_LOADERS':
                    if key in self.settings:
                        del self.settings[key]


def walk(module_name, dirname, topdown=True):
    """
    Copy of :func:`os.walk`, please refer to its doc. The only difference is that we walk in a package_resource
    instead of a plain directory.
    :type module_name: basestring
    :param module_name: module to search in
    :type dirname: basestring
    :param dirname: base directory
    :type topdown: bool
    :param topdown: if True, perform a topdown search.
    """
    def rec_walk(root):
        """
        Recursively list subdirectories and filenames from the root.
        :param root: the root path
        :type root: basestring
        """
        dirnames = []
        filenames = []
        for name in pkg_resources.resource_listdir(module_name, root):
            fullname = root + '/' + name
            isdir = pkg_resources.resource_isdir(module_name, fullname)
            if isdir:
                dirnames.append(name)
                if not topdown:
                    rec_walk(fullname)
            else:
                filenames.append(name)
        yield root, dirnames, filenames
        if topdown:
            for name in dirnames:
                for values in rec_walk(root + '/' + name):
                    yield values
    return rec_walk(dirname)
