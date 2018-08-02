"""Common DjangoFloor exceptions
=============================
.. deprecated:: 1.0

Define several common exceptions, which can be gracefully handled by DjangoFloor.
You should raise these exceptions, or create new exceptions which derive from these ones. They help to display helpful
messages to end-user.
"""
import warnings

from django.utils.translation import ugettext as _
from djangofloor.utils import RemovedInDjangoFloor200Warning

__author__ = "Matthieu Gallet"
warnings.warn(
    "djangofloor.exceptions module and its functions will be removed",
    RemovedInDjangoFloor200Warning,
)


class ApiException(Exception):
    """ Base exception, corresponding to a bad request from the client.
    """

    http_code = 400

    @property
    def default_msg(self):
        return _("An unknown error occurred during the processing of your request.")

    def __init__(self, msg=None):
        self.msg = msg or self.default_msg

    def __unicode__(self):
        return self.msg

    def __str__(self):
        return self.msg


class NotFoundException(ApiException):
    http_code = 404

    @property
    def default_msg(self):
        return _("The requested object does not exist on the server.")


class PermissionDenied(ApiException):
    http_code = 403

    @property
    def default_msg(self):
        return _("You do not have the permission to do that.")


class InvalidRequest(ApiException):
    http_code = 400

    @property
    def default_msg(self):
        return _("Invalid request.")


class InvalidOperation(ApiException):
    http_code = 400

    @property
    def default_msg(self):
        return _("You cannot execute this command.")


class InternalServerError(ApiException):
    http_code = 500

    @property
    def default_msg(self):
        return _("An error occured on the server.")


class AuthenticationRequired(ApiException):
    http_code = 401

    @property
    def default_msg(self):
        return _("You must be authenticated to use this method.")
