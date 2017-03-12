# -*- coding: utf-8 -*-

from django.core.checks import register

__author__ = 'Matthieu Gallet'

settings_check_results = []


# noinspection PyUnusedLocal
@register()
def settings_check(app_configs, **kwargs):
    return settings_check_results
