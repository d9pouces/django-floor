# -*- coding: utf-8 -*-
"""Command for générating

"""
from __future__ import unicode_literals, print_function
import codecs
import os
import shutil

from django.conf import settings
from django.core.management import BaseCommand, call_command, execute_from_command_line
from django.template.loader import render_to_string

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--apache', default=None, help='Generate an Apache configuration file.')
        parser.add_argument('--nginx', default=None, help='Generate a NGinx configuration file.')
        parser.add_argument('--systemd', default=None, help='Generate a Systemd configuration file.')
        parser.add_argument('--supervisor', default=None, help='Generate a Supervisor configuration file.')
        parser.add_argument('--initd', default=None, help='Generate a init.d configuration file.')
        parser.add_argument('--clearsessions', default=None, help='Generate a crontab line for the clearsession command.')
        parser.add_argument('--crontab', default=None, help='Generate a Crontab configuration file.')
        parser.add_argument('--collectstatic', default=None, help='Collectstatic and copy them to destination.')
        parser.add_argument('--extra-process', action='append', default=[], help='Extra process for supervisor/systemd.')
        parser.add_argument('--user', default=None, help='Name of the project user')

    def handle(self, *args, **options):
        # noinspection PyAttributeOutsideInit
        self.verbosity = options.get('verbosity')
        template_values = {'username': options.get('user', settings.PROJECT_NAME),
                           'project_name': settings.PROJECT_NAME,
                           'use_celery': settings.USE_CELERY,
                           'gunicorn': None,
                           'static_dst': None,
                           'processes': [x.split(':') for x in options['extra_process']]}
        static_dst = options['collectstatic']
        if static_dst:
            if os.path.isdir(settings.STATIC_ROOT):
                shutil.rmtree(settings.STATIC_ROOT)
            call_command('collectstatic', interactive=False)
            if os.path.isdir(static_dst):
                shutil.rmtree(static_dst)
            shutil.copytree(settings.STATIC_ROOT, static_dst)
            template_values['static_dst'] = static_dst
        for option_key, template_name in (('supervisor', 'djangofloor/commands/supervisor.conf'),
                                          ('systemd', 'djangofloor/commands/systemd.conf'),
                                          ('apache', 'djangofloor/commands/apache.conf'),
                                          ('nginx', 'djangofloor/commands/nginx.conf'),
                                          ):
            if options[option_key]:
                self.write_template(template_name, options[option_key], template_values)

    @staticmethod
    def write_template(template_name, filename, extra_template_values):
        template_values = {}
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        template_values.update(extra_template_values)
        content = render_to_string(template_name, template_values)
        with codecs.open(filename, 'w', encoding='utf-8') as fd:
            fd.write(content)
