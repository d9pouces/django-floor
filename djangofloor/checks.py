"""Define checks integrated to the Django check framework
=====================================================

Django offers a system check framework, but that is called only after the Django setup.
However, settings based on callables (like :class:`djangofloor.conf.config_values.CallableSetting`)  can
also trigger some :class:`django.core.checks.Warning` during the setting loading.
Just append them to the `settings_check_results` list to delay them and display them just after the Django setup.

"""
import sys

import os
from django.core.checks import register, Error

__author__ = 'Matthieu Gallet'

settings_check_results = []


def missing_package(package_name, desc=''):
    if hasattr(sys, 'real_prefix'):  # inside a virtualenv
        cmd = 'Try "pip install %s" to install it.' % package_name
    elif __file__.startswith(os.environ.get('HOME', '/home')):
        cmd = 'Try "pip3 install --user %s" to install it.' % package_name
    else:
        cmd = 'Try "sudo pip3 install %s" to install it.' % package_name
    settings_check_results.append(Error('Python package "%s" is required%s. %s' % (package_name, desc, cmd),
                                        obj='djangofloor.conf.settings', id='djangofloor.E001'))


# noinspection PyUnusedLocal
@register()
def settings_check(app_configs, **kwargs):
    return settings_check_results
