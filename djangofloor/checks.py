# -*- coding: utf-8 -*-
"""Define checks integrated to the Django check framework
=====================================================

Currently, the check is build at settings loading time: any config value can add messages to `settings_check_results`.
"""

from django.core.checks import register

__author__ = 'Matthieu Gallet'

settings_check_results = []


# noinspection PyUnusedLocal
@register()
def settings_check(app_configs, **kwargs):
    return settings_check_results
