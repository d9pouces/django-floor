# -*- coding: utf-8 -*-
"""Command for générating

"""
from __future__ import unicode_literals, print_function
import codecs
import os
import shutil

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.template.loader import render_to_string
from django.utils.module_loading import import_string
from djangofloor.settings import __settings_original_value as settings_original_values
from djangofloor.iniconf import OptionParser

try:
    # noinspection PyCompatibility
    from configparser import ConfigParser
except ImportError:
    # noinspection PyUnresolvedReferences,PyCompatibility
    from ConfigParser import ConfigParser

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--apache22', default=None, help='Generate an Apache 2.2 configuration file.')
        parser.add_argument('--apache24', default=None, help='Generate an Apache 2.4 configuration file.')
        parser.add_argument('--nginx', default=None, help='Generate a NGinx configuration file.')
        parser.add_argument('--systemd', default=None, help='Generate a Systemd configuration file (destination folder).')
        parser.add_argument('--supervisor', default=None, help='Generate a Supervisor configuration file.')
        parser.add_argument('--collectstatic', default=None, help='Collectstatic and copy them to destination.')
        parser.add_argument('--extra-process', action='append', default=[], help='Extra process for supervisor/systemd.')
        parser.add_argument('--username', default=None, help='Name of the project user')
        parser.add_argument('--conf', default=None, help='Generate a basic configuration file (destination folder)')

    def handle(self, *args, **options):
        # noinspection PyAttributeOutsideInit
        self.verbosity = options.get('verbosity')
        template_values = {'username': options.get('user', settings.PROJECT_NAME),
                           'bind_address': settings.BIND_ADDRESS,
                           'project_name': settings.PROJECT_NAME,
                           'use_celery': settings.USE_CELERY,
                           'static_url': settings.STATIC_URL,
                           'media_url': settings.MEDIA_URL,
                           'use_sqlite': settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3',
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
                                          ('apache22', 'djangofloor/commands/apache22.conf'),
                                          ('apache24', 'djangofloor/commands/apache24.conf'),
                                          ('nginx', 'djangofloor/commands/nginx.conf'),
                                          ):
            if options[option_key]:
                self.write_template(template_name, options[option_key], template_values)
        if options['systemd']:
            for process_name, process_cmd in template_values['processes']:
                template_values['process_name'] = process_name
                template_values['process_cmd'] = process_cmd
                systemd_path = os.path.join(options['systemd'], '%s' % process_name)
                self.write_template('djangofloor/commands/systemd.conf', systemd_path, template_values)

        if options['conf']:
            ini_conf_path = os.path.join(options['conf'], 'settings.ini')
            py_conf_path = os.path.join(options['conf'], 'settings.py')
            self.write_template('djangofloor/commands/settings.py', py_conf_path, template_values)
            if settings.DJANGOFLOOR_MAPPING:
                try:
                    ini_values = import_string(settings.DJANGOFLOOR_MAPPING)
                except ImportError:
                    ini_values = []
                parser = ConfigParser()
                for option_parser in ini_values:
                    assert isinstance(option_parser, OptionParser)
                    value = str(settings_original_values.get(option_parser.setting_name, ''))
                    section, sep, option = option_parser.option.partition('.')
                    if not parser.has_section(section):
                        parser.add_section(section)
                    parser.set(section, option, value)
                with codecs.open(ini_conf_path, 'w', encoding='utf-8') as fd:
                    parser.write(fd)
            else:
                self.write_template('djangofloor/commands/settings.ini', ini_conf_path, {'content': 'content'})

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
