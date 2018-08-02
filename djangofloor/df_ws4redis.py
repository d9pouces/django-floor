""".. deprecated:: 1.0"""
import warnings

from django.contrib.auth import get_user_model
from django.utils.lru_cache import lru_cache

from djangofloor.tasks import SESSION, WINDOW, BROADCAST, USER, call
from djangofloor.utils import RemovedInDjangoFloor200Warning
from djangofloor.wsgi.window_info import WindowInfo, Session

__author__ = "Matthieu Gallet"


@lru_cache()
def get_pk(kind, value):
    if kind == "user":
        return get_user_model().objects.get(username=value).pk


warnings.warn(
    "djangofloor.df_ws4redis module and its functions will be removed",
    RemovedInDjangoFloor200Warning,
)


def ws_call(signal_name, request, sharing, kwargs):
    if isinstance(sharing, bytes):
        sharing = str(sharing)
    to = _sharing_to_topics(request, sharing)
    window_info = WindowInfo.from_request(request)
    call(window_info, signal_name, to=to, kwargs=kwargs)


def _sharing_to_topics(request, sharing):
    to = []
    if sharing == SESSION:
        to = [Session(request.session_key)]
    elif sharing == WINDOW:
        to = [WINDOW]
    elif sharing == USER:
        to = [USER]
    elif sharing == BROADCAST:
        to = [BROADCAST]
    if BROADCAST in sharing:
        to = [BROADCAST]
    else:
        for username in sharing.get(USER, []):
            to.append(get_pk("user", username))
        for session in sharing.get(SESSION, []):
            to.append(Session(session))
    return to
