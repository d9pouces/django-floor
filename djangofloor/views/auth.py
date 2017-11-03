"""Views related to user authentication
====================================

"""
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.views import LogoutView, LoginView, PasswordResetView, PasswordChangeView

from djangofloor.decorators import validate_form, everyone

__author__ = 'Matthieu Gallet'
logger = logging.getLogger('django.requests')

validate_form(form_cls=UserCreationForm, path='djangofloor.validate.user_creation', is_allowed_to=everyone)
validate_form(form_cls=PasswordResetForm,
              path='djangofloor.validate.password_reset', is_allowed_to=everyone)


def login(request):
    """return the django.contrib.auth or the django-allauth login view"""
    if settings.USE_ALL_AUTH:
        from allauth.account.views import login
        return login(request)
    return LoginView.as_view()(request)


def logout(request):
    """return the django.contrib.auth or the django-allauth logout view"""
    if settings.USE_ALL_AUTH:
        from allauth.account.views import logout
        return logout(request)
    return LogoutView.as_view()(request)


def password_reset(request):
    """Display a password reset form"""
    if settings.USE_ALL_AUTH:
        from allauth.account.views import password_reset
        return password_reset(request)
    return PasswordResetView.as_view()(request)


@login_required(login_url='df:login')
def set_password(request):
    """Define a new password for the user"""
    if settings.USE_ALL_AUTH:
        from allauth.account.views import password_change
        return password_change(request)
    return PasswordChangeView.as_view()(request)
