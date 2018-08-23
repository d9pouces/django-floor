"""HttpRequest and WindowInfo middlewares
======================================

Two kinds of middlewares are provided:

  * standard Django middleware,
  * middlewares for populating :class:`djangofloor.wsgi.window_info.WindowInfo`

The :class:`DjangoFloorMiddleware` provides several things:

  * authenticates users with the `settings.DF_REMOTE_USER_HEADER` HTTP header,
  * generates a unique ID and add it to the :class:`django.http.request.HttpRequest`,
  * add the 'X-UA-Compatible' header to the response,
  * if `settings.DF_FAKE_AUTHENTICATION_USERNAME` and the `settings.DEBUG` are set, a username is set, for simplifying
    debug sessions,
  * overrides the 'REMOTE_ADDR' META attribute since your project is assumed to be run behind a reverse proxy,
  * if the `HTTP_AUTHORIZATION` header is set, use it for authenticating users (HTTP basic auth)

The class :class:`WindowInfoMiddleware` allows to:

  * populate a new :class:`djangofloor.wsgi.window_info.WindowInfo` from a :class:`django.http.request.HttpRequest`,
  * serialize a :class:`djangofloor.wsgi.window_info.WindowInfo` to a dict,
  * populate a new :class:`djangofloor.wsgi.window_info.WindowInfo` from a dict,,
  * populate a template context from a :class:`djangofloor.wsgi.window_info.WindowInfo` object,
  * build an empty :class:`djangofloor.wsgi.window_info.WindowInfo`,
  * install new methods to the :class:`djangofloor.wsgi.window_info.WindowInfo` class.

"""
import base64
import logging
import warnings

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.context_processors import PermWrapper
from django.contrib.auth.middleware import (
    RemoteUserMiddleware as BaseRemoteUserMiddleware
)
from django.contrib.auth.models import Group, AnonymousUser
from django.contrib.messages import DEFAULT_LEVELS
from django.contrib.sessions.backends.base import VALID_KEY_CHARS
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.http import HttpRequest
from django.utils import translation
from django.utils.crypto import get_random_string
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import get_language_from_request

from djangofloor.utils import RemovedInDjangoFloor200Warning

__author__ = "Matthieu Gallet"
logger = logging.getLogger("django.request")


# noinspection PyClassHasNoInit
class DjangoFloorMiddleware(BaseRemoteUserMiddleware):
    """Like :class:`django.contrib.auth.middleware.RemoteUserMiddleware` but:

    * can use any header defined by the setting `DF_REMOTE_USER_HEADER`,
    * handle the HTTP_X_FORWARDED_FOR HTTP header (set the right client IP)
    * handle HTTP basic authentication
    * set response header for Internet Explorer (to use its most recent render engine)
    """

    header = settings.DF_REMOTE_USER_HEADER
    ajax_header = "HTTP_%s" % settings.WEBSOCKET_HEADER
    if header:
        header = header.upper().replace("-", "_")

    # noinspection PyMethodMayBeStatic
    def process_request(self, request: HttpRequest):
        request.window_key = get_random_string(32, VALID_KEY_CHARS)
        if request.is_ajax() and self.ajax_header in request.META:
            from djangofloor.wsgi.wsgi_server import signer

            signed_token = request.META[self.ajax_header]
            request.window_key = signer.unsign(signed_token)
        request.has_websocket_topics = False
        request.remote_username = None

        if settings.USE_X_FORWARDED_FOR and "HTTP_X_FORWARDED_FOR" in request.META:
            request.META["REMOTE_ADDR"] = (
                request.META["HTTP_X_FORWARDED_FOR"].split(",")[0].strip()
            )

        if settings.USE_HTTP_BASIC_AUTH and "HTTP_AUTHORIZATION" in request.META:
            authentication = request.META["HTTP_AUTHORIZATION"]
            authmeth, sep, auth_data = authentication.partition(" ")
            if sep == " " and authmeth.lower() == "basic":
                auth_data = base64.b64decode(auth_data.strip()).decode("utf-8")
                username, password = auth_data.split(":", 1)
                user = auth.authenticate(username=username, password=password)
                if user:
                    request.user = user
                    auth.login(request, user)
        # noinspection PyTypeChecker
        username = getattr(settings, "DF_FAKE_AUTHENTICATION_USERNAME", None)
        if username and settings.DEBUG:
            remote_addr = request.META.get("REMOTE_ADDR")
            if remote_addr in settings.INTERNAL_IPS:
                request.META[self.header] = username
            elif remote_addr:
                logger.warning(
                    "Unable to use `settings.DF_FAKE_AUTHENTICATION_USERNAME`. "
                    "You should add %s to the list `settings.INTERNAL_IPS`."
                    % remote_addr
                )

        if self.header and self.header in request.META:
            remote_username = request.META.get(self.header)
            if (
                not remote_username or remote_username == "(null)"
            ):  # special case due to apache2+auth_mod_kerb :-(
                return
            remote_username = self.format_remote_username(remote_username)
            # noinspection PyTypeChecker
            self.remote_user_authentication(request, remote_username)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def process_response(self, request, response):
        response["X-UA-Compatible"] = "IE=edge,chrome=1"
        return response

    def remote_user_authentication(self, request, username):
        # AuthenticationMiddleware is required so that request.user exists.
        # noinspection PyTypeChecker
        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class."
            )
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated:
            cleaned_username = self.clean_username(username, request)
            if request.user.get_username() == cleaned_username:
                request.remote_username = cleaned_username
                return
            else:
                self._remove_invalid_user(request)
        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(remote_user=username)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)
            request.remote_username = user.username

    # noinspection PyMethodMayBeStatic
    def format_remote_username(self, remote_username):
        return remote_username.partition("@")[0]


class WindowInfoMiddleware:
    """Base class for the WindowInfo middlewares."""

    def from_request(self, request, window_info):
        pass

    def new_window_info(self, window_info):
        pass

    def to_dict(self, window_info):
        return {}

    def from_dict(self, window_info, values):
        pass

    def get_context(self, window_info):
        return {}

    def install_methods(self, window_info_cls):
        pass


class WindowKeyMiddleware(WindowInfoMiddleware):
    """handle the unique ID generated for each :class:`django.http.request.HttpRequest` and copy
    it to the :class:`WindowInfo` object"""

    def from_request(self, request, window_info):
        # noinspection PyTypeChecker
        window_info.window_key = getattr(request, "window_key", None)

    def new_window_info(self, window_info):
        window_info.window_key = None

    def to_dict(self, window_info):
        return {"window_key": window_info.window_key}

    def from_dict(self, window_info, values):
        window_info.window_key = values.get("window_key")

    def get_context(self, window_info):
        # noinspection PyTypeChecker
        return {"df_window_key": getattr(window_info, "window_key")}


class DjangoAuthMiddleware(WindowInfoMiddleware):
    """handle attributes related to the :mod:`django.contrib.auth` framework"""

    def from_request(self, request, window_info):
        assert isinstance(request, HttpRequest)
        # auth and perms part
        # noinspection PyTypeChecker
        user = getattr(request, "user", None)
        window_info._user = user
        window_info._perms = None
        window_info._template_perms = None
        window_info.user_agent = request.META.get("HTTP_USER_AGENT", "")
        window_info.csrf_cookie = request.META.get("CSRF_COOKIE", "")
        if user and user.is_authenticated:
            window_info.user_pk = user.pk
            window_info.username = user.get_username()
            window_info.is_superuser = user.is_superuser
            window_info.is_staff = user.is_staff
            window_info.is_active = user.is_active
        else:
            window_info.user_pk = None
            window_info.username = None
            window_info.is_superuser = False
            window_info.is_staff = False
            window_info.is_active = False

    def new_window_info(self, window_info):
        window_info._user = None
        window_info._perms = None
        window_info._template_perms = None
        window_info.user_agent = ""
        window_info.user_pk = None
        window_info.username = None
        window_info.is_superuser = False
        window_info.is_staff = False
        window_info.is_active = False
        window_info.csrf_cookie = ""

    def to_dict(self, window_info):
        # noinspection PyProtectedMember
        return {
            "user_pk": window_info.user_pk,
            "username": window_info.username,
            "is_superuser": window_info.is_superuser,
            "is_staff": window_info.is_staff,
            "is_active": window_info.is_active,
            "csrf_cookie": window_info.csrf_cookie,
            "perms": list(window_info._perms)
            if isinstance(window_info._perms, set)
            else None,
            "user_agent": window_info.user_agent,
        }

    def from_dict(self, window_info, values):
        window_info._user = None
        window_info.csrf_cookie = values.get("csrf_cookie")
        window_info.user_pk = values.get("user_pk")
        window_info.username = values.get("username")
        window_info.is_superuser = values.get("is_superuser")
        window_info.is_staff = values.get("is_staff")
        window_info.is_active = values.get("is_active")
        window_info.is_authenticated = bool(window_info.user_pk)
        window_info.is_anonymous = not bool(window_info.user_pk)
        window_info._perms = (
            set(values["perms"]) if values.get("perms") is not None else None
        )
        window_info._template_perms = None
        window_info.user_agent = values.get("user_agent")

    def get_context(self, window_info):
        """provide the same context data as the :mod:`django.contrib.auth.context_processors`:

         * `user`: a user or :class:`django.contrib.auth.models.AnonymousUser`
         * `perms`, with the same meaning
        """
        user = window_info.user or AnonymousUser()
        return {"user": user, "perms": PermWrapper(user)}

    def install_methods(self, window_info_cls):
        def get_user(req):
            """return the user object if authenticated, else return `None`"""
            # noinspection PyProtectedMember
            if req._user or req.user_pk is None:
                # noinspection PyProtectedMember
                return req._user
            users = list(get_user_model().objects.filter(pk=req.user_pk)[0:1])
            if users:
                req._user = users[0]
                return req._user
            return None

        def has_perm(req, perm):
            """ return true is the user has the required perm.

            >>> from djangofloor.wsgi.window_info import WindowInfo
            >>> r = WindowInfo.from_dict({'username': 'username', 'perms':['app_label.codename']})
            >>> r.has_perm('app_label.codename')
            True

            :param req: WindowInfo
            :param perm: name of the permission  ("app_label.codename")
            :return: True if the user has the required perm
            :rtype: :class:`bool`
            """
            return perm in req.perms

        def get_perms(req):
            """:class:`set` of all perms of the user (set of "app_label.codename")"""
            if not req.user_pk:
                return set()
            elif req._perms is not None:
                return req._perms
            from django.contrib.auth.models import Permission

            if req.is_superuser:
                query = Permission.objects.all()
            else:
                query = Permission.objects.filter(
                    Q(user__pk=req.user_pk) | Q(group__user__pk=req.user_pk)
                )
            req._perms = set(
                "%s.%s" % p
                for p in query.select_related("content_type").values_list(
                    "content_type__app_label", "codename"
                )
            )
            return req._perms

        window_info_cls.user = property(get_user)
        window_info_cls.has_perm = has_perm
        window_info_cls.perms = property(get_perms)


class BrowserMiddleware(WindowInfoMiddleware):
    """add attributes related to the browser (currently only the HTTP_USER_AGENT header)"""

    def from_request(self, request, window_info):
        window_info.user_agent = request.META.get("HTTP_USER_AGENT", "")

    def new_window_info(self, window_info):
        window_info.user_agent = ""

    def to_dict(self, window_info):
        return {"user_agent": window_info.user_agent}

    def from_dict(self, window_info, values):
        window_info.user_agent = values.get("user_agent", "")

    def get_context(self, window_info):
        return {
            "df_user_agent": window_info.user_agent,
            "messages": [],
            "DEFAULT_MESSAGE_LEVELS": DEFAULT_LEVELS,
        }


class Djangoi18nMiddleware(WindowInfoMiddleware):
    """Add attributes required for using i18n-related functions."""

    def from_request(self, request, window_info):
        # noinspection PyTypeChecker
        if getattr(request, "session", None):
            window_info.language_code = get_language_from_request(request)
        else:
            window_info.language_code = settings.LANGUAGE_CODE

    def new_window_info(self, window_info):
        window_info.language_code = None

    def to_dict(self, window_info):
        return {"language_code": window_info.language_code}

    def from_dict(self, window_info, values):
        window_info.language_code = values.get("language_code")

    def get_context(self, window_info):
        return {
            "LANGUAGES": settings.LANGUAGES,
            "LANGUAGE_CODE": window_info.language_code,
            "LANGUAGE_BIDI": translation.get_language_bidi(),
        }


# TODO remove these classes
class IEMiddleware(MiddlewareMixin):
    """.. deprecated:: 1.0  replaced by :class:`djangofloor.middleware.DjangoFloorMiddleware`"""

    def __init__(self, get_response=None):
        super().__init__(get_response=get_response)
        warnings.warn(
            "djangofloor.middleware.IEMiddleware has been replaced by "
            "djangofloor.middleware.DjangoFloorMiddleware",
            RemovedInDjangoFloor200Warning,
        )

    # noinspection PyMethodMayBeStatic
    def process_request(self, request):
        request.window_key = get_random_string(32, VALID_KEY_CHARS)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def process_template_response(self, request, response):
        response["X-UA-Compatible"] = "IE=edge,chrome=1"
        return response


class RemoteUserMiddleware(BaseRemoteUserMiddleware):
    """Deprecated class, replaced by :class:`djangofloor.middleware.DjangoFloorMiddleware`"""

    def __init__(self, get_response=None):
        super().__init__(get_response=get_response)
        warnings.warn(
            "djangofloor.middleware.RemoteUserMiddleware has been replaced by "
            "djangofloor.middleware.DjangoFloorMiddleware",
            RemovedInDjangoFloor200Warning,
        )

    header = settings.DF_REMOTE_USER_HEADER

    def process_request(self, request):
        request.df_remote_authenticated = False
        if self.header and self.header in request.META:
            if not request.user.is_authenticated:
                self.original_process_request(request)
            request.df_remote_authenticated = request.user.is_authenticated

    def original_process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class."
            )
        username = request.META.get(self.header)
        if not username or username == "(null)":  # special case caused by Apache :-(
            return
        username, sep, domain = username.partition("@")
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated:
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


class FakeAuthenticationMiddleware(MiddlewareMixin):
    """Deprecated class, replaced by :class:`djangofloor.middleware.DjangoFloorMiddleware`
    """

    def __init__(self, get_response=None):
        super().__init__(get_response=get_response)
        warnings.warn(
            "djangofloor.middleware.FakeAuthenticationMiddleware has been replaced by "
            "djangofloor.middleware.DjangoFloorMiddleware",
            RemovedInDjangoFloor200Warning,
        )

    group_cache = {}

    # noinspection PyMethodMayBeStatic
    def process_request(self, request):
        username = settings.DF_FAKE_AUTHENTICATION_USERNAME
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


class BasicAuthMiddleware(MiddlewareMixin):
    """Deprecated class, replaced by :class:`djangofloor.middleware.DjangoFloorMiddleware`
    """

    def __init__(self, get_response=None):
        super().__init__(get_response=get_response)
        warnings.warn(
            "djangofloor.middleware.BasicAuthMiddleware has been replaced by "
            "djangofloor.middleware.DjangoFloorMiddleware",
            RemovedInDjangoFloor200Warning,
        )

    # noinspection PyMethodMayBeStatic
    def process_request(self, request):
        if "HTTP_AUTHORIZATION" in request.META:
            authentication = request.META["HTTP_AUTHORIZATION"]
            authmeth, sep, auth_data = authentication.partition(" ")
            if sep == " " and authmeth.lower() == "basic":
                auth_data = base64.b64decode(auth_data.strip()).decode("utf-8")
                username, password = auth_data.split(":", 1)
                user = auth.authenticate(username=username, password=password)
                if user:
                    request.user = user
                    auth.login(request, user)
