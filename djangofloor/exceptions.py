# coding=utf-8
from __future__ import unicode_literals
from django.utils.translation import ugettext as _

__author__ = 'flanker'


class ApiException(Exception):
    http_code = 400

    @property
    def default_msg(self):
        return _('An unknown error occurred during the processing of your request.')

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
        return _('The requested object does not exist on the server.')


class PermissionDenied(ApiException):
    http_code = 403

    @property
    def default_msg(self):
        return _('You do not have the permission to do that.')


class InvalidRequest(ApiException):
    http_code = 400

    @property
    def default_msg(self):
        return _('Invalid request.')


class InvalidOperation(ApiException):
    http_code = 400

    @property
    def default_msg(self):
        return _('You cannot execute this command.')


class InternalServerError(ApiException):
    http_code = 500

    @property
    def default_msg(self):
        return _('An error occured on the server.')


class AuthenticationRequired(ApiException):
    http_code = 401

    @property
    def default_msg(self):
        return _('You must be authenticated to use this method.')
