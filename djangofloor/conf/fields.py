"""Convert values from config files to Python values
=================================================

Use these classes in your mapping provided in `yourproject.iniconf:INI_MAPPING`.
Check :mod:`djangofloor.conf.mapping` for examples.
"""

import os

from django.core.checks import Error

from djangofloor.checks import settings_check_results

__author__ = "Matthieu Gallet"

MISSING_VALUE = [[]]


def bool_setting(value):
    """return `True` if the provided (lower-cased) text is one of ('1', 'ok', 'yes', 'true', 'on')"""
    return str(value).lower() in {"1", "ok", "yes", "true", "on"}


def str_or_none(text):
    """return `None` if the text is empty, else returns the text"""
    return text or None


def str_or_blank(value):
    """return '' if the provided value is `None`, else return value"""
    return "" if value is None else str(value)


def guess_relative_path(value):
    """Replace an absolute path by its relative path if the abspath begins by the current dir"""
    if value is None:
        return ""
    elif os.path.exists(value):
        value = os.path.abspath(value)
        return value.replace(os.path.abspath(os.getcwd()), ".")
    return value


def strip_split(value):
    """Split the value on "," and strip spaces of the result. Remove empty values.

    >>> strip_split('keyword1, keyword2 ,,keyword3')
    ["keyword1", "keyword2", "keyword3"]

    >>> strip_split('')
    []

    >>> strip_split(None)
    []

    :param value:
    :type value:
    :return: a list of strings
    :rtype: :class:`list`
    """
    if value:
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


class ConfigField:
    """Class that maps an option in a .ini file to a setting.

    :param name: the section and the option in a .ini file (like "database.engine")
    :param setting_name: the name of the setting (like "DATABASE_ENGINE")
    :param from_str: any callable that takes a text value and returns an object. Default to `str_or_none`
    :type from_str: `callable`
    :param to_str: any callable that takes the Python value and that converts it to str. Default to `str`
    :type to_str: `callable`
    :param help_str: any text that can serve has help in documentation.
    :param default: the value that will be used in documentation. The current setting value is used if equal to `None`.
    """

    def __init__(
        self,
        name: str,
        setting_name: str,
        from_str=str,
        to_str=str_or_blank,
        help_str: str = None,
        default: object = None,
    ):
        self.name = name
        self.setting_name = setting_name
        self.from_str = from_str
        self.to_str = to_str
        self.__doc__ = help_str
        self.value = default

    def __str__(self):
        return self.name


class CharConfigField(ConfigField):
    """Accepts str values. If `allow_none`, then `None` replaces any empty value."""

    def __init__(self, name, setting_name, allow_none=True, **kwargs):
        from_str = str_or_none if allow_none else str
        super().__init__(
            name, setting_name, from_str=from_str, to_str=str_or_blank, **kwargs
        )


class IntegerConfigField(ConfigField):
    """Accept integer values. If `allow_none`, then `None` replaces any empty values (other `0` is used)."""

    def __init__(self, name, setting_name, allow_none=True, **kwargs):
        if allow_none:

            def from_str(value: str):
                return int(value) if value else None

        else:

            def from_str(value: str):
                return int(value) if value else 0

        super().__init__(
            name, setting_name, from_str=from_str, to_str=str_or_blank, **kwargs
        )


class FloatConfigField(ConfigField):
    """Accept floating-point values. If `allow_none`, then `None` replaces any empty values (other `0.0` is used)."""

    def __init__(self, name, setting_name, allow_none=True, **kwargs):
        if allow_none:

            def from_str(value):
                return float(value) if value else None

        else:

            def from_str(value):
                return float(value) if value else 0.0

        super().__init__(
            name, setting_name, from_str=from_str, to_str=str_or_blank, **kwargs
        )


class ListConfigField(ConfigField):
    """Convert a string to a list of values, splitted with the :meth:`djangofloor.conf.fields.strip_split` function."""

    def __init__(self, name, setting_name, **kwargs):
        def to_str(value):
            if value:
                return ",".join([str(x) for x in value])
            return ""

        super().__init__(
            name, setting_name, from_str=strip_split, to_str=to_str, **kwargs
        )


class BooleanConfigField(ConfigField):
    """Search for a boolean value in the ini file.
    If this value is empty and `allow_none` is `True`, then the value is `None`.
    Otherwise returns `True` if the provided (lower-cased) text is one of ('1', 'ok', 'yes', 'true', 'on')
    """

    def __init__(self, name, setting_name, allow_none=False, **kwargs):
        if allow_none:

            def from_str(value):
                if not value:
                    return None
                return bool_setting(value)

            def to_str(value):
                if value is None:
                    return ""
                return str(bool(value)).lower()

        else:

            def from_str(value):
                return bool_setting(value)

            def to_str(value):
                return str(bool(value)).lower()

        super().__init__(name, setting_name, from_str=from_str, to_str=to_str, **kwargs)


class ChoiceConfigFile(ConfigField):
    """Only allow a limited set of values in the .ini file.
    The available values must be given as :class:`str`.

    Choices must be a :class:`dict`, mapping .ini (string) values to actual values.

    If an invalid value is provided by the user, then `None` is returned, but an error is displayed
    through the Django check system.
    """

    def __init__(self, name, setting_name, choices, help_str="", **kwargs):
        def from_str(value):
            if value not in choices:
                valid = ", ".join(['"%s"' % x for x in choices])
                settings_check_results.append(
                    Error(
                        'Invalid value "%s". Valid choices: %s.' % (value, valid),
                        obj="configuration",
                    )
                )
            return choices.get(value)

        def to_str(value):
            for k, v in choices.items():
                if v == value:
                    return str(k)
            return ""

        valid_values = ", ".join(['"%s"' % x for x in choices])
        if help_str:
            help_str += " Valid choices: %s" % valid_values
        else:
            help_str = "Valid choices: %s" % valid_values

        super().__init__(
            name,
            setting_name,
            from_str=from_str,
            to_str=to_str,
            help_str=help_str,
            **kwargs
        )
