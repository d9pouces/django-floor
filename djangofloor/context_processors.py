# coding=utf-8
from __future__ import unicode_literals, absolute_import
from django.conf import settings


__author__ = 'flanker'


def context_base(request):
    return {
        'df_remote_authenticated': getattr(request, 'df_remote_authenticated', False),
        'df_project_name': settings.FLOOR_PROJECT_NAME,
        'df_user': request.user,
        'df_language_code': settings.LANGUAGE_CODE,
        'df_user_agent': request.META.get('HTTP_USER_AGENT', ''),
    }
