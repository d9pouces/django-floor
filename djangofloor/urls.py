"""URLs specific to DjangoFloor
============================

Define URLs for user authentication forms and for defining JS signals.
Also define the URL linked to the monitoring and to the search views.
"""
from django.conf import settings
from django.urls import re_path

from djangofloor.utils import get_view_from_string
from djangofloor.views import auth, signals, monitoring

__author__ = "Matthieu Gallet"


app_name = "djangofloor"
urlpatterns = [
    re_path(r"^logout/", auth.logout, name="logout"),
    re_path(r"^login/", auth.login, name="login"),
    re_path(r"^password_reset/", auth.password_reset, name="password_reset"),
    re_path(r"^password_change/", auth.set_password, name="set_password"),
    re_path(r"^signup/", auth.signup, name="signup"),
]

if settings.WEBSOCKET_URL:
    urlpatterns += [re_path(r"^signals.js$", signals, name="signals")]
if settings.DF_SYSTEM_CHECKS:
    urlpatterns += [
        re_path(r"^monitoring/system_state/", monitoring.system_state, name="system_state")
    ]
    urlpatterns += [
        re_path(
            r"^monitoring/exception/",
            monitoring.raise_exception,
            name="raise_exception",
        )
    ]
    urlpatterns += [
        re_path(r"^monitoring/log/", monitoring.generate_log, name="generate_log")
    ]
if settings.DF_SITE_SEARCH_VIEW:
    search_view = get_view_from_string(settings.DF_SITE_SEARCH_VIEW)
    urlpatterns += [re_path(r"^search/", search_view, name="site_search")]
