# coding=utf-8
from __future__ import unicode_literals
import os
import sys

from django.conf import settings
from django.core.management import BaseCommand
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _


class Command(BaseCommand):
    args = '<apache|nginx|supervisor|systemd>'
    help = _('Display example configurations for Apache, NGinx or Supervisor')
    requires_system_checks = False

    def handle(self, *args, **options):
        if not args:
            self.stderr.write('Please provide at least one command apache|nginx|supervisor|system')
            return
        for cmd in args:
            template = 'djangofloor/commands/%(cmd)s.conf' % {'cmd': cmd}
            template_values = self.get_template_values()
            string = render_to_string(template, template_values)
            self.stdout.write(string)

    # noinspection PyMethodMayBeStatic
    def get_template_values(self):
        port = settings.REVERSE_PROXY_PORT
        if port is None:
            port = 80 if not settings.REVERSE_PROXY_SSL_CRT_FILE else 443
        result = {'admins': settings.ADMINS, 'python': sys.executable, 'username': '%s_user' % settings.PROJECT_NAME,
                  'project_name': settings.PROJECT_NAME, 'executable': sys.argv[0], 'databases': settings.DATABASES,
                  'hostnames': settings.ALLOWED_HOSTS, 'bind_address': settings.BIND_ADDRESS,
                  'use_x_send_file': settings.USE_X_SEND_FILE, 'x_accel_redirect': settings.X_ACCEL_REDIRECT,
                  'timeout': settings.REVERSE_PROXY_TIMEOUT,
                  'ssl_key_file': settings.REVERSE_PROXY_SSL_KEY_FILE,
                  'ssl_crt_file': settings.REVERSE_PROXY_SSL_CRT_FILE, 'port': port, 'media_root': settings.MEDIA_ROOT,
                  'media_url': settings.MEDIA_URL, 'static_root': settings.STATIC_ROOT,
                  'static_url': settings.STATIC_URL, 'forwarded_host': settings.USE_X_FORWARDED_HOST,
                  'secure_proxy_header': settings.SECURE_PROXY_SSL_HEADER, 'use_celery': settings.USE_CELERY, }

        for key in ('manage', 'gunicorn', 'celery'):
            key = key.replace('-', '_')
            result[key] = 'djangofloor-%s --dfproject %s' % (key, settings.PROJECT_NAME)
            for foldername in os.environ.get('PATH', '').split(':'):
                path = os.path.join(foldername, 'djangofloor-%s' % key)
                if os.path.isfile(path):
                    result[key] = '%s --dfproject %s' % (path, settings.PROJECT_NAME)
                    break

        return result
