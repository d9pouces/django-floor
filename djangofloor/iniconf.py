""".. deprecated:: 1.0"""
import warnings

from djangofloor.conf import fields, mapping
from djangofloor.utils import RemovedInDjangoFloor200Warning

__author__ = 'Matthieu Gallet'

warnings.warn('djangofloor.iniconf module and its functions are moved to djangofloor.conf.fields',
              RemovedInDjangoFloor200Warning)


def bool_setting(value):
    return fields.bool_setting(value)


def str_or_none(text):
    return fields.str_or_none(text)


def str_or_blank(value):
    return fields.str_or_blank(value)


def guess_relative_path(value):
    return fields.guess_relative_path(value)


def strip_split(value):
    return fields.strip_split(value)


MISSING_VALUE = [[]]


class OptionParser(fields.ConfigField):
    def __init__(self, setting_name, option, converter=str, to_str=str_or_blank, help_str=None,
                 doc_default_value=MISSING_VALUE):
        """class that maps an option in a .ini file to a setting.

        :param setting_name: the name of the setting (like "DATABASE_ENGINE")
        :type setting_name: `str`
        :param option: the section and the option in a .ini file (like "database.engine")
        :type option: `str`
        :param converter: any callable that takes a text value and returns an object. Default to `str_or_none`
        :type converter: `callable`
        :param to_str: any callable that takes the Python value and that converts it to str
            only used for writing sample config file. Default to `str`
        :type to_str: `callable`
        :param help_str: any text that can serve has help in documentation.
            If None, then `settings.%s_HELP % setting_name` will be used as help text.
        :type help_str: `str`
        :param doc_default_value: the value that will be used in documentation.
        The current setting value will be used if left to `None`.
        :type doc_default_value: `object`
        """
        super(OptionParser, self).__init__(option, setting_name, from_str=converter,
                                           to_str=to_str, help_str=help_str, default=doc_default_value)

        self.option = option
        self.converter = converter
        self.help_str = help_str
        self.default_value = None
        self.doc_default_value = doc_default_value

    @property
    def section(self):
        return self.option.partition('.')[0]

    @property
    def key(self):
        return self.option.partition('.')[2]

    def has_value(self, parser):
        section, sep, option = self.option.partition('.')
        return parser.has_option(section=section, option=option)

    def str_value(self):
        return self.to_str(self.default_value)

    @property
    def __name__(self):
        return self.option

    def __str__(self):
        return self.option

    def set_value(self, parser, ini_values):
        """ Given a .ini config file and a Python dict, read its value and set the dict with it

        :param parser: ConfigParser that read the .ini config file
        :type parser: :class:`configparser.ConfigParser`
        :param ini_values: a dict to fill
        :type ini_values: :class:`dict`
        :return: `True` if this value is defined in the configuration file, `False` otherwise
        :rtype: :class:`bool`
        """
        section, sep, option = self.option.partition('.')
        if not self.has_value(parser):
            return False
        value = parser.get(section=section, option=option)
        ini_values[self.setting_name] = self.converter(value)
        return True


INI_MAPPING = mapping.INI_MAPPING
