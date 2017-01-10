# coding=utf-8
"""Connect Python code to the DjangoFloor signal system
====================================================

Define the decorator for connecting Python code to signals, a :class:`djangofloor.decorators.SignalRequest`
which can be easily serialized and is lighter than a :class:`django.http.HttpRequest`,
and some code to convert serialized data sent by Javascript to something useful in Python.

Using the decorator
*******************

The decorator :func:`djangofloor.decorators.connect` let you connect any Python function to a signal (which is only a
text string). Signals are automatically discovered, as soon as there are in files `signals.py` in any app listed in
the setting `INSTALLED_APPS` (like `admin.py` or `models.py`).

To use this decorator, create the file `myproject/signals.py`::

    from djangofloor.decorators import connect
    @connect(path='myproject.signals.demosignal')
    def my_function(request, arg1, arg2):
        print(arg1, arg2)

Serialization/deserialization
*****************************

Since all arguments must be serialized (in JSON), only types which are acceptable for JSON can be used as arguments
for signals.


Using Python3
*************

Python3 introduces the notion of function annotations. DjangoFloor can use them to deserialize received data sent by JS:


.. code-block:: python

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
from django.utils.six import text_type


try:
    from inspect import signature
except ImportError:
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    from funcsigs import signature
from django import forms
from django.utils.translation import ugettext_lazy as _
from djangofloor.exceptions import InvalidRequest


__author__ = 'Matthieu Gallet'
REGISTERED_SIGNALS = {}
logger = logging.getLogger('djangofloor.request')


class RE(object):
    """ used to check in a string value match a given regexp.

    Example (requires Python 3.2+), for a function that can only handle a string on the form 123a456:

    .. code-block:: python

        @connect(path='myproject.signals.test')
        def test(request, value: RE("\d{3}a\d{3}")):
            pass

    Your code wan't be called if value has not the right form.


    :param value: the pattern of the regexp
    :type value: `str`
    :param caster: if not `None`, any callable applied to the value (if valid)
    :type caster: `callable` or `None`
    :param flags: regexp flags passed to `re.compile`
    :type flags: `int`
    """
    def __init__(self, value, caster=None, flags=0):
        self.caster = caster
        self.regexp = re.compile(value, flags=flags)

    def __call__(self, value):
        matcher = self.regexp.match(value)
        if not matcher:
            raise ValueError
        value = matcher.group(1) if matcher.groups() else value
        return self.caster(value) if self.caster else value


class Choice(object):
    """ used to check if a value is among some valid choices.

    Example (requires Python 3.2+), for a function that can only two values:

    .. code-block:: python

        @connect(path='myproject.signals.test')
        def test(request, value: Choice([True, False])):
            pass

    Your code wan't be called if value is not True or False.

    :param caster: callable to convert the provided deserialized JSON data before checking its validity.
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

    Given a form and a :class:`list` of :class:`dict`, transforms the :class:`list` into a
    :class:`django.http.QueryDict` and initialize the form with it.

    >>> class SimpleForm(forms.Form):
    ...    field = forms.CharField()
    ...
    >>> x = SerializedForm(SimpleForm)
    >>> form = x([{'field': 'object'}])
    >>> form.is_valid()
    True

    How to use it with Python3:

    .. code-block:: python

        @connect(path='myproject.signals.test')
        def test(request, value: SerializedForm(SimpleForm), other: int):
            print(value.is_valid())

    How to use it with Python2:

    .. code-block:: python

        @connect(path='myproject.signals.test')
        def test(request, value, other):
            value = SerializedForm(SimpleForm)(value)
            print(value.is_valid())


    On the JS side, the easiest way is to serialize the form with JQuery:

    .. code-block:: html

        <form onsubmit="return df.call('myproject.signals.test', {value: $(this).serializeArray(), other: 42})">
            <input name='field' value='test' type='text'>
        </form>


    """
    def __init__(self, form_cls):
        self.form_cls = form_cls

    def __call__(self, value, *args, **kwargs):
        """
        :param value:
        :type value: :class:`list` of :class:`dict`
        :return:
        :rtype: :class:`django.forms.Form`
        """
        query_dict = QueryDict('', mutable=True)
        for obj in value:
            query_dict.update({obj['name']: obj['value']})
        return self.form_cls(query_dict, *args, **kwargs)


class SignalRequest(object):
    """ Store the username and the session key and must be supplied to any Python signal call.

    Can be constructed from a standard :class:`django.http.HttpRequest`.

    :param username: should be User.username
    :type username: :class:`str`
    :param session_key: the session key, unique to a opened browser window (useful if a user has multiple windows)
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
    :type perms: :class:`list`
    :param window_key: a string value specific to each opened browser window/tab
    :type window_key: :class:`str`
    """
    def __init__(self, username, session_key, user_pk=None, is_superuser=False, is_staff=False, is_active=False,
                 perms=None, window_key=None):
        self.username = username
        self.session_key = session_key
        self.user_pk = user_pk
        self.is_superuser = is_superuser
        self.is_staff = is_staff
        self.is_active = is_active
        self._perms = set(perms) if perms is not None else None
        self._template_perms = None
        self.window_key = window_key

    @classmethod
    def from_user(cls, user):
        """ Create a :class:`djangofloor.decorators.SignalRequest` from a valid User. The SessionKey is set to `None`

        :param user: any Django user
        :type user: :class:`django.contrib.auth.models.AbstractUser`
        :rtype: :class:`djangofloor.decorators.SignalRequest`
        """
        return cls(user.get_username(), None, user_pk=user.pk, is_superuser=user.is_superuser, is_staff=user.is_staff,
                   is_active=user.is_active)

    def to_dict(self):
        """Convert this :class:`djangofloor.decorators.SignalRequest` to a :class:`dict` which can be provided to JSON.

        :return: a dict ready to be serialized in JSON
        :rtype: :class:`dict`
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
        """:class:`set` of all perms of the user (set of "app_label.codename")"""
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
        """:class:`dict` of perms, to be used in templates.

        Example:

        .. code-block:: html

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
        """ return a :class:`djangofloor.decorators.SignalRequest` from a :class:`django.http.HttpRequest`.

        If the request already is a :class:`djangofloor.decorators.SignalRequest`,
        then it is returned as-is (not copied).

        :param request: standard Django request
        :type request: :class:`django.http.HttpRequest` or :class:`djangofloor.decorators.SignalRequest`
        :return: a valid request
        :rtype: :class:`djangofloor.decorators.SignalRequest`
        """
        if isinstance(request, SignalRequest):
            return request
        # noinspection PyUnresolvedReferences
        session_key = request.session.session_key if hasattr(request, 'session') and request.session else None
        window_key = request.window_key if hasattr(request, 'window_key') else None
        # noinspection PyUnresolvedReferences
        user = request.user if hasattr(request, 'user') and request.user else None
        if user.is_authenticated():
            return cls(username=user.get_username(), session_key=session_key,
                       user_pk=user.pk, is_superuser=user.is_superuser, is_staff=user.is_staff,
                       is_active=user.is_active, window_key=window_key)
        return cls(None, session_key=session_key, window_key=window_key)


class ViewWrapper(object):
    def __init__(self, fn, path=None):
        self.path = path
        self.function = fn
        self.__name__ = fn.__name__ if hasattr(fn, '__name__') else path

        # fetch signature to analyze arguments
        sig = signature(fn)
        self.required_arguments = set()
        self.optional_arguments = set()
        self.accept_kwargs = False
        self.accept_args = False
        self.argument_types = {}
        self.required_arguments_names = []
        self.optional_arguments_names = []

        for key, param in sig.parameters.items():
            if key in ('request', ):
                continue
            if param.kind == param.VAR_KEYWORD:  # corresponds to "fn(**kwargs)"
                self.accept_kwargs = True
            elif param.kind == param.VAR_POSITIONAL:  # corresponds to "fn(*args)"
                self.accept_args = True
            elif param.default == param.empty:  # "fn(foo)" : kind = POSITIONAL_ONLY or POSITIONAL_OR_KEYWORD
                self.required_arguments.add(key)
                if param.annotation != param.empty and callable(param.annotation):
                    self.argument_types[key] = param.annotation
                self.required_arguments_names.append(key)
            else:
                self.optional_arguments.add(key)  # "fn(foo=bar)" : kind = POSITIONAL_OR_KEYWORD or KEYWORD_ONLY
                if param.annotation != param.empty and callable(param.annotation):
                    self.argument_types[key] = param.annotation
                self.optional_arguments_names.append(key)

        if path is None:
            path = fn.__name__
        self.register(path)

    def register(self, path):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


class RedisCallWrapper(ViewWrapper):
    def __init__(self, fn, path=None, delayed=False, allow_from_client=True, auth_required=True):
        super(RedisCallWrapper, self).__init__(fn, path=path)
        self.allow_from_client = allow_from_client
        self.delayed = delayed
        self.auth_required = auth_required

    def register(self, path):
        REGISTERED_SIGNALS.setdefault(path, []).append(self)

    def prepare_kwargs(self, kwargs):
        logger.debug(self.path, kwargs)
        kwargs = {x: y for (x, y) in kwargs.items()}
        if not self.accept_kwargs:
            for arg_name in kwargs:
                if arg_name not in self.required_arguments and arg_name not in self.optional_arguments:
                    raise InvalidRequest(text_type(_('Unexpected argument: %(arg)s')) % {'arg': arg_name})
        for arg_name in self.required_arguments:
            if arg_name not in kwargs:
                raise InvalidRequest(text_type(_('Required argument: %(arg)s')) % {'arg': arg_name})
        for k, v in self.argument_types.items():
            try:
                if k in kwargs:
                    kwargs[k] = v(kwargs[k])
            except ValueError:
                raise InvalidRequest(text_type(_('Invalid value %(value)s for argument %(arg)s.')) %
                                     {'arg': k, 'value': v})
        return kwargs


def connect(fn=None, path=None, delayed=False, allow_from_client=True, auth_required=True):
    """Decorator to use in your Python code. Use it in any file named `signals.py` in a installed Django app.

    .. code-block:: python

        @connect(path='myproject.signal.name', allow_from_client=True, delayed=False)
        def function(request, arg1, arg2, **kwargs):
            pass

    :param fn: the Python function to connect to the signal
    :type fn: :class:`callable`
    :param path: the name of the signal
    :type path: :class:`unicode` or :class:`str`
    :param delayed: should this code be called in an asynchronous way (through Celery)? default to `False`
    :type delayed: :class:`bool`
    :param allow_from_client: can be called from JavaScript? default to `True`
    :type allow_from_client: :class:`bool`
    :param auth_required: can be called only from authenticated client? default to `True`
    :type auth_required: :class:`bool`
    :return: a wrapped function
    :rtype: :class:`callable`
    """
    wrapped = lambda fn_: RedisCallWrapper(fn_, path=path, delayed=delayed, allow_from_client=allow_from_client,
                                           auth_required=auth_required)
    if fn is not None:
        wrapped = wrapped(fn)
    return wrapped
