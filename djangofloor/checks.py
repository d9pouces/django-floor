"""Define checks integrated to the Django check framework
=====================================================

Django offers a system check framework, but that is called only after the Django setup.
However, settings based on callables (like :class:`djangofloor.conf.config_values.CallableSetting`)  can
also trigger some :class:`django.core.checks.Warning` during the setting loading.
Just append them to the `settings_check_results` list to delay them and display them just after the Django setup.

"""

from django.core.checks import register

__author__ = 'Matthieu Gallet'

settings_check_results = []


# noinspection PyUnusedLocal
@register()
def settings_check(app_configs, **kwargs):
    return settings_check_results
