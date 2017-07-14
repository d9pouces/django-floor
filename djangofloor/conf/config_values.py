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

    # noinspection PyMethodMayBeStatic
    def pre_collectstatic(self, merger, value):
        """Called before the "collectstatic" command (at least the one provided by Djangofloor).
        Could be used for creating public files or directories (static files, required directories...).
        """
        pass

    # noinspection PyMethodMayBeStatic
    def pre_migrate(self, merger, value):
        """Called before the "migrate" command.
        Could be used for creating private files (like the SECRET_KEY file)
        """
        pass

    # noinspection PyMethodMayBeStatic
    def post_collectstatic(self, merger, value):
        """Called after the "collectstatic" command"""
        pass

    # noinspection PyMethodMayBeStatic
    def post_migrate(self, merger, value):
        """Called after the "migrate" command"""
        pass

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

    def __init__(self, value, mode=0o755):
        super().__init__(value)
        self.mode = mode

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


class Directory(Path):
    """Represent a directory on the filesystem, that is automatically created by the "migrate" and "collectstatic"
    commands"""

    def get_value(self, merger):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        value = merger.analyze_raw_value(self.value)
        value = os.path.normpath(value)
        if not value.endswith('/'):
            value += '/'
        return value

    def pre_collectstatic(self, merger, value):
        if not os.path.isdir(value):
            os.makedirs(value)
        if self.mode and (os.stat(value).st_mode & 0o777) != self.mode:
            os.chmod(value, self.mode)

    def pre_migrate(self, merger, value):
        self.pre_collectstatic(merger, value)


class File(Path):
    """Represent a file name. Its parent directory is automatically created by the "migrate" and "collectstatic"
    command.

    """

    def get_value(self, merger):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        value = merger.analyze_raw_value(self.value)
        value = os.path.normpath(value)
        return value

    def pre_collectstatic(self, merger, value):
        filename = merger.analyze_raw_value(self.value)
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        if os.path.isfile(value) and self.mode is not None:
            os.chmod(value, self.mode)

    def pre_migrate(self, merger, value):
        self.pre_collectstatic(merger, value)


class AutocreateFile(File):
    """Represent a file name. Its parent directory is automatically created by the "collectstatic" command.
     If the file does not exist, the provided callable is used when the "migrate" command is called.

     The first argument of the provided `create_function` is the name of the file to create.
     If `create_function` is `None`, then an empty file is created.
     """

    def __init__(self, value, create_function, mode=None, *args, **kwargs):
        """

        :param value: name of the file
        :param create_function: called when the file does not exist.
            Must return a text string.
        :param mode: mode of the create file (chmod value, like 0o755 for a file readable by everyone)
        :param args: args passed to the `create_function`
        :param kwargs:  keyword args passed to the `create_function`

        """
        super().__init__(value, mode=mode)
        self.create_function = create_function
        self.args = args
        self.kwargs = kwargs

    def pre_migrate(self, merger, value):
        self.pre_collectstatic(merger, value)
        if os.path.isfile(value):
            return
        if self.create_function is None:
            open(value, 'w').close()
        else:
            self.create_function(value, *self.args, **self.kwargs)
        if self.mode is not None and os.path.isfile(value):
            os.chmod(value, self.mode)


class AutocreateFileContent(AutocreateFile):
    """Return the content of an existing file, or automatically write it and returns the content of the created file.
    Content must be a unicode string.

    The file is only written when the "migrate" Django command is called.
    The first arg of the provided `create_function` is a bool, in addition of your *args and **kwargs:
        * `True` when Django is ready and your function is called for writing the file during the "migrate" command
        * `False` when Django is not ready and your function is called for loading settings

    """

    def pre_migrate(self, merger, value):
        filename = merger.analyze_raw_value(self.value)
        if os.path.isfile(filename):
            return
        result = self.create_function(True, *self.args, **self.kwargs)
        dirname = os.path.dirname(filename)
        try:
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            with open(filename, 'w', encoding='utf-8') as fd:
                fd.write(result)
            if self.mode is not None:
                os.chmod(filename, self.mode)
        except PermissionError:
            print('Unable to modify %s: permission denied.' % value)

    def get_value(self, merger):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        """
        filename = merger.analyze_raw_value(self.value)
        if os.path.isfile(filename):
            with codecs.open(filename, 'r', encoding='utf-8') as fd:
                result = fd.read()
        else:
            result = self.create_function(False, *self.args, **self.kwargs)
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
    >>> def inverse_value(values):
    >>>     return not values['SETTING_1']
    >>> SETTING_2 = CallableSetting(inverse_value, 'SETTING_1')

    In `local_settings.py`

    >>> SETTING_1 = False

    In your code:

    >>> from django.conf import settings
    >>> if hasattr(settings, 'SETTING_2'):
    >>>     assert(settings.SETTING_1 is False)  # default value is overriden by local_settings.py
    >>>     assert(settings.SETTING_2 is True)  # SETTING_2 value is dynamically computed on startup

    Extra arguments must be strings, that are interpreted as required settings,
    that must be available before the call to your function. You can also set an attribute called
    `required_settings`.

    >>> def inverse_value(values):
    >>>     return not values['SETTING_1']
    >>> inverse_value.required_settings = ['SETTING_1']
    >>> SETTING_2 = CallableSetting(inverse_value)

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
