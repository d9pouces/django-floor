""".. deprecated:: 1.0"""
import warnings

from djangofloor.tasks import SESSION
from djangofloor.utils import RemovedInDjangoFloor200Warning

__author__ = "Matthieu Gallet"

warnings.warn(
    "djangofloor.df_redis module and its functions will be removed",
    RemovedInDjangoFloor200Warning,
)


# noinspection PyUnusedLocal
def push_signal_call(request, signal_name, kwargs, sharing=SESSION):
    pass


# noinspection PyUnusedLocal
def fetch_signal_calls(request):
    return []
