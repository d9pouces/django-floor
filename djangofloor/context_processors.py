"""DjangoFloor's specific context processors
=========================================

Add some values to the template context, related to:

  * (enabled or disabled) default views provided by DjangoFloor,
  * notification objects,
  * authentication provided by HTTP headers,
  * websockets

"""
import warnings

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from djangofloor.models import Notification
from djangofloor.utils import RemovedInDjangoFloor200Warning

__author__ = 'Matthieu Gallet'


def context_base(request):
    """Provide the following variables to templates when you RequestContext:

        * `df_has_index_view`: True if an default index view is included
        * `df_has_monitoring_view`: True if the monitoring view is included
        * `df_has_site_search_view`: True if a site-wide search view is provided
        * `df_project_name`: name of your project
        * `df_remote_username`: username provided by a HTTP header
        * `df_remote_authenticated`: True if the user authenticated by a HTTP header
        * `df_get_notifications`: when used, return the list of Notifications of the user
        * `df_user_agent`: user agent provided by the HttpRequest
        * `df_window_key`: a random value provided by each HttpRequest (allowing to identify each browser window)
        * `df_has_ws_topics`: True if some websockets topics are provided to the HttpRequest

    :param request: a HTTP request
    :type request: :class:`django.http.HttpRequest`
    :return: a dict to update the global template context
    :rtype: :class:`dict`
    """

    def df_language_code():
        warnings.warn('"df_language_code" template value will be removed, use "LANGUAGE_CODE" (provided by '
                      '"django.template.context_processors.i18n") instead.', RemovedInDjangoFloor200Warning)
        return settings.LANGUAGE_CODE

    def df_user():
        warnings.warn('"df_user" template value will be removed, use "user" (provided by '
                      '"django.contrib.auth.context_processors.auth") instead.', RemovedInDjangoFloor200Warning)
        return getattr(request, 'user', AnonymousUser())

    return {
        'df_has_index_view': bool(settings.DF_INDEX_VIEW),
        'df_has_monitoring_view': bool(settings.DF_SYSTEM_CHECKS),
        'df_has_site_search_view': bool(settings.DF_SITE_SEARCH_VIEW),
        'df_project_name': settings.DF_PROJECT_NAME,
        'df_remote_username': getattr(request, 'remote_username', None),
        'df_remote_authenticated': bool(getattr(request, 'remote_username', None)),
        'df_user_can_register': settings.DF_ALLOW_USER_CREATION and settings.DF_ALLOW_LOCAL_USERS,
        'df_allow_local_users': settings.DF_ALLOW_LOCAL_USERS,
        'df_get_notifications': lambda: Notification.get_notifications(request),
        'df_user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'df_window_key': getattr(request, 'window_key', None),
        'df_session_id': request.COOKIES.get(settings.SESSION_COOKIE_NAME),
        'df_has_ws_topics': getattr(request, 'has_websocket_topics', False),
        'df_http_request': request,
        'df_user': df_user,
        'df_language_code': df_language_code,
    }
