"""Module with all default DjangoFloor WS functions
================================================

For all app in `settings.INSTALLED_APPS`, DjangoFloor tries to import `app.functions` for auto-discovering WS functions.
If you want to write your WS functions into other modules, be sure that `app.functions` imports these modules.

"""
import logging

from django.contrib.auth.forms import SetPasswordForm
from django.http import QueryDict

# noinspection PyProtectedMember
from django.middleware.csrf import (
    _get_new_csrf_string,
    _salt_cipher_secret,
    _unsalt_cipher_token,
)

from djangofloor.decorators import function, is_authenticated
from djangofloor.tasks import scall, WINDOW

__author__ = "Matthieu Gallet"
logger = logging.getLogger("djangofloor.signals")


@function(path="df.validate.set_password", is_allowed_to=is_authenticated)
def validate_set_password_form(window_info, data=None):
    """Dynamically validate the SetPasswordForm (for self-modifying its password) class.

    .. code-block:: javascript

        $.dfws.df.validate.set_password({data: $(this).serializeArray()}).then(function (r) {console.log(r); })

    """
    query_dict = QueryDict("", mutable=True)
    for obj in data:
        query_dict.update({obj["name"]: obj["value"]})
    form = SetPasswordForm(window_info.user, query_dict)
    valid = form.is_valid()
    return {
        "valid": valid,
        "errors": {
            f: e.get_json_data(escape_html=False) for f, e in form.errors.items()
        },
        "help_texts": {f: e.help_text for (f, e) in form.fields.items() if e.help_text},
    }


@function(path="df.validate.renew_csrf", is_allowed_to=is_authenticated)
def renew_csrf(window_info):
    if not window_info.csrf_cookie:
        csrf_secret = _get_new_csrf_string()
        window_info.csrf_cookie = _salt_cipher_secret(csrf_secret)
    else:
        csrf_secret = _unsalt_cipher_token(window_info.csrf_cookie)
    value = _salt_cipher_secret(csrf_secret)
    scall(window_info, "df.validate.update_csrf", to=[WINDOW], value=value)
