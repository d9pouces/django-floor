# coding=utf-8
"""define ContextProcessors.

The only ContextProcessor defined add some common variables related to DjangoFloor.

"""
from __future__ import unicode_literals, absolute_import
from django.conf import settings


__author__ = 'Matthieu Gallet'


def context_base(request):
    """Provide the following variables to templates when you RequestContext:
        * 'df_remote_authenticated': `True` if the user has been authenticated by :class:`djangofloor.middleware.RemoteUserMiddleware`.
        * 'df_project_name': name of your project, as defined in settings.FLOOR_PROJECT_NAME,
        * 'df_user': the user (:class:`django.contrib.auth.models.AbstractUser`),
        * 'df_language_code': settings.LANGUAGE_CODE (:class:`str`),
        * 'df_user_agent': the User Agent or '' if not defined in the request (:class:`str`),
        * 'df_index_view': the default view name (:class:`str`)

    :param request: a HTTP request
    :type request: :class:`django.http.HttpRequest`
    :return: a dict to update the global template context
    :rtype: :class:`dict`
    """
    return {
        'df_remote_authenticated': getattr(request, 'df_remote_authenticated', False),
        'df_project_name': settings.FLOOR_PROJECT_NAME,
        'df_user': request.user,
        'df_language_code': settings.LANGUAGE_CODE,
        'df_user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'df_index_view': settings.FLOOR_INDEX or 'djangofloor.views.index',
    }
