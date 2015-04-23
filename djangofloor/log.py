# coding=utf-8
from __future__ import unicode_literals
import datetime

from django.core import mail
from django.utils.log import AdminEmailHandler


__author__ = 'flanker'

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
        mail.mail_admins(subject, message, *args, connection=self.connection(), **kwargs)

    def format_subject(self, subject):
        """
        Escape CR and LF characters, and limit length.
        RFC 2822's hard limit is 998 characters per line. So, minus "Subject: "
        the actual subject must be no longer than 989 characters.
        """
        formatted_subject = subject.replace('\n', '\\n').replace('\r', '\\r')
        return formatted_subject[:989]
