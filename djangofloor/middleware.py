# coding=utf-8
"""Several middleware, for production or debugging purposes
========================================================

"""
from __future__ import unicode_literals
import codecs
from django.contrib.sessions.backends.base import VALID_KEY_CHARS
from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import get_random_string
# noinspection PyPackageRequirements
from pipeline.compilers import CompilerBase
import base64
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.middleware import RemoteUserMiddleware as BaseRemoteUserMiddleware
from django.contrib.auth.models import Group
# noinspection PyPackageRequirements
from pipeline.compressors import CompressorBase
from djangofloor.df_pipeline import cssmin

__author__ = 'Matthieu Gallet'


class IEMiddleware(object):
    """required for signals tight to a window
    Add a HTTP header for Internet Explorer Compatibility.
    Ensure that IE uses the last version of its display engine.
    """
    # noinspection PyMethodMayBeStatic
    def process_request(self, request):
        request.window_key = get_random_string(32, VALID_KEY_CHARS)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def process_template_response(self, request, response):
        response['X-UA-Compatible'] = 'IE=edge,chrome=1'
        return response


class RemoteUserMiddleware(BaseRemoteUserMiddleware):
    """Like :class:`django.contrib.auth.middleware.RemoteUserMiddleware` but:

    * can use any header defined by the setting `FLOOR_AUTHENTICATION_HEADER`,
    * add a `df_remote_authenticated` attribute to the request (`True` if the user has been authenticated via the header)
    """
    header = settings.FLOOR_AUTHENTICATION_HEADER

    def process_request(self, request):
        request.df_remote_authenticated = False
        if request.META['REMOTE_ADDR'] in settings.REVERSE_PROXY_IPS and self.header and self.header in request.META:
            if not request.user.is_authenticated():
                self.original_process_request(request)
            request.df_remote_authenticated = request.user.is_authenticated()

    def original_process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class.")
        if self.header not in request.META:
            return
        username = request.META[self.header]
        username, sep, domain = username.partition('@')
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated():
            if request.user.get_username() == self.clean_username(username, request):
                return
            else:
                # An authenticated user is associated with the request, but
                # it does not match the authorized user in the header.
                self._remove_invalid_user(request)

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(remote_user=username)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)


class FakeAuthenticationMiddleware(object):
    """ Only for dev/debugging purpose: emulate a user authenticated by the remote proxy.

    Use `settings.FLOOR_FAKE_AUTHENTICATION_USERNAME` to create (if needed) a user and authenticate the request.
    Only works in `settings.DEBUG` mode and if `settings.FLOOR_FAKE_AUTHENTICATION_USERNAME` is set.
    """
    group_cache = {}

    # noinspection PyMethodMayBeStatic
    def process_request(self, request):
        username = settings.FLOOR_FAKE_AUTHENTICATION_USERNAME
        if not settings.DEBUG or not username:
            return
        user = auth.authenticate(remote_user=username)
        if user:
            request.user = user
            auth.login(request, user)
            request.df_remote_authenticated = True
            if settings.FLOOR_FAKE_AUTHENTICATION_GROUPS:
                for group_name in settings.FLOOR_FAKE_AUTHENTICATION_GROUPS:
                    if group_name not in self.group_cache:
                        group, created = Group.objects.get_or_create(name=group_name)
                        self.group_cache[group_name] = group
                    else:
                        group = self.group_cache[group_name]
                    user.groups.add(group)


class BasicAuthMiddleware(object):
    """Basic HTTP authentication using Django users to check passwords.
    """

    # noinspection PyMethodMayBeStatic
    def process_request(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            authentication = request.META['HTTP_AUTHORIZATION']
            (authmeth, auth_data) = authentication.split(' ', 1)
            if 'basic' == authmeth.lower():
                auth_data = base64.b64decode(auth_data.strip()).decode('utf-8')
                username, password = auth_data.split(':', 1)
                user = auth.authenticate(username=username, password=password)
                if user:
                    request.user = user
                    auth.login(request, user)


# noinspection PyAbstractClass
class RCSSMinCompressor(CompressorBase):

    @staticmethod
    def compress_css(css):
        return cssmin(css)


class PyScssCompiler(CompilerBase):
    output_extension = 'css'

    def match_file(self, filename):
        return filename.endswith('.scss')

    def compile_file(self, infile, outfile, outdated=False, force=False):
        # noinspection PyPackageRequirements
        import scss.compiler
        """Define your middlewares here"""
        if not outdated and not force:
            return  # No need to recompiled file
        result = scss.compiler.compile_file(infile)
        with codecs.open(outfile, 'w', encoding='utf-8') as fd:
            fd.write(result)
