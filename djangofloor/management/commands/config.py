# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

from argparse import ArgumentParser

from django.core.management import BaseCommand
from django.utils.translation import ugettext as _
from djangofloor import __version__ as version
from djangofloor import decorators
from djangofloor.conf.fields import ConfigField
from djangofloor.conf.providers import IniConfigProvider
from djangofloor.conf.settings import merger
from djangofloor.tasks import import_signals_and_functions
from djangofloor.utils import remove_arguments_from_help

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    help = 'show the current configuration.' \
           'Can display as python file ("config python") or as .ini file ("config ini"). Use -v 2 to display more info.'

    def add_arguments(self, parser):
        assert isinstance(parser, ArgumentParser)
        parser.add_argument('action', default='show', choices=('python', 'ini', 'signals', 'help'),
                            help=('"python": display the current config as Python module,\n'
                                  '"ini": display the current config as .ini file'
                                  '"signals": show the defined signals and remote functions'))
        remove_arguments_from_help(parser, {'--settings', '--traceback', '--pythonpath'})

    def handle(self, *args, **options):
        try:
            self.handle_head(**options)
        except BrokenPipeError:
            pass

    def handle_head(self, **options):
        action = options['action']
        verbosity = options['verbosity']
        if action == 'python':
            self.stdout.write(self.style.NOTICE('# ' + '-' * 80))
            self.stdout.write(self.style.NOTICE(_('# Djangofloor version %(version)s') % {'version': version, }))
            self.stdout.write(self.style.NOTICE('# Configuration providers:'))
            for provider in merger.providers:
                if provider.is_valid():
                    self.stdout.write(self.style.NOTICE('#  - %s "%s"' % (provider.name, provider)))
                elif verbosity > 1:
                    self.stdout.write(self.style.ERROR('#  - %s "%s"' % (provider.name, provider)))
            self.stdout.write(self.style.NOTICE('# ' + '-' * 80))
            setting_names = list(merger.raw_settings)
            setting_names.sort()
            for setting_name in setting_names:
                if setting_name not in merger.settings:
                    continue
                value = merger.settings[setting_name]
                self.stdout.write(self.style.NOTICE('%s = %r' % (setting_name, value)))
                if verbosity <= 1:
                    continue
                for provider_name, raw_value in merger.raw_settings[setting_name].items():
                    self.stdout.write(self.style.WARNING('#   %s -> %r' % (provider_name or 'built-in', raw_value)))
        elif action == 'ini':
            if verbosity >= 3:
                provider = merger.fields_provider
                self.stdout.write(self.style.NOTICE('; list of fields in %s "%s"' % (provider.name, provider)))
            for provider in merger.providers:
                if not isinstance(provider, IniConfigProvider):
                    continue
                elif provider.is_valid():
                    self.stdout.write(self.style.NOTICE('#  - %s "%s"' % (provider.name, provider)))
                elif verbosity >= 2:
                    self.stdout.write(self.style.ERROR('#  - %s "%s"' % (provider.name, provider)))
            provider = IniConfigProvider()
            merger.write_provider(provider)
            self.stdout.write(provider.to_str())
        elif action == 'help':
            for provider in merger.providers:
                if not isinstance(provider, IniConfigProvider):
                    continue
                elif provider.is_valid():
                    self.stdout.write(self.style.NOTICE('#  - %s "%s"' % (provider.name, provider)))
                else:
                    self.stdout.write(self.style.ERROR('#  - %s "%s"' % (provider.name, provider)))
            provider = IniConfigProvider()
            merger.write_provider(provider, include_doc=True)
            self.stdout.write(provider.to_str())
        elif action == 'signals':
            import_signals_and_functions()

            def display_callable(conn):
                fn = conn.function
                if getattr(fn, '__module__', None) and getattr(fn, '__name__', None):
                    path = '%s.%s' % (fn.__module__, fn.__name__)
                elif getattr(fn, '__name__', None):
                    path = fn.__name__
                else:
                    path = str(fn)
                return path

            self.stdout.write(self.style.ERROR('Signals'))
            data = list(decorators.REGISTERED_SIGNALS.items())
            for name, connections in sorted(data, key=lambda x: x[0]):

                self.stdout.write(self.style.WARNING('    "%s"' % name))
                for connection in connections:
                    self.stdout.write(self.style.NOTICE('      -> %s' % display_callable(connection)))
            self.stdout.write(self.style.ERROR('Functions'))
            data = list(decorators.REGISTERED_FUNCTIONS.items())
            for name, connection in sorted(data, key=lambda x: x[0]):
                self.stdout.write(self.style.WARNING('    "%s" -> %s' % (name, display_callable(connection))))
        else:
            self.stdout.write(self.style.WARNING('Please specify either "ini", "signals" or "python"'))
