# -*- coding: utf-8 -*-
"""Generate scripts (for creating packages) and documentation source.

One of the goal of this project is to standardize deployment methods. Documentation should also be standardized.

Takes two base folders (the one provided by DjangoFloor and one provided by your project).
Write all files which are in one of these folders. If a file is in both folders, then the one in DjangoFloor's
directory is ignored.

All these files are assumed to be Django templates. All Django settings are available as template variables.
If you override a default file by an empty one, this file will be ignored.

A few extra variables are currently added to the context:

  * `python_version` (like `python3.4`), corresponding to the current interpreter
  * `year` : datetime.datetime.now().year
  * `use_python3` : sys.version_info[0] == 3
  * `settings_merger` : :class:`djangofloor.utils.SettingMerger` with documentation settings

"""
from __future__ import unicode_literals
from argparse import ArgumentParser
from collections import OrderedDict
from difflib import unified_diff
import datetime
import sys

import codecs
import os
from django.core.management import BaseCommand
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.six import text_type
import pkg_resources

from djangofloor import settings
from djangofloor.utils import walk, SettingMerger

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    template_suffix = '_tpl'

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

    def get_relative_filenames(self, src_module, src_folder):
        """Return the set of all filenames in the `src_folder` (relative to the `src_module` Python module).
        If the filename ends with '_tpl', this suffix will be removed and the file will be templated.

         Returned filenames are relative to this base folder.
        """
        self.stdout.write(self.style.SUCCESS('Looking for template files in %s:%s' % (src_module, src_folder)))
        result = {}
        if pkg_resources.resource_isdir(src_module, src_folder):
            for (root, dirnames, filenames) in walk(src_module, src_folder):
                for filename in filenames:
                    path = os.path.join(root, filename)[len(src_folder) + 1:]
                    # noinspection PyTypeChecker
                    if path.endswith(self.template_suffix):
                        result[path[:-len(self.template_suffix)]] = path
                    else:
                        result[path] = path
        return result

    def write_template_file(self, default_template_folder, filename, target_directory, context, test_mode=False,
                            verbose_mode=False):
        template_filename = '%s/%s' % (default_template_folder, filename)
        target_filename = os.path.join(target_directory, filename)
        display_filename = filename
        # noinspection PyTypeChecker
        if target_filename.endswith(self.template_suffix):
            target_filename = target_filename[:-len(self.template_suffix)]
        if display_filename.endswith(self.template_suffix):
            display_filename = display_filename[:-len(self.template_suffix)]
        pkg_resources.ensure_directory(target_filename)
        try:
            new_content = render_to_string(template_filename, context)
        except TemplateSyntaxError as e:
            self.stderr.write(self.style.ERROR('Invalid template %s found in %s' % (filename, default_template_folder)))
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
                self.stdout.write(self.style.MIGRATE_LABEL('Unmodified content: %s from %s' %
                                                           (display_filename, default_template_folder)))
            elif not test_mode:
                with codecs.open(target_filename, 'w', encoding='utf-8') as fd:
                    fd.write(new_content)
                self.stdout.write(self.style.MIGRATE_LABEL('Written file: %s from %s' %
                                                           (display_filename, default_template_folder)))
            else:
                self.stdout.write(self.style.MIGRATE_LABEL('File to write: %s from %s' %
                                                           (display_filename, default_template_folder)))
            if verbose_mode and previous_content and new_content != previous_content:
                for line in unified_diff(previous_content.splitlines(), new_content.splitlines(),
                                         fromfile='%s-before' % target_filename, tofile='%s-after' % target_filename):
                    self.stdout.write(line)
        else:
            self.stdout.write(self.style.MIGRATE_LABEL('Skipped file: %s from %s' %
                                                       (display_filename, default_template_folder)))

    def handle(self, *args, **options):
        verbose_mode = options['verbosity'] > 1
        test_mode = options['test']
        if test_mode:
            self.stdout.write(self.style.ERROR('[test mode: no file will be written]'))
        target_directory = options['target']
        default_template_folder = 'djangofloor/dev'
        extra_template_folder = options['extra_folder']
        # noinspection PyTypeChecker
        all_default_filenames = self.get_relative_filenames('djangofloor', 'templates/' + default_template_folder)
        all_extra_filenames = self.get_relative_filenames(options['extra_module'], 'templates/' + extra_template_folder)

        project_settings_module_name = os.environ.get('DJANGOFLOOR_PROJECT_DEFAULTS', '')
        user_settings_path = os.environ.get('DJANGOFLOOR_PYTHON_SETTINGS', '')
        djangofloor_config_path = os.environ.get('DJANGOFLOOR_INI_SETTINGS', '')
        djangofloor_mapping = os.environ.get('DJANGOFLOOR_MAPPING', '')
        project_name = os.environ.get('DJANGOFLOOR_PROJECT_NAME', 'djangofloor')

        merger = SettingMerger(project_name, 'djangofloor.defaults', project_settings_module_name, user_settings_path,
                               djangofloor_config_path, djangofloor_mapping, doc_mode=True, read_only=True)
        merger.process()
        merger.post_process()

        context = {key: value for (key, value) in merger.settings.items() if
                   (key == key.upper() and key not in ('_', '__') and not key.endswith('_HELP'))}
        context['year'] = datetime.datetime.now().year
        context['python_version'] = 'python%s.%s' % (sys.version_info[0], sys.version_info[1])
        context['use_python3'] = sys.version_info[0] == 3
        context['settings_merger'] = merger
        context['path_bin_virtualenv'] = '/home/%s/.virtualenvs/%s/bin' % (merger.settings['PROJECT_NAME'],
                                                                           merger.settings['PROJECT_NAME'])
        context['path_etc_virtualenv'] = '/home/%s/.virtualenvs/%s/etc' % (merger.settings['PROJECT_NAME'],
                                                                           merger.settings['PROJECT_NAME'])
        context['path_bin_debian'] = '/usr/local/bin'
        context['path_etc_debian'] = '/etc'
        for variable in options['extra_context']:
            key, sep, value = variable.partition(':')
            if sep != ':':
                self.stderr.write(self.style.WARNING('Invalid variable %s (should be like KEY:VALUE)' % variable))
                return
            context[key] = value
        # write files defined by DjangoFloor
        filenames = OrderedDict(sorted(all_default_filenames.items(), key=lambda y: y[0]))
        for target_filename, filename in filenames.items():
            if target_filename in all_extra_filenames:
                continue
            self.write_template_file(default_template_folder, filename, target_directory, context,
                                     test_mode=test_mode, verbose_mode=verbose_mode)
        # write files defined by your project
        filenames = [x for x in all_extra_filenames.values()]
        filenames.sort()
        for filename in filenames:
            self.write_template_file(extra_template_folder, filename, target_directory, context,
                                     test_mode=test_mode, verbose_mode=verbose_mode)
