# -*- coding: utf-8 -*-
"""Command for generating default configuration files for Apache, Nginx, Supervisor or systemd.
Currently used for creating Debian packages.

"""
from __future__ import unicode_literals, print_function

import codecs
import datetime
import os
import shutil
import sys

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.template.loader import render_to_string

from djangofloor import defaults_install
from djangofloor.conf.providers import IniConfigProvider
from djangofloor.management.base import TemplatedBaseCommand
from djangofloor.scripts import get_merger_from_env

try:
    # noinspection PyCompatibility
    from configparser import ConfigParser
except ImportError:
    # noinspection PyUnresolvedReferences,PyCompatibility
    from ConfigParser import ConfigParser

__author__ = 'Matthieu Gallet'


class Command(TemplatedBaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--apache22', default=None, help='Generate an Apache 2.2 configuration file.')
        parser.add_argument('--apache24', default=None, help='Generate an Apache 2.4 configuration file.')
        parser.add_argument('--nginx', default=None, help='Generate a NGinx configuration file.')
        parser.add_argument('--systemd', default=None,
                            help='Generate a Systemd configuration file (destination folder).')
        parser.add_argument('--supervisor', default=None, help='Generate a Supervisor configuration file.')
        parser.add_argument('--collectstatic', default=None, help='Collectstatic and copy them to destination.')
        parser.add_argument('--extra-process', default=[], nargs='*', help='Extra process for supervisor or systemd')
        parser.add_argument('--username', default=None, help='Name of the project user')
        parser.add_argument('--conf', default=None, help='Generate a basic configuration file (destination folder)')
        parser.add_argument('--default-conf', default='', help='Use this file as default configuration file')
        parser.add_argument('--defaults', default=defaults_install.__file__,
                            help='filepath of a Python module with default install settings')

    def handle(self, *args, **options):
        config_files = options['config_file']
        template_values = self.get_template_context(config_files)

        # noinspection PyAttributeOutsideInit
        self.verbosity = options.get('verbosity')
        use_sqlite = template_values['DATABASES']['default']['ENGINE'] == 'django.db.backends.sqlite3'
        template_values = {'USERNAME': options.get('user', template_values['DF_MODULE_NAME']),
                           'USE_SQLITE': use_sqlite,
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
                systemd_path = os.path.join(options['systemd'], '%s.service' % process_name)
                self.write_template('djangofloor/commands/systemd.conf', systemd_path, template_values)

        if options['conf']:
            ini_conf_path = os.path.join(options['conf'], 'settings.ini')
            if options['default_conf']:
                shutil.copy2(options['default_conf'], ini_conf_path)
            elif settings.DJANGOFLOOR_MAPPING:
                self.write_template('djangofloor/commands/settings.ini', ini_conf_path, {'settings_merger': merger})

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

    def get_template_context(self, config_files, extra_context):
        """

        :param config_files: list of .ini filenames
        :param extra_context: list of "template_variable=value"
        :return: template context (dict)
        """
        merger = get_merger_from_env(read_only=True)
        for config_file in config_files:
            merger.add_provider(IniConfigProvider(os.path.abspath(config_file)))
        merger.process()
        merger.post_process()
        context = {key: value for (key, value) in merger.settings.items()}
        context['year'] = datetime.datetime.now().year
        context['python_version'] = 'python%s.%s' % (sys.version_info[0], sys.version_info[1])
        context['use_python3'] = sys.version_info[0] == 3
        context['settings_merger'] = merger
        module_name = merger.settings['DF_MODULE_NAME']
        context['path_bin_virtualenv'] = '/home/%s/.virtualenvs/%s/bin' % (module_name, module_name)
        context['path_etc_virtualenv'] = '/home/%s/.virtualenvs/%s/etc' % (module_name, module_name)
        context['path_bin_debian'] = '/usr/local/bin'
        context['path_etc_debian'] = '/etc'
        provider = IniConfigProvider()
        merger.write_provider(provider)
        context['settings_ini'] = provider.to_str()

        for variable in extra_context:
            key, sep, value = variable.partition(':')
            if sep != ':':
                self.stderr.write(self.style.WARNING('Invalid variable %s (should be like KEY:VALUE)' % variable))
                continue
            context[key] = value
        return context
