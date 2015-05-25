# coding=utf-8
from __future__ import unicode_literals, absolute_import
import logging
import re
from django.contrib.auth.models import Permission
from django.db.models import Q

from django.http import QueryDict


try:
    from inspect import signature
except ImportError:
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    from funcsigs import signature
from django import forms
from django.utils.translation import ugettext as _

from djangofloor.exceptions import InvalidRequest


__author__ = 'flanker'
REGISTERED_SIGNALS = {}
logger = logging.getLogger('djangofloor.request')


class RE(object):
    def __init__(self, value, caster=None):
        self.caster = caster
        self.regexp = re.compile(value)

    def __call__(self, value):
        matcher = self.regexp.match(value)
        if not matcher:
            raise ValueError
        value = matcher.group(1) if matcher.groups() else value
        return self.caster(value) if self.caster else value


class Choice(object):
    def __init__(self, values, caster=None):
        self.values = set(values)
        self.caster = caster

    def __call__(self, value):
        value = self.caster(value) if self.caster else value
        if value not in self.values:
            raise ValueError
        return value


class SerializedForm(object):
    """given a form and a `list` of `dict`, transforms the `dict` into a :class:`django.http.QueryDict` and initialize the form with it.

>>> class SimpleForm(forms.Form):
...    field = forms.CharField()
...
>>> x = SerializedForm(SimpleForm)
>>> form = x([{'field': 'object'}])
>>> form.is_valid()
True


    """

    def __init__(self, form_cls):
        self.form_cls = form_cls

    def __call__(self, value):
        """
        :param value:
        :type value: :class:`list` of :class:`dict`
        :return:
        :rtype: :class:`django.forms.Form`
        """
        query_dict = QueryDict('', mutable=True)
        for obj in value:
            query_dict.update({obj['name']: obj['value']})
        return self.form_cls(query_dict)


class SignalRequest(object):
    """ Store the username and the session key and must be supplied to any Python signal call.
    Can be constructed from a plain :class:`django.http.HttpRequest`.
    """
    def __init__(self, username, session_key, user_pk=None, is_superuser=False, is_staff=False, is_active=False, perms=None):
        self.username = username
        self.session_key = session_key
        self.user_pk = user_pk
        self.is_superuser = is_superuser
        self.is_staff = is_staff
        self.is_active = is_active
        self._perms = perms
        self._template_perms = None

    @classmethod
    def from_user(cls, user):
        return cls(user.get_username(), None, user_pk=user.pk, is_superuser=user.is_superuser, is_staff=user.is_staff,
                   is_active=user.is_active)

    def to_dict(self):
        result = {}
        result.update(self.__dict__)
        if isinstance(self._perms, set):
            result['perms'] = list(self._perms)
        else:
            result['perms'] = None
        del result['_perms']
        del result['_template_perms']
        return result

    def has_perm(self, perm):
        return perm in self.perms

    @property
    def perms(self):
        if not self.user_pk:
            return set()
        elif self._perms is not None:
            return self._perms
        if self.is_superuser:
            query = Permission.objects.all()
        else:
            query = Permission.objects.filter(Q(user__pk=self.user_pk) | Q(group__user__pk=self.user_pk))
        self._perms = {'%s.%s' % p for p in
                       query.select_related('content_type').values_list('content_type__app_label', 'codename')}
        return self._perms

    @property
    def template_perms(self):
        if self._template_perms is None:
            result = {}
            for perm in self.perms:
                app_name, sep, codename = perm.partition('.')
                result.setdefault(app_name, {})[codename] = True
            self._template_perms = result
        return self._template_perms

    @classmethod
    def from_request(cls, request):
        """ return a `SignalRequest` from a Django request
        :param request: standard Django request
        :type request: :class:`django.http.HttpRequest` or :class:`SignalRequest`
        :return:
        :rtype: :class:`djangofloor.decorators.SignalRequest`
        """
        if isinstance(request, SignalRequest):
            return request
        session_key = request.session.session_key if request.session else None
        user = request.user
        if user.is_authenticated():
            return cls(username=user.get_username(), session_key=session_key,
                       user_pk=user.pk, is_superuser=user.is_superuser, is_staff=user.is_staff, is_active=user.is_active)
        return cls(None, session_key)


class CallWrapper(object):
    def __init__(self, fn, path=None):
        self.path = path
        self.function = fn
        self.__name__ = fn.__name__ if hasattr(fn, '__name__') else path

        # fetch signature to analyze arguments
        sig = signature(fn)
        self.required_arguments = []
        self.optional_arguments = []
        self.accept_kwargs = []
        self.argument_types = {}

        for key, param in sig.parameters.items():
            if key in ('request',):
                continue
            if param.kind == param.VAR_KEYWORD:  # corresponds to "fn(**kwargs)"
                self.accept_kwargs = True
            elif param.kind == param.VAR_POSITIONAL:  # corresponds to "fn(*args)"
                self.accept_kwargs = True
            elif param.default == param.empty:  # "fn(foo)" : kind = POSITIONAL_ONLY or POSITIONAL_OR_KEYWORD
                self.required_arguments.append(key)
                if param.annotation != param.empty and callable(param.annotation):
                    self.argument_types[key] = param.annotation
            else:
                self.optional_arguments.append(key)  # "fn(foo=bar)" : kind = POSITIONAL_OR_KEYWORD or KEYWORD_ONLY
                if param.annotation != param.empty and callable(param.annotation):
                    self.argument_types[key] = param.annotation

        if path is None:
            path = fn.__name__
        self.register(path)

    def register(self, path):
        raise NotImplementedError

    def prepare_kwargs(self, kwargs):
        logger.debug(self.path, kwargs)
        kwargs = {x: y for (x, y) in kwargs.items()}
        if not self.accept_kwargs:
            for arg_name in kwargs:
                if arg_name not in self.required_arguments and arg_name not in self.optional_arguments:
                    raise InvalidRequest(_('Unexpected argument: %(arg)s') % {'arg': arg_name})
        for arg_name in self.required_arguments:
            if arg_name not in kwargs:
                raise InvalidRequest(_('Required argument: %(arg)s') % {'arg': arg_name})
        for k, v in self.argument_types.items():
            try:
                if k in kwargs:
                    kwargs[k] = v(kwargs[k])
            except ValueError:
                raise InvalidRequest(_('Invalid value %(value)s for argument %(arg)s.') % {'arg': 'k', 'value': v})
        return kwargs

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


class RedisCallWrapper(CallWrapper):
    def __init__(self, fn, path=None, delayed=False, allow_from_client=True, auth_required=True):
        super(RedisCallWrapper, self).__init__(fn, path=path)
        self.allow_from_client = allow_from_client
        self.delayed = delayed
        self.auth_required = auth_required

    def register(self, path):
        REGISTERED_SIGNALS.setdefault(path, []).append(self)


def connect(fn=None, path=None, delayed=False, allow_from_client=True, auth_required=True):
    wrapped = lambda fn_: RedisCallWrapper(fn_, path=path, delayed=delayed, allow_from_client=allow_from_client, auth_required=auth_required)
    if fn is not None:
        wrapped = wrapped(fn)
    return wrapped
