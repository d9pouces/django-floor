"""Views related to user authentication
====================================

"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, UsernameField
from django.contrib.auth.views import LogoutView, LoginView, PasswordResetView, PasswordChangeView
from django.http import HttpResponseRedirect
from django.views.decorators.cache import never_cache

from djangofloor.decorators import validate_form, everyone

__author__ = 'Matthieu Gallet'
logger = logging.getLogger('django.requests')

validate_form(form_cls=UserCreationForm, path='djangofloor.validate.user_creation', is_allowed_to=everyone)
validate_form(form_cls=PasswordResetForm,
              path='djangofloor.validate.password_reset', is_allowed_to=everyone)


class EmailUserCreationForm(UserCreationForm):

    class Meta:
        model = get_user_model()
        fields = ("username", "email")
        field_classes = {'username': UsernameField}


class SignupView(LoginView):
    form_class = EmailUserCreationForm
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        """Security check complete. Create the user and log it in."""
        if settings.DF_ALLOW_USER_CREATION and settings.DF_ALLOW_LOCAL_USERS:
            user = form.save()
            auth_login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = {'initial': self.get_initial(), 'prefix': self.get_prefix()}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({'data': self.request.POST, 'files': self.request.FILES})
        return kwargs


@never_cache
def login(request):
    """return the django.contrib.auth or the django-allauth login view"""
    if settings.USE_ALL_AUTH:
        # noinspection PyPackageRequirements
        from allauth.account.views import login
        return login(request)
    return LoginView.as_view()(request)


@never_cache
def signup(request):
    """return the django.contrib.auth or the django-allauth login view"""
    if settings.USE_ALL_AUTH:
        # noinspection PyPackageRequirements
        from allauth.account.views import signup
        return signup(request)
    return SignupView.as_view()(request)


@never_cache
def logout(request):
    """return the django.contrib.auth or the django-allauth logout view"""
    if settings.USE_ALL_AUTH:
        # noinspection PyPackageRequirements
        from allauth.account.views import logout
        return logout(request)
    return LogoutView.as_view()(request)


@never_cache
def password_reset(request):
    """Display a password reset form"""
    if settings.USE_ALL_AUTH:
        # noinspection PyPackageRequirements
        from allauth.account.views import password_reset
        return password_reset(request)
    return PasswordResetView.as_view()(request)


@never_cache
@login_required(login_url='df:login')
def set_password(request):
    """Define a new password for the user"""
    if settings.USE_ALL_AUTH:
        # noinspection PyPackageRequirements
        from allauth.account.views import password_change
        return password_change(request)
    return PasswordChangeView.as_view()(request)
