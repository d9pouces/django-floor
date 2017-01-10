# coding=utf-8
"""Log handler that send emails
============================

Overrides :class:`django.utils.log.AdminEmailHandler` to avoid flooding admin with many e-mails.

If an e-mail with the same object has already been sent in the last 10 minutes, then nothing is done.
This duration can be configured (argument `min_interval`).

"""
from __future__ import unicode_literals
import datetime

from django.core import mail
from django.utils.log import AdminEmailHandler
import io
import sys


__author__ = 'Matthieu Gallet'

LAST_SENDS = {}


class FloorAdminEmailHandler(AdminEmailHandler):
    """An exception log handler that emails log entries to site admins.

    If the request is passed as the first argument to the log record,
    request data will be provided in the email report.
    """
    def __init__(self, include_html=False, email_backend=None, min_interval=600):
        super(FloorAdminEmailHandler, self).__init__(include_html=include_html, email_backend=email_backend)
        self.min_interval = min_interval

    def send_mail(self, subject, message, *args, **kwargs):
        interval = datetime.datetime.now() - LAST_SENDS.get(subject, datetime.datetime(1970, 1, 1))
        if interval < datetime.timedelta(0, self.min_interval):
            return
        LAST_SENDS[subject] = datetime.datetime.now()
        original_std = sys.stdout, sys.stderr
        # sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        try:
            pass
            mail.mail_admins(subject, message, *args, connection=self.connection(), **kwargs)
        except Exception as e:
            print('<==================================================================================================')
            print('Unable to send the mail: %s' % e)
            print(subject)
            print('===================================================================================================')
            print('/!\\ settings.DEBUG = False BUT STILL UNABLE TO SEND MAIL TO ADMIN /!\\')
            print('==================================================================================================>')
        sys.stdout, sys.stdout = original_std