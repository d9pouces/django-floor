"""Classes and functions used for the DjangoFloor settings system
==============================================================

Define several helpers classes and internal functions for the DjangoFloor settings system, allowing to merge
settings from different sources. This file must be importable while Django is not loaded yet.
"""

import sys
import traceback
import warnings
from collections import OrderedDict
from distutils.version import LooseVersion

from django import get_version
from django.conf import LazySettings
from django.core.management import color_style
from django.core.management.base import OutputWrapper
from django.core.management.color import no_style
from django.utils.functional import empty

from djangofloor.conf.config_values import ExpandIterable, ConfigValue, SettingReference
from djangofloor.conf.fields import ConfigField
from djangofloor.conf.providers import ConfigProvider, PythonConfigFieldsProvider

try:
    # noinspection PyCompatibility
    from configparser import ConfigParser
except ImportError:
    # noinspection PyUnresolvedReferences,PyCompatibility
    from ConfigParser import ConfigParser
import string

__author__ = "Matthieu Gallet"

_deprecated_settings = {
    "BIND_ADDRESS": SettingReference("LISTEN_ADDRESS"),
    "BROKER_DB": SettingReference("CELERY_DB"),
    "FLOOR_BACKUP_SINGLE_TRANSACTION": None,
    "FLOOR_EXTRA_CSS": SettingReference("DF_CSS"),
    "FLOOR_EXTRA_JS": SettingReference("DF_JS"),
    "FLOOR_FAKE_AUTHENTICATION_USERNAME": SettingReference(
        "DF_FAKE_AUTHENTICATION_USERNAME"
    ),
    "FLOOR_WS_FACILITY": None,
    "FLOOR_INDEX": SettingReference("DF_INDEX_VIEW"),
    "FLOOR_PROJECT_VERSION": SettingReference("DF_PROJECT_VERSION"),
    "FLOOR_SIGNAL_DECODER": SettingReference("WEBSOCKET_SIGNAL_DECODER"),
    "FLOOR_SIGNAL_ENCODER": SettingReference("WEBSOCKET_SIGNAL_ENCODER"),
    "FLOOR_URL_CONF": SettingReference("DF_URL_CONF"),
    "FLOOR_USE_WS4REDIS": "ws4redis is not used anymore.",
    "LOG_PATH": 'Use "LOG_DIRECTORY" instead.',
    "LOGOUT_URL": None,
    "MAX_REQUESTS": None,
    "PROTOCOL": SettingReference("SERVER_PROTOCOL"),
    "REDIS_HOST": SettingReference("CELERY_HOST"),
    "REDIS_PORT": SettingReference("CELERY_PORT"),
    "REVERSE_PROXY_IPS": None,
    "REVERSE_PROXY_TIMEOUT": None,
    "REVERSE_PROXY_SSL_KEY_FILE": None,
    "REVERSE_PROXY_SSL_CRT_FILE": None,
    "REVERSE_PROXY_PORT": 'Use the port component of "SERVER_BASE_URL" instead.',
    "THREADS": None,
    "USE_SCSS": None,
    "WORKERS": None,
    "WEBSOCKET_REDIS_EMULATION_INTERVAL": None,
    "WEBSOCKET_REDIS_SUBSCRIBER": None,
}
_warned_settings = set()


def __getattr(self, name):
    if name in _deprecated_settings:
        new_content = _deprecated_settings[name]
        if name not in _warned_settings:
            from djangofloor.utils import RemovedInDjangoFloor200Warning

            f = traceback.extract_stack()
            is_debug = any(filename[0].endswith("/debug.py") for filename in f)
            if not is_debug:
                msg = 'Setting "%s" is deprecated. ' % name

                if isinstance(new_content, SettingReference):
                    msg += "Replaced by %s" % new_content.value
                else:
                    msg += new_content or ""
                warnings.warn(msg, RemovedInDjangoFloor200Warning, stacklevel=2)
            _warned_settings.add(name)
        if isinstance(new_content, SettingReference):
            return getattr(self, new_content.value)
    if self._wrapped is empty:
        self._setup(name)
    return getattr(self._wrapped, name)


LazySettings.__getattr__ = __getattr


class SettingMerger:
    """Load different settings modules and config files and merge them.
    """

    def __init__(
        self,
        fields_provider,
        providers,
        extra_values=None,
        stdout=None,
        stderr=None,
        no_color=False,
    ):
        self.fields_provider = fields_provider or PythonConfigFieldsProvider(None)
        extra_values = extra_values or {}
        self.extra_values = extra_values
        self.providers = providers or []
        self.__formatter = string.Formatter()
        self.settings = {}
        self.config_values = (
            []
        )  # list of (ConfigValue, provider_name, setting_name, final_value)
        self.raw_settings = OrderedDict()
        for key, value in extra_values.items():
            self.raw_settings[key] = OrderedDict()
            self.raw_settings[key][None] = value
        # raw_settings[setting_name][str(provider) or None] = raw_value
        self.__working_stack = set()
        self.stdout = OutputWrapper(stdout or sys.stdout)
        self.stderr = OutputWrapper(stderr or sys.stderr)
        if no_color:
            self.style = no_style()
        else:
            self.style = color_style()
            self.stderr.style_func = self.style.ERROR

    def add_provider(self, provider):
        self.providers.append(provider)

    def process(self):
        self.load_raw_settings()
        self.load_settings()

    def load_raw_settings(self):
        # get all setting names and sort them
        all_settings_names_set = set()
        for field in self.fields_provider.get_config_fields():
            assert isinstance(field, ConfigField)
            all_settings_names_set.add(field.setting_name)
        for provider in self.providers:
            assert isinstance(provider, ConfigProvider)
            for setting_name, value in provider.get_extra_settings():
                all_settings_names_set.add(setting_name)
        all_settings_names = list(sorted(all_settings_names_set))
        # initialize all defined settings
        for setting_name in all_settings_names:
            self.raw_settings[setting_name] = OrderedDict()
        # fetch default values if its exists (useless?)
        for field in self.fields_provider.get_config_fields():
            assert isinstance(field, ConfigField)
            self.raw_settings[field.setting_name][None] = field.value
        # read all providers (in the right order)
        for provider in self.providers:
            assert isinstance(provider, ConfigProvider)
            source_name = str(provider)
            for field in self.fields_provider.get_config_fields():
                assert isinstance(field, ConfigField)
                if provider.has_value(field):
                    value = provider.get_value(field)
                    # noinspection PyTypeChecker
                    self.raw_settings[field.setting_name][source_name] = value
            for setting_name, value in provider.get_extra_settings():
                self.raw_settings[setting_name][source_name] = value

    def has_setting_value(self, setting_name):
        return setting_name in self.raw_settings

    def get_setting_value(self, setting_name):
        if setting_name in self.settings:
            return self.settings[setting_name]
        elif setting_name in self.__working_stack:
            raise ValueError(
                "Invalid cyclic dependency between " + ", ".join(self.__working_stack)
            )
        elif setting_name not in self.raw_settings:
            raise ValueError("Invalid setting reference: %s" % setting_name)
        self.__working_stack.add(setting_name)
        provider_name, raw_value = None, None
        for provider_name, raw_value in self.raw_settings[setting_name].items():
            pass
        value = self.analyze_raw_value(raw_value, provider_name, setting_name)
        self.settings[setting_name] = value
        self.__working_stack.remove(setting_name)
        return value

    def load_settings(self):
        for setting_name in self.raw_settings:
            self.get_setting_value(setting_name)

    def call_method_on_config_values(self, method_name: str):
        """Scan all settings, looking for :class:`django.conf.config_values.ConfigValue` and calling one of their
        methods.

        :param method_name: 'pre_collectstatic', 'pre_migrate', 'post_collectstatic', or 'post_migrate'.
        """
        for raw_value, provider_name, setting_name, final_value in self.config_values:
            try:
                getattr(raw_value, method_name)(
                    self, provider_name, setting_name, final_value
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        'Invalid value "%s" in %s for %s (%s)'
                        % (raw_value, provider_name or "built-in", setting_name, e)
                    )
                )

    def analyze_raw_value(self, obj, provider_name, setting_name):
        """Parse the object for replacing variables by their values.

        If `obj` is a string like "THIS_IS_{TEXT}", search for a setting named "TEXT" and replace {TEXT} by its value
        (say, "VALUE"). The returned object is then equal to "THIS_IS_VALUE".
        If `obj` is a list, a set, a tuple or a dict, its components are recursively parsed.
        If `obj` is a subclass of :class:`djangofloor.conf.config_values.ConfigValue`, its value is on-the-fly computed.
        Otherwise, `obj` is returned as-is.

        :param obj: object to analyze
        :param provider_name: the name of the config file
        :param setting_name: the name of the setting containing this value
            but this value can be inside a dict or a list (like `SETTING = [Directory("/tmp"), ]`)
        :return: the parsed setting
        """
        if isinstance(obj, str):
            values = {}
            for (
                literal_text,
                field_name,
                format_spec,
                conversion,
            ) in self.__formatter.parse(obj):
                if field_name is not None:
                    values[field_name] = self.get_setting_value(field_name)
            return self.__formatter.format(obj, **values)
        elif isinstance(obj, ConfigValue):
            final_value = obj.get_value(self, provider_name, setting_name)
            self.config_values.append((obj, provider_name, setting_name, final_value))
            return final_value
        elif isinstance(obj, list) or isinstance(obj, tuple):
            result = []
            for sub_obj in obj:
                if isinstance(sub_obj, ExpandIterable):
                    result += self.get_setting_value(sub_obj.value)
                else:
                    result.append(
                        self.analyze_raw_value(sub_obj, provider_name, setting_name)
                    )
            if isinstance(obj, tuple):
                return tuple(result)
            return result
        elif isinstance(obj, set):
            result = set()
            for sub_obj in obj:
                if isinstance(sub_obj, ExpandIterable):
                    result |= self.get_setting_value(sub_obj.value)
                else:
                    result.add(
                        self.analyze_raw_value(sub_obj, provider_name, setting_name)
                    )
            return result
        elif isinstance(obj, dict):
            result = obj.__class__()  # OrderedDict or plain dict
            for sub_key, sub_obj in obj.items():
                if isinstance(sub_obj, ExpandIterable):
                    result.update(self.get_setting_value(sub_obj.value))
                else:
                    value = self.analyze_raw_value(sub_obj, provider_name, setting_name)
                    key = self.analyze_raw_value(sub_key, provider_name, setting_name)
                    result[key] = value
            return result
        return obj

    def post_process(self):
        """Perform some cleaning on settings:

            * remove duplicates in `INSTALLED_APPS` (keeps only the first occurrence)
        """
        # remove duplicates in INSTALLED_APPS
        self.settings["INSTALLED_APPS"] = list(
            OrderedDict.fromkeys(self.settings["INSTALLED_APPS"])
        )
        django_version = get_version()
        # remove deprecated settings
        if LooseVersion(django_version) >= LooseVersion("1.8"):
            if "TEMPLATES" in self.settings:
                for key in (
                    "TEMPLATE_DIRS",
                    "TEMPLATE_CONTEXT_PROCESSORS",
                    "TEMPLATE_LOADERS",
                    "TEMPLATE_DEBUG",
                ):
                    if key in self.settings:
                        del self.settings[key]

    def write_provider(self, provider, include_doc=False):
        for config_field in sorted(
            self.fields_provider.get_config_fields(), key=lambda x: x.name
        ):
            assert isinstance(config_field, ConfigField)
            if config_field.setting_name not in self.settings:
                continue
            config_field.value = self.settings[config_field.setting_name]
            provider.set_value(config_field, include_doc=include_doc)
