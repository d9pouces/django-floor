# -*- coding: utf-8 -*-
"""Allow dependencies between settings
===================================

By default, setting files are plain Python files, and you can not reference settings different Python files.
Examples:

.. code-block:: python

  # file1: djangofloor.config.defaults
  from djangofloor.config.config_values import SettingReference
  DEBUG = False
  TEMPLATE_DEBUG = SettingReference('DEBUG')


.. code-block:: python

  # file1: myproject.defaults
  DEBUG = True


Since the second file overrides the first one, `TEMPLATE_DEBUG` has the same value as `DEBUG` and is `True`.

"""
from __future__ import unicode_literals, print_function, absolute_import

import codecs
import os
import warnings

from django.utils.module_loading import import_string
from django.utils.six import text_type


__author__ = 'Matthieu Gallet'


class ConfigValue(object):
    """Base class for special setting values. When a setting is a :class:`djangofloor.settings.ConfigValue`,
      then the method `get_value(merger)` is called for getting the definitive value.
    """
    def __init__(self, value):
        self.value = value

    def get_value(self, merger):
        """ Return the intepreted value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        raise NotImplementedError

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)


class RawValue(ConfigValue):
    """Return the value as-is. Since by defaults all string values are assumed to be formatted string,
you need to use :class:`RawValue` for using values that should be formatted.

.. code-block:: python

    from djangofloor.conf.config_values import RawValue
    SETTING_1 = '{DEBUG}'  # will be transformed to 'True' or 'False'
    SETTING_2 = Raw('{DEBUG}')  # will be kept as  '{DEBUG}'
    """

    def get_value(self, merger):
        """ Return the non-intepreted value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        return self.value


class Path(ConfigValue):
    """Represent any path on the filesystem."""

    def get_value(self, merger):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        value = merger.analyze_raw_value(self.value)
        value = os.path.normpath(value)
        return value

    def __repr__(self):
        return text_type(self.value)


class AutocreateDirectory(Path):
    """Represent a directory path that must be created on startup (if not `merger.read_only`)
    """

    def get_value(self, merger):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        value = merger.analyze_raw_value(self.value)
        value = os.path.normpath(value)
        if not os.path.isdir(value) and not merger.read_only:
            try:
                os.makedirs(value)
            except PermissionError:
                print('Unable to create %s: Permission denied' % value)
        if not value.endswith('/'):
            value += '/'
        return value


class AutocreateFile(Path):
    """Represent a file name, whose parent directory should be created on startup
    """

    def get_value(self, merger):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        value = merger.analyze_raw_value(self.value)
        value = os.path.normpath(value)
        dirname = os.path.dirname(value)
        if not os.path.isdir(dirname) and not merger.read_only:
            os.makedirs(dirname)  # do not use ensure_dir()! (cycling dependencies…)
        return value


class AutocreateFileContent(Path):
    """Return the content of an existing file, or automatically write it and returns the content of the created file.
    Content must be a unicode string.

    """
    def __init__(self, value, create_function, *args, **kwargs):
        """

        :param value: name of the file
        :param create_function: callable called when the file does not exist. Must return a text string
        :param args: args passed to the `create_function`
        :param kwargs:  keyword args passed to the `create_function`
        """
        super(AutocreateFileContent, self).__init__(value)
        self.create_function = create_function
        self.args = args
        self.kwargs = kwargs

    def get_value(self, merger):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        filename = merger.analyze_raw_value(self.value)
        dirname = os.path.dirname(filename)
        allow_create = not merger.read_only
        if not os.path.isdir(dirname) and allow_create:
            try:
                os.makedirs(dirname)  # do not use ensure_dir()! (cycling dependencies…)
            except PermissionError:
                allow_create = False
                print('Unable to create %s: Permission denied' % dirname)
        if os.path.isfile(filename):
            with codecs.open(filename, 'r', encoding='utf-8') as fd:
                result = fd.read()
        elif merger.read_only or not callable(self.create_function):
            result = ''
        else:
            result = self.create_function(*self.args, **self.kwargs)
            if allow_create:
                try:
                    with codecs.open(filename, 'w', encoding='utf-8') as fd:
                        fd.write(result)
                except PermissionError:
                    print('Unable to create %s: Permission denied' % filename)
        return result


class SettingReference(ConfigValue):
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
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        result = merger.get_setting_value(self.value)
        if self.func:
            result = self.func(result)
        return result


class DeprecatedSetting(ConfigValue):

    def __init__(self, value, default=None, msg=''):
        super(DeprecatedSetting, self).__init__(value)
        self.default = default
        self.msg = msg

    def get_value(self, merger):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        if merger.has_setting_value(self.value) and merger.get_setting_value(self.value):
            from djangofloor.utils import RemovedInDjangoFloor110Warning
            warnings.warn('"%s" setting should not be used anymore. %s' % (self.value, self.msg),
                          RemovedInDjangoFloor110Warning)
            return merger.get_setting_value(self.value)
        return merger.analyze_raw_value(self.default)

    def __repr__(self):
        return repr(self.value)


class CallableSetting(ConfigValue):
    """
    Require a function(kwargs) as argument, this function will be called with all already computed settings in a dict.

    >>> SETTING_1 = True
    >>> SETTING_2 = CallableSetting(lambda x: not x['SETTING_1'], 'SETTING_1')

    In `local_settings.py`

    >>> SETTING_1 = False

    In your code:

    >>> from django.conf import settings

    Then `settings.SETTING_2` is equal to `True`

    Extra arguments must be strings, that are interpreted as required settings,
    that must be available before the call to your function. You can also set an attribute called
    `required_settings`.


    >>> def sample_setting(x, y):
    >>>     return x + y
    >>> sample_setting.required_settings = ['SETTING_1', 'SETTING_2']

    """

    def __init__(self, value, *required):
        if isinstance(value, text_type):
            value = import_string(value)
        super(CallableSetting, self).__init__(value)
        if hasattr(value, 'required_settings'):
            self.required = list(value.required_settings)
        else:
            self.required = required

    def get_value(self, merger):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        for required in self.required:
            merger.get_setting_value(required)
        return self.value(merger.settings)

    def __repr__(self):
        fn = repr(self.value)
        if hasattr(self.value, '__module__') and hasattr(self.value, '__name__'):
            fn = '%s.%s' % (self.value.__module__, self.value.__name__)
        return "CallableSetting(%r, %s)" % (fn, ', '.join(['%r' % x for x in self.required]))


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
    pass
