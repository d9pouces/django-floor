# coding=utf-8
"""Define the decorator for connecting Python code to signals, a `SignalRequest` which can be easily serialized and is lighter than a `django.http.HttpRequest`, and some helping code to convert serialized data sent by Javascript to something useful in Python.

Usage of the decorator
**********************

The decorator `connect` let you connect any Python function to a signal (which is only a text string).
Signals are automatically discovered, as soon as there are in files `signals.py` in any app listed in the setting `INSTALLED_APPS` (like `admin.py` or `models.py`).

To use this decorator, create the file `myproject/signals.py`::

    from djangofloor.decorators import connect
    @connect(path='myproject.signals.demosignal')
    def my_function(request, arg1, arg2):
        print(arg1, arg2)

Serialization/deserialization
*****************************

Since all arguments must be serialized (in JSON), only types which are acceptable for JSON can be used as arguments for signals.


Using Python3
*************

Python3 introduces the notion of function annotations. DjangoFloor can use them to deserialize received data sent by JS::

        @connect(path='myproject.signals.demosignal')
        def my_function(request, arg1: int, arg2: float):
            print(arg1, arg2)


The annotation can be any callable, which raise ValueError (in case of error ;)) or a deserialized value.
DjangoFlor define several callable to handle common cases:

    * checking if a string matches a regexp: :class:`djangofloor.decorators.RE`,
    * checking if a value is one of several choices: :class:`djangofloor.decorators.Choice`,
    * handle form data sent by JS as a plain Django form.

"""
from __future__ import unicode_literals, absolute_import
import logging
import re

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
    """ used to check in a string value match a given regexp.

    Example (requires Python 3.2+), for a function that can only handle a string on the form 123a456::

        @connect(path='myproject.signals.test')
        def test(request, value: RE("\d{3}a\d{3}")):
            pass

    Your code wan't be called if value has not the right form.
    """
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
    """ used to check if a value is among some valid choices.

    Example (requires Python 3.2+), for a function that can only two values::

        @connect(path='myproject.signals.test')
        def test(request, value: Choice([True, False])):
            pass

    Your code wan't be called if value is not True or False.

    `caster` is an optional argument (a callable to convert data before checking its validity).
    """
    def __init__(self, values, caster=None):
        self.values = set(values)
        self.caster = caster

    def __call__(self, value):
        value = self.caster(value) if self.caster else value
        if value not in self.values:
            raise ValueError
        return value


class SerializedForm(object):
    """Transform values sent by JS to a Django form.

    Given a form and a `list` of `dict`, transforms the `dict` into a :class:`django.http.QueryDict` and initialize the form with it.

    >>> class SimpleForm(forms.Form):
    ...    field = forms.CharField()
    ...
    >>> x = SerializedForm(SimpleForm)
    >>> form = x([{'field': 'object'}])
    >>> form.is_valid()
    True

    How to use it with Python3::

        @connect(path='myproject.signals.test')
        def test(request, value: SerializedForm(SimpleForm), other: int):
            print(value.is_valid())

    How to use it with Python2::

        @connect(path='myproject.signals.test')
        def test(request, value, other):
            value = SerializedForm(SimpleForm)(value)
            print(value.is_valid())


    On the JS side, the easiest way is to serialize the form with JQuery::

        <form onsubmit="return df.call('myproject.signals.test', {value: $(this).serializeArray(), other: 42})">
            <input name='field' value='test' type='text'>
        </form>


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

    Can be constructed from a standard :class:`django.http.HttpRequest`.
    """
    def __init__(self, username, session_key, user_pk=None, is_superuser=False, is_staff=False, is_active=False, perms=None):
        """
        :param username: should be User.username
        :type username: :class:`str`
        :param session_key: the session key, unique to a opened browser window (useful when a user has multiple opened windows)
        :type session_key: :class:`str`
        :param user_pk: primary key of the user (for easy ORM queries)
        :type user_pk: :class:`int`
        :param is_superuser: is the user a superuser?
        :type is_superuser: :class:`bool`
        :param is_staff: belongs the user to the staff?
        :type is_staff: :class:`bool`
        :param is_active: is the user active?
        :type is_active: :class:`bool`
        :param perms: list of "app_name.permission_name" (optional)
        :type perms:
        """
        self.username = username
        self.session_key = session_key
        self.user_pk = user_pk
        self.is_superuser = is_superuser
        self.is_staff = is_staff
        self.is_active = is_active
        self._perms = set(perms) if perms is not None else None
        self._template_perms = None

    @classmethod
    def from_user(cls, user):
        """ Create a `SignalRequest` from a valid User. The SessionKey is set to `None`

        :param user: any Django user
        :rtype: `SignalRequest`
        """
        return cls(user.get_username(), None, user_pk=user.pk, is_superuser=user.is_superuser, is_staff=user.is_staff,
                   is_active=user.is_active)

    def to_dict(self):
        """Convert this SignalRequest to a dict which can be provided to JSON.
        :return:
        :rtype:
        """
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
        """ return true is the user has the required perm.

        >>> r = SignalRequest('username', perms=['app_label.codename'])
        >>> r.has_perm('app_label.codename')
        True

        :param perm: name of the permission  ("app_label.codename")
        :return: True if the user has the required perm
        :rtype: :class:`bool`
        """
        return perm in self.perms

    @property
    def perms(self):
        """`set` of all perms of the user (set of "app_label.codename")"""
        if not self.user_pk:
            return set()
        elif self._perms is not None:
            return self._perms
        from django.contrib.auth.models import Permission
        if self.is_superuser:
            query = Permission.objects.all()
        else:
            query = Permission.objects.filter(Q(user__pk=self.user_pk) | Q(group__user__pk=self.user_pk))
        self._perms = set(['%s.%s' % p for p in
                           query.select_related('content_type').values_list('content_type__app_label', 'codename')])
        return self._perms

    @property
    def template_perms(self):
        """`dict` of perms, to be used in templates.

        Example::
        {% if request.template_perms.app_label.codename %}...{% endif %}
        """
        if self._template_perms is None:
            result = {}
            for perm in self.perms:
                app_name, sep, codename = perm.partition('.')
                result.setdefault(app_name, {})[codename] = True
            self._template_perms = result
        return self._template_perms

    @classmethod
    def from_request(cls, request):
        """ return a `SignalRequest` from a Django request.

        If the request already is a SignalRequest, then it is returned as-is (not copied).
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
    """Decorator to use in your Python code. Use it in any file named `signals.py` in a installed Django app.::

        @connect(path='myproject.signal.name', allow_from_client=True, delayed=False)
        def function(request, arg1, arg2, **kwargs):
            pass

    :param fn: the Python function to connect to the signal
    :type fn: any callable
    :param path: the name of the signal
    :type path: :class:`unicode` or :class:`str`
    :param delayed: should this code be called in an asynchronous way (through Celery)? default to `False`
    :type delayed: :class:`bool`
    :param allow_from_client: can be called from JavaScript? default to `True`
    :type allow_from_client: :class:`bool`
    :param auth_required: can be called only from authenticated client? default to `True`
    :type auth_required: :class:`bool`
    :return:
    :rtype:
    """
    wrapped = lambda fn_: RedisCallWrapper(fn_, path=path, delayed=delayed, allow_from_client=allow_from_client, auth_required=auth_required)
    if fn is not None:
        wrapped = wrapped(fn)
    return wrapped
