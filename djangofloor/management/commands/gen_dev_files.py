# -*- coding: utf-8 -*-
"""Generate scripts (for creating packages) and documentation source.

One of the goal of this project is to standardize deployment methods. Documentation should also be standardized.

Takes two base folders (the one provided by DjangoFloor and one provided by your project).
Write all files which are in one of these folders. If a file is in both folders, then the one in DjangoFloor's
directory is ignored.

All these files are assumed to be Django templates. All Django settings are available as template variables.
If you override a default file by an empty one, this file will be ignored.

Two variables are currently added to the context:

  * `year`
  * `python_version` (like `python3.4`), corresponding to the current interpreter

"""
from __future__ import unicode_literals
from argparse import ArgumentParser
import codecs
from difflib import unified_diff
import os
import datetime
import sys

from django.core.management import BaseCommand
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.six import text_type
import pkg_resources

from djangofloor import settings
from djangofloor.utils import walk, SettingMerger


__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        assert isinstance(parser, ArgumentParser)
        parser.add_argument('target', default='.', action='store', help='Target folder')
        parser.add_argument('--extra-folder', default='%s/dev' % settings.PROJECT_NAME,
                            action='store', help='Extra template folder')
        parser.add_argument('--extra-module', default=settings.PROJECT_NAME,
                            action='store', help='Python module for finding extra template folder')
        parser.add_argument('--extra-context', nargs='*', help='Extra variable for the template system '
                                                               '(--extra-context=NAME:VALUE)', default=[])
        parser.add_argument('-t', '--test', default=False, action='store_true',
                            help='Test mode: do not write any file')
        # parser.add_argument('-v', '--verbose', default=False, action='store_true',
        #                     help='Test mode: do not write any file')

    @staticmethod
    def get_relative_filenames(src_module, src_folder):
        """Return the set of all filenames in the `src_folder` (relative to the `src_module` Python module).
         Returned filenames are relative to this base folder.
        """
        result = set()
        if pkg_resources.resource_isdir(src_module, src_folder):
            for (root, dirnames, filenames) in walk(src_module, src_folder):
                for filename in filenames:
                    result.add(os.path.join(root, filename)[len(src_folder) + 1:])
        return result

    def write_template_file(self, default_template_folder, filename, target_directory, context, test_mode=False,
                            verbose_mode=False):
        template_filename = '%s/%s' % (default_template_folder, filename)
        target_filename = os.path.join(target_directory, filename)
        pkg_resources.ensure_directory(target_filename)
        try:
            new_content = render_to_string(template_filename, context)
        except TemplateSyntaxError as e:
            self.stderr.write(self.style.ERROR('Unable to write %s' % filename))
            self.stderr.write(self.style.ERROR(text_type(e)))
            return
        except UnicodeDecodeError as e:
            self.stderr.write(self.style.ERROR('Unable to read template  %s' % template_filename))
            self.stderr.write(self.style.ERROR(text_type(e)))
            return
        if new_content:
            previous_content = None
            if os.path.isfile(target_filename):
                with codecs.open(target_filename, 'r', encoding='utf-8') as fd:
                    previous_content = fd.read()
            if new_content == previous_content:
                self.stdout.write(self.style.MIGRATE_LABEL('Unmodified content: %s' % filename))
            elif not test_mode:
                with codecs.open(target_filename, 'w', encoding='utf-8') as fd:
                    fd.write(new_content)
                self.stdout.write(self.style.MIGRATE_LABEL('Written file: %s' % filename))
            else:
                self.stdout.write(self.style.MIGRATE_LABEL('File to write: %s' % filename))
            if verbose_mode and previous_content and new_content != previous_content:
                for line in unified_diff(previous_content.splitlines(), new_content.splitlines(),
                                         fromfile='%s-before' % target_filename, tofile='%s-after' % target_filename):
                    self.stdout.write(line)
        else:
            self.stdout.write(self.style.MIGRATE_LABEL('Skipped file: %s' % filename))

    def handle(self, *args, **options):
        verbose_mode = options['verbosity'] > 1
        test_mode = options['test']
        if test_mode:
            self.stdout.write(self.style.ERROR('[test mode: no file will be written]'))
        target_directory = options['target']
        default_template_folder = 'djangofloor/dev'
        extra_template_folder = options['extra_folder']
        all_default_filenames = self.get_relative_filenames('djangofloor', 'templates/' + default_template_folder)
        all_extra_filenames = self.get_relative_filenames(options['extra_module'], 'templates/' + extra_template_folder)

        project_settings_module_name = os.environ.get('DJANGOFLOOR_PROJECT_DEFAULTS', '')
        user_settings_path = os.environ.get('DJANGOFLOOR_PYTHON_SETTINGS', '')
        djangofloor_config_path = os.environ.get('DJANGOFLOOR_INI_SETTINGS', '')
        djangofloor_mapping = os.environ.get('DJANGOFLOOR_MAPPING', '')
        project_name = os.environ.get('DJANGOFLOOR_PROJECT_NAME', 'djangofloor')

        merger = SettingMerger(project_name, 'djangofloor.defaults', project_settings_module_name, user_settings_path,
                               djangofloor_config_path, djangofloor_mapping, doc_mode=True)
        merger.process()
        merger.post_process()

        context = {key: value for (key, value) in merger.settings.items() if
                   (key == key.upper() and key not in ('_', '__') and not key.endswith('_HELP'))}
        context['year'] = datetime.datetime.now().year
        context['python_version'] = 'python%s.%s' % (sys.version_info[0], sys.version_info[1])
        context['use_python3'] = sys.version_info[0] == 3
        context['settings_merger'] = merger
        for variable in options['extra_context']:
            key, sep, value = variable.partition(':')
            if sep != ':':
                self.stderr.write(self.style.WARNING('Invalid variable %s (should be like KEY:VALUE)' % variable))
                return
            context[key] = value

        all_default_filenames = list(all_default_filenames)
        all_default_filenames.sort()
        for filename in all_default_filenames:
            if filename in all_extra_filenames:
                continue
            self.write_template_file(default_template_folder, filename, target_directory, context,
                                     test_mode=test_mode, verbose_mode=verbose_mode)
        all_extra_filenames = list(all_extra_filenames)
        all_extra_filenames.sort()
        for filename in all_extra_filenames:
            self.write_template_file(extra_template_folder, filename, target_directory, context,
                                     test_mode=test_mode, verbose_mode=verbose_mode)
