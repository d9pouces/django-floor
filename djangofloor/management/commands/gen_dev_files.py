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
import os
import datetime

from django.core.management import BaseCommand
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.six import text_type
import pkg_resources
import sys

from djangofloor import settings
from djangofloor.utils import walk
from djangofloor.settings import merger

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

    def write_template_file(self, default_template_folder, filename, target_directory, context):
        template_filename = '%s/%s' % (default_template_folder, filename)
        target_filename = os.path.join(target_directory, filename)
        pkg_resources.ensure_directory(target_filename)
        try:
            text = render_to_string(template_filename, context)
        except TemplateSyntaxError as e:
            self.stderr.write(self.style.ERROR('Unable to write %s' % filename))
            self.stderr.write(self.style.ERROR(text_type(e)))
            return
        except UnicodeDecodeError as e:
            self.stderr.write(self.style.ERROR('Unable to read template  %s' % template_filename))
            self.stderr.write(self.style.ERROR(text_type(e)))
            return
        if text:
            with codecs.open(target_filename, 'w', encoding='utf-8') as fd:
                fd.write(text)
            self.stdout.write(self.style.MIGRATE_LABEL('Written file: %s' % filename))
        else:
            self.stdout.write(self.style.MIGRATE_LABEL('Skipped file: %s' % filename))

    def handle(self, *args, **options):
        target_directory = options['target']
        default_template_folder = 'djangofloor/dev'
        extra_template_folder = options['extra_folder']
        all_default_filenames = self.get_relative_filenames('djangofloor', 'templates/' + default_template_folder)
        all_extra_filenames = self.get_relative_filenames(options['extra_module'], 'templates/' + extra_template_folder)

        context = {key: value for (key, value) in merger.settings.items() if
                   (key == key.upper() and key not in ('_', '__') and not key.endswith('_HELP'))}
        context['year'] = datetime.datetime.now().year
        context['python_version'] = 'python%s.%s' % (sys.version_info[0], sys.version_info[1])
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
            self.write_template_file(default_template_folder, filename, target_directory, context)
        all_extra_filenames = list(all_extra_filenames)
        all_extra_filenames.sort()
        for filename in all_extra_filenames:
            self.write_template_file(extra_template_folder, filename, target_directory, context)
