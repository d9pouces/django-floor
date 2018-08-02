"""URLs specific to DjangoFloor
============================

Define URLs for user authentication forms and for defining JS signals.
Also define the URL linked to the monitoring and to the search views.
"""
from django.conf import settings
from django.conf.urls import url

from djangofloor.utils import get_view_from_string
from djangofloor.views import auth, signals, monitoring

__author__ = "Matthieu Gallet"


app_name = "djangofloor"
urlpatterns = [
    url(r"^logout/", auth.logout, name="logout"),
    url(r"^login/", auth.login, name="login"),
    url(r"^password_reset/", auth.password_reset, name="password_reset"),
    url(r"^password_change/", auth.set_password, name="set_password"),
    url(r"^signup/", auth.signup, name="signup"),
]

if settings.WEBSOCKET_URL:
    urlpatterns += [url(r"^signals.js$", signals, name="signals")]
if settings.DF_SYSTEM_CHECKS:
    urlpatterns += [
        url(r"^monitoring/system_state/", monitoring.system_state, name="system_state")
    ]
    urlpatterns += [
        url(
            r"^monitoring/exception/",
            monitoring.raise_exception,
            name="raise_exception",
        )
    ]
    urlpatterns += [
        url(r"^monitoring/log/", monitoring.generate_log, name="generate_log")
    ]
if settings.DF_SITE_SEARCH_VIEW:
    search_view = get_view_from_string(settings.DF_SITE_SEARCH_VIEW)
    urlpatterns += [url(r"^search/", search_view, name="site_search")]
