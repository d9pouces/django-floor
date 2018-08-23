"""Complex settings at runtime
===========================

Allow to define settings based on references to other settings (overriden in other config files).

Examples:

.. code-block:: python

  # file1: djangofloor.config.defaults
  from djangofloor.config.config_values import SettingReference
  DEBUG = False
  TEMPLATE_DEBUG = SettingReference('DEBUG')


.. code-block:: python

  # file1: myproject.defaults
  DEBUG = True


Since the second file overrides the first one, `TEMPLATE_DEBUG` always has the same value as `DEBUG` (`True`).

"""

import os
import warnings

from django.utils.module_loading import import_string
from django.core.checks import Warning

from djangofloor.checks import settings_check_results

__author__ = "Matthieu Gallet"


class ConfigValue:
    """Base class for special setting values. When a setting is a :class:`djangofloor.settings.ConfigValue`,
      then the method `get_value(merger)` is called for getting the definitive value.
    """

    def __init__(self, value):
        self.value = value

    def get_value(self, merger, provider_name: str, setting_name: str):
        """ Return the intepreted value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        raise NotImplementedError

    # noinspection PyMethodMayBeStatic
    def pre_collectstatic(self, merger, provider_name, setting_name, value):
        """Called before the "collectstatic" command (at least the one provided by Djangofloor).
        Could be used for creating public files or directories (static files, required directories...).
        """
        pass

    # noinspection PyMethodMayBeStatic
    def pre_migrate(self, merger, provider_name, setting_name, value):
        """Called before the "migrate" command.
        Could be used for creating private files (like the SECRET_KEY file)
        """
        pass

    # noinspection PyMethodMayBeStatic
    def post_collectstatic(self, merger, provider_name, setting_name, value):
        """Called after the "collectstatic" command"""
        pass

    # noinspection PyMethodMayBeStatic
    def post_migrate(self, merger, provider_name, setting_name, value):
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

    def get_value(self, merger, provider_name: str, setting_name: str):
        """ Return the non-intepreted value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        return self.value


class Path(ConfigValue):
    """Represent any path on the filesystem."""

    def __init__(self, value, mode=None):
        super().__init__(value)
        self.mode = mode

    def get_value(self, merger, provider_name, setting_name):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        value = merger.analyze_raw_value(self.value, provider_name, setting_name)
        value = os.path.normpath(value)
        return value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, str(self.value))

    @staticmethod
    def makedirs(merger, dirname):
        if not dirname or os.path.isdir(dirname):
            return
        dirname = os.path.abspath(dirname)
        if os.path.exists(dirname):
            merger.stderr.write("'%s' already exists and is not a directory.")
            return
        merger.stdout.write("Creating directory '%s'" % dirname)
        try:
            os.makedirs(dirname)
        except Exception as e:
            merger.stderr.write("Unable to create directory '%s' (%s)" % (dirname, e))

    def chmod(self, merger, filename):
        if not filename or not os.path.isfile(filename):
            return
        filename = os.path.abspath(filename)
        if self.mode is None or (os.stat(filename).st_mode & 0o777) == self.mode:
            return
        merger.stdout.write("Change mode of '%s' to 0o%o" % (filename, self.mode))
        try:
            os.chmod(filename, self.mode)
        except Exception as e:
            merger.stderr.write("Unable to change mode of '%s' (%s)" % (filename, e))


class Directory(Path):
    """Represent a directory on the filesystem, that is automatically created by the "migrate" and "collectstatic"
    commands"""

    def get_value(self, merger, provider_name: str, setting_name: str):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        value = merger.analyze_raw_value(self.value, provider_name, setting_name)
        value = os.path.normpath(value)
        if not value.endswith("/"):
            value += "/"
        if not os.path.isdir(value):
            settings_check_results.append(
                Warning(
                    "'%s' is not a directory. Run the 'collectstatic' command to fix this problem."
                    % value,
                    obj="configuration",
                )
            )
        return value

    def pre_collectstatic(self, merger, provider_name, setting_name, value):
        self.makedirs(merger, value)
        self.chmod(merger, value)

    def pre_migrate(self, merger, provider_name, setting_name, value):
        self.makedirs(merger, value)
        self.chmod(merger, value)


class File(Path):
    """Represent a file name. Its parent directory is automatically created by the "migrate" and "collectstatic"
    command.

    """

    def get_value(self, merger, provider_name: str, setting_name: str):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        value = merger.analyze_raw_value(self.value, provider_name, setting_name)
        value = os.path.normpath(value)
        if not os.path.isfile(value):
            settings_check_results.append(
                Warning("'%s' does not exist." % value, obj="configuration")
            )
        return value

    def pre_collectstatic(self, merger, provider_name, setting_name, value):
        if value is None:
            return
        self.makedirs(merger, os.path.dirname(value))
        self.chmod(merger, value)

    def pre_migrate(self, merger, provider_name, setting_name, value):
        self.pre_collectstatic(merger, provider_name, setting_name, value)


class AutocreateFileContent(File):
    """Return the content of an existing file, or automatically write it and returns the content of the created file.
    Content must be a unicode string.
    The first argument of the provided `create_function` is the name of the file to create.

    The file is only written when the "migrate" Django command is called.
    The first arg of the provided `create_function` is a bool, in addition of your own *args and **kwargs:
        * `True` when Django is ready and your function is called for writing the file during the "migrate" command
        * `False` when Django is not ready and your function is called for loading settings

    """

    def __init__(self, value, create_function, mode=None, *args, **kwargs):
        """

        :param value: name of the file
        :param create_function: called when the file does not exist.
            Must return a text string.
        :param mode: mode of the create file (chmod value, like 0o755 for a file readable by everyone)
        :param args: extra args passed to the `create_function`
        :param kwargs:  extra keyword args passed to the `create_function`

        """
        super().__init__(value, mode=mode)
        self.create_function = create_function
        self.args = args
        self.kwargs = kwargs

    def pre_migrate(self, merger, provider_name, setting_name, value):
        filename = merger.analyze_raw_value(self.value, provider_name, setting_name)
        if filename is None or os.path.isfile(
            filename
        ):  # empty filename, or it already exists => nothing to do
            return
        result = self.create_function(True, *self.args, **self.kwargs)
        filename = os.path.abspath(filename)
        if result is not None:
            self.makedirs(merger, os.path.dirname(filename))
            merger.stdout.write("Writing new value to '%s'" % filename)
            try:
                result_text = self.serialize_value(result)
                with open(filename, "w", encoding="utf-8") as fd:
                    fd.write(result_text)
            except Exception as e:
                merger.stderr.write(
                    "Unable to write content of '%s' (%s)" % (filename, e)
                )
            self.chmod(merger, filename)
        else:
            merger.stderr.write("Invalid empty content for '%s'" % filename)

    def pre_collectstatic(self, merger, provider_name, setting_name, value):
        pass

    def get_value(self, merger, provider_name: str, setting_name: str):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        filename = merger.analyze_raw_value(self.value, provider_name, setting_name)
        if os.path.isfile(filename):
            with open(filename, "r", encoding="utf-8") as fd:
                result_text = fd.read()
            result = self.unserialize_value(result_text)
        else:
            settings_check_results.append(
                Warning(
                    "'%s' does not exist. Run the 'migrate' command to fix this problem."
                    % filename,
                    obj="configuration",
                )
            )
            result = self.create_function(False, *self.args, **self.kwargs)
        return result

    # noinspection PyMethodMayBeStatic
    def serialize_value(self, value) -> str:
        """Serialize the result value to write it to the target file.

        :param value: the value returned by the `create_function`
        :return:
        """
        return value

    # noinspection PyMethodMayBeStatic
    def unserialize_value(self, value: str):
        """
        Format the text read in the target file.
        :param value: the content of the file
        :return:
        """
        return value


class AutocreateFile(AutocreateFileContent):
    """Represent a file name. Its parent directory is automatically created by the "collectstatic" command.
     """

    def __init__(self, value, mode=None, *args, **kwargs):
        super().__init__(value, lambda x: "", mode=mode, *args, **kwargs)

    def get_value(self, merger, provider_name: str, setting_name: str):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        filename = merger.analyze_raw_value(self.value, provider_name, setting_name)
        if not os.path.isfile(filename):
            settings_check_results.append(
                Warning(
                    "'%s' does not exist. Run the 'migrate' command to fix this problem."
                    % filename,
                    obj="configuration",
                )
            )
        return filename


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
        super().__init__(value)
        self.func = func

    def get_value(self, merger, provider_name: str, setting_name: str):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        result = merger.get_setting_value(self.value)
        if self.func:
            result = self.func(result)
        return result


class DeprecatedSetting(ConfigValue):
    def __init__(self, value, default=None, msg=""):
        super().__init__(value)
        self.default = default
        self.msg = msg

    def get_value(self, merger, provider_name: str, setting_name: str):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        if merger.has_setting_value(self.value) and merger.get_setting_value(
            self.value
        ):
            from djangofloor.utils import RemovedInDjangoFloor200Warning

            warnings.warn(
                '"%s" setting should not be used anymore. %s' % (self.value, self.msg),
                RemovedInDjangoFloor200Warning,
            )
            return merger.get_setting_value(self.value)
        return merger.analyze_raw_value(self.default, provider_name, setting_name)

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
        if isinstance(value, str):
            value = import_string(value)
        super().__init__(value)
        if hasattr(value, "required_settings"):
            self.required = list(value.required_settings)
        else:
            self.required = required

    def get_value(self, merger, provider_name: str, setting_name: str):
        """ Return the value

        :param merger: merger object, with all interpreted settings
        :type merger: :class:`djangofloor.utils.SettingMerger`
        :param provider_name: name of the provider containing this value
        :param setting_name: name of the setting containing this value
        """
        for required in self.required:
            merger.get_setting_value(required)
        return self.value(merger.settings)

    def __repr__(self):
        fn = repr(self.value)
        if hasattr(self.value, "__module__") and hasattr(self.value, "__name__"):
            fn = "%s.%s" % (self.value.__module__, self.value.__name__)
        return "CallableSetting(%r, %s)" % (
            fn,
            ", ".join(["%r" % x for x in self.required]),
        )


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
