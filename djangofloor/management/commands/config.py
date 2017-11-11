from argparse import ArgumentParser

from django.conf import settings
from django.core.management import BaseCommand
from django.utils.translation import ugettext as _

from djangofloor import __version__ as version
from djangofloor import decorators
from djangofloor.conf.providers import IniConfigProvider
from djangofloor.conf.settings import merger
from djangofloor.tasks import import_signals_and_functions, get_expected_queues
from djangofloor.utils import remove_arguments_from_help, guess_version
from djangofloor.wsgi.window_info import render_to_string

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    help = 'show the current configuration.' \
           'Can display as python file ("config python") or as .ini file ("config ini"). Use -v 2 to display more info.'
    requires_system_checks = False
    options = {
        'python': 'display the current config as Python module',
        'ini': 'display the current config as .ini file',
        'heroku': 'display a configuration valid to deploy on Heroku',
        'apache': 'display an example of Apache config',
        'nginx': 'display an example of Nginx config',
        'systemd': 'display an example of systemd config',
        'supervisor': 'display an example of Supervisor config',
    }
    if settings.USE_CELERY:
        options['signals'] = 'show the defined signals and remote functions'

    def add_arguments(self, parser):
        assert isinstance(parser, ArgumentParser)
        parser.add_argument('action', default='show', choices=self.options,
                            help=',\n'.join(['"%s": %s' % x for x in self.options.items()]))
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
            self.show_python_config(verbosity)
        elif action == 'ini':
            self.show_ini_config(verbosity)
        elif action == 'signals':
            self.show_signals_config()
        elif action == 'heroku':
            self.show_heroku_config()
        elif action == 'apache':
            self.show_external_config('djangofloor/config/apache.conf')
        elif action == 'nginx':
            self.show_external_config('djangofloor/config/nginx.conf')
        elif action == 'systemd':
            self.show_external_config('djangofloor/config/systemd.conf')
        elif action == 'supervisor':
            self.show_external_config('djangofloor/config/supervisor.conf')

    def show_external_config(self, config):
        content = render_to_string(config, merger.settings)
        self.stdout.write(content)

    def show_signals_config(self):
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

    def show_ini_config(self, verbosity):
        if verbosity >= 2:
            self.stdout.write(self.style.SUCCESS('# read configuration files:'))
        for provider in merger.providers:
            if not isinstance(provider, IniConfigProvider):
                continue
            elif provider.is_valid():
                self.stdout.write(self.style.SUCCESS('    #  - %s "%s"' % (provider.name, provider)))
            elif verbosity >= 2:
                self.stdout.write(self.style.ERROR('    #  - %s "%s" (not found)' % (provider.name, provider)))
        provider = IniConfigProvider()
        merger.write_provider(provider, include_doc=verbosity >= 2)
        self.stdout.write(provider.to_str())

    def show_python_config(self, verbosity):
        self.stdout.write(self.style.SUCCESS('# ' + '-' * 80))
        self.stdout.write(self.style.SUCCESS(_('# Djangofloor version %(version)s') % {'version': version, }))
        self.stdout.write(self.style.SUCCESS(_('# %(project)s version %(version)s') %
                                             {'version': guess_version(merger.settings),
                                              'project': merger.settings['DF_PROJECT_NAME']}))
        self.stdout.write(self.style.SUCCESS('# Configuration providers:'))
        for provider in merger.providers:
            if provider.is_valid():
                self.stdout.write(self.style.SUCCESS('#  - %s "%s"' % (provider.name, provider)))
            elif verbosity > 1:
                self.stdout.write(self.style.ERROR('#  - %s "%s" (not found)' % (provider.name, provider)))
        self.stdout.write(self.style.SUCCESS('# ' + '-' * 80))
        setting_names = list(merger.raw_settings)
        setting_names.sort()
        for setting_name in setting_names:
            if setting_name not in merger.settings:
                continue
            value = merger.settings[setting_name]
            self.stdout.write(self.style.SUCCESS('%s = %r' % (setting_name, value)))
            if verbosity <= 1:
                continue
            for provider_name, raw_value in merger.raw_settings[setting_name].items():
                self.stdout.write(self.style.WARNING('    #   %s -> %r' % (provider_name or 'built-in', raw_value)))

    def show_heroku_config(self):
        # Pipfile
        # add extra packages (due to the config) to the Pipfile
        # requirements.txt
        # heroku addons:create heroku-postgresql:dev
        queues = get_expected_queues()
        self.stdout.write('web: %s-aiohttp' % settings.DF_MODULE_NAME)
        for queue in queues:
            self.stdout.write('%s: %s-%s worker -Q %s' % (queue, settings.DF_MODULE_NAME, 'celery', queue))
