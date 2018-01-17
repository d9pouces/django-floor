"""Providers of Django settings
============================

Settings that are merged to provide the final Django settings come from different kinds of sources
(Python modules or files, ini files, …).

"""
import hashlib
import os
import sys
from collections import OrderedDict

from io import StringIO

from djangofloor.conf.fields import ConfigField

try:
    # noinspection PyUnresolvedReferences,PyCompatibility
    from configparser import ConfigParser
except ImportError:
    # noinspection PyUnresolvedReferences,PyCompatibility
    from ConfigParser import ConfigParser

__author__ = 'Matthieu Gallet'


class ConfigProvider:
    """Base class of config provider."""
    name = None

    def has_value(self, config_field):
        """Return True if a config_field is present in the file"""
        raise NotImplementedError

    def set_value(self, config_field, include_doc=False):
        """Get the value of the config_field and set its internal value"""
        raise NotImplementedError

    def get_value(self, config_field):
        """Get the internal value if the config field is present in its internal values.
Otherwise returns the current value of the config field."""
        raise NotImplementedError

    def get_extra_settings(self):
        """Return all settings internally defined.


    :return: an iterable of (setting_name, value)"""
        raise NotImplementedError

    def is_valid(self):
        """Return `True` if the provider is valid (for example, the corresponding file is missing)."""
        raise NotImplementedError

    def to_str(self):
        """Convert all its internal values to a string"""
        raise NotImplementedError


class IniConfigProvider(ConfigProvider):
    """Read a config file using the .ini syntax."""
    name = '.ini file'

    def __init__(self, config_file=None):
        self.parser = ConfigParser()
        self.config_file = config_file
        if config_file:
            self.parser.read([config_file])

    def __str__(self):
        return self.config_file

    @staticmethod
    def __get_info(config_field: ConfigField):
        section, sep, option = config_field.name.partition('.')
        return section, option

    def set_value(self, config_field: ConfigField, include_doc: bool=False):
        """update the internal config file """
        section, option = self.__get_info(config_field)
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        to_str = config_field.to_str(config_field.value)
        if include_doc and config_field.__doc__:
            for line in config_field.__doc__.splitlines():
                to_str += ' \n# %s' % line
        self.parser.set(section, option, to_str)

    def get_value(self, config_field: ConfigField):
        """get option from the config file"""
        section, option = self.__get_info(config_field)
        if self.parser.has_option(section=section, option=option):
            str_value = self.parser.get(section=section, option=option)
            return config_field.from_str(str_value)
        return config_field.value

    def has_value(self, config_field: ConfigField):
        """return `True` if the option is defined in the config file """
        section, option = self.__get_info(config_field)
        return self.parser.has_option(section=section, option=option)

    def get_extra_settings(self):
        """No extra setting can be defined in a config file"""
        return []

    def is_valid(self):
        """Return `True` if the config file exists """
        return os.path.isfile(self.config_file)

    def to_str(self):
        """Display the config file """
        fd = StringIO()
        self.parser.write(fd)
        return fd.getvalue()


class PythonModuleProvider(ConfigProvider):
    """Load a Python module from its dotted name"""
    name = 'Python module'

    def __init__(self, module_name=None):
        self.module_name = module_name
        self.module = None
        self.values = OrderedDict()
        if module_name is not None:
            from djangofloor.utils import import_module
            try:
                self.module = import_module(module_name, package=None)
            except ImportError:
                pass

    def __str__(self):
        return self.module_name

    def set_value(self, config_field, include_doc=False):
        """Set the value of the config field in an internal dict"""
        self.values[config_field.setting_name] = config_field.value

    def get_value(self, config_field):
        """Get the value of a variable defined in the Python module."""
        if self.module is None or not hasattr(self.module, config_field.name):
            return config_field.value
        return getattr(self.module, config_field.name)

    def has_value(self, config_field):
        """`True` if the corresponding variable is defined in the module"""
        return self.module is not None and hasattr(self.module, config_field.name)

    def get_extra_settings(self):
        """Return all values that look like a Django setting (i.e. uppercase variables)"""
        if self.module is not None:
            for key, value in self.module.__dict__.items():
                if key.upper() != key or key.endswith('_HELP') or key == '_':
                    continue
                yield key, value

    def is_valid(self):
        """Return `True` if the module can be imported"""
        return bool(self.module)

    def to_str(self):
        """Display values as if set in a Python module"""
        fd = StringIO()
        fd.write('# -*- coding: utf-8 -*-\n')
        for k, v in self.values.items():
            fd.write('%s = %r\n' % (k, v))
        return fd.getvalue()


class PythonFileProvider(PythonModuleProvider):
    """Load a Python module from the filename"""
    name = 'Python file'

    def __init__(self, module_filename):
        self.module_filename = module_filename
        super(PythonFileProvider, self).__init__()
        if not os.path.isfile(module_filename):
            return
        version = tuple(sys.version_info[0:1])
        md5 = hashlib.md5(module_filename.encode('utf-8')).hexdigest()
        module_name = "djangofloor.__private" + md5
        if version >= (3, 5):
            import importlib.util
            spec = importlib.util.spec_from_file_location(module_name, module_filename)
            module_ = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module_)
        elif version >= (3, 2):
            # noinspection PyCompatibility
            from importlib.machinery import SourceFileLoader
            module_ = SourceFileLoader(module_name, module_filename).load_module()
        else:
            # noinspection PyDeprecation
            import imp
            # noinspection PyDeprecation
            module_ = imp.load_source(module_name, module_filename)
        self.module = module_

    def __str__(self):
        return self.module_filename


class DictProvider(ConfigProvider):
    """Use a plain Python dict as a setting provider """
    name = 'dict'

    def __init__(self, values):
        self.values = values

    def get_extra_settings(self):
        """Return all uppercase keys of the internal dict as valid filenames"""
        for k, v in self.values.items():
            if k == k.upper():
                yield k, v

    def set_value(self, config_field, include_doc=False):
        """modify the internal dict for storing the value """
        self.values[config_field.setting_name] = config_field.value

    def get_value(self, config_field):
        """get a value from the internal dict if present """
        return self.values.get(config_field.setting_name, config_field.value)

    def has_value(self, config_field):
        """check if the value is present in the internal dict """
        return config_field.setting_name in self.values

    def __str__(self):
        return '%r' % self.values

    def is_valid(self):
        """always `True`"""
        return True

    def to_str(self):
        """display the internal dict"""
        return '%r' % self.values


class ConfigFieldsProvider:
    """Provides a list of :class:`djangofloor.conf.fields.ConfigField`.
Used for retrieving settings from a config file.
    """
    name = None

    def get_config_fields(self):
        """Return a list of config fields"""
        raise NotImplementedError


class PythonConfigFieldsProvider(ConfigFieldsProvider):
    """Provide a list of :class:`djangofloor.conf.fields.ConfigField` from an attribute in a Python module. """
    name = 'Python attribute'

    def __init__(self, value=None):
        if value is None:
            module_name, attribute_name = None, None
        else:
            module_name, sep, attribute_name = value.partition(':')
        self.module_name = module_name
        self.attribute_name = attribute_name
        self.module = None
        if module_name is not None:
            from djangofloor.utils import import_module
            try:
                self.module = import_module(module_name, package=None)
            except ImportError:
                pass

    def get_config_fields(self):
        """Return the list that is defined in the module by the attribute name"""
        if self.module:
            return getattr(self.module, self.attribute_name, [])
        return []

    def __str__(self):
        return '%s:%s' % (self.module_name, self.attribute_name)
