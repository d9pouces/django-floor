# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

import warnings

from djangofloor import views
from djangofloor.utils import RemovedInDjangoFloor110Warning

__author__ = 'Matthieu Gallet'


def signals(request):
    warnings.warn('"df/signals.js" URL is deprecated, replaced by the "df:signals" view.',
                  RemovedInDjangoFloor110Warning)
    return views.signals(request)


def signal_call(request, signal):
    warnings.warn('"df_signal_call" view is deprecated, replaced by the websocket-based signals.',
                  RemovedInDjangoFloor110Warning)
    return views.signal_call(request, signal)


def get_signal_calls(request):
    warnings.warn('"df_get_signal_calls" view is deprecated, replaced by the websocket-based signals.',
                  RemovedInDjangoFloor110Warning)
    return views.get_signal_calls(request)
