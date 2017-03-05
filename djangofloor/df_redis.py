# -*- coding: utf-8 -*-
""".. deprecated:: 1.0"""
from __future__ import unicode_literals, print_function, absolute_import

import warnings

from djangofloor.utils import RemovedInDjangoFloor110Warning

from djangofloor.tasks import SESSION

__author__ = 'Matthieu Gallet'

warnings.warn('djangofloor.df_redis module and its functions will be removed', RemovedInDjangoFloor110Warning)


# noinspection PyUnusedLocal
def push_signal_call(request, signal_name, kwargs, sharing=SESSION):
    pass


# noinspection PyUnusedLocal
def fetch_signal_calls(request):
    return []
