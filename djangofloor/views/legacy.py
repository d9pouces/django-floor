import warnings

from djangofloor import views
from djangofloor.utils import RemovedInDjangoFloor200Warning

__author__ = 'Matthieu Gallet'


def signals(request):
    warnings.warn('"df/signals.js" URL is deprecated, replaced by the "df:signals" view.',
                  RemovedInDjangoFloor200Warning)
    return views.signals(request)


def signal_call(request, signal):
    warnings.warn('"df_signal_call" view is deprecated, replaced by the websocket-based signals.',
                  RemovedInDjangoFloor200Warning)
    return views.signal_call(request, signal)


def get_signal_calls(request):
    warnings.warn('"df_get_signal_calls" view is deprecated, replaced by the websocket-based signals.',
                  RemovedInDjangoFloor200Warning)
    return views.get_signal_calls(request)
