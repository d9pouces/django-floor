""" "Main" functions for Django, Celery, Gunicorn and uWSGI
========================================================

Define "main" functions for your scripts using the Django `manage.py` system or Gunicorn/Celery/uWSGI.
"""
import datetime
import ipaddress
import logging
import logging.config
import os
import re
import shutil
import subprocess
import sys
from argparse import ArgumentParser
from distutils.spawn import find_executable
from typing import Union

from django.utils.autoreload import python_reloader

from djangofloor.conf.merger import SettingMerger
from djangofloor.conf.providers import PythonModuleProvider, PythonFileProvider, IniConfigProvider, \
    PythonConfigFieldsProvider

__author__ = 'Matthieu Gallet'


class ScriptCommand:

    def __init__(self):
        self.options_set = []

    def add_arguments(self, parser: ArgumentParser):
        pass

    def add_argument(self, parser, *args, **kwargs):
        self.options_set.append(args[-1])
        parser.add_argument(*args, **kwargs)

    def set_options(self, options):
        for option_name in self.options_set:
            option_name = option_name.replace('-', '_')
            while option_name[0:1] == '_':
                option_name = option_name[1:]
            set_default_option(options, option_name)

    def __call__(self):
        set_env()
        import django
        django.setup()
        from django.conf import settings
        logging.config.dictConfig(settings.LOGGING)
        parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
        self.add_arguments(parser)
        options, extra_args = parser.parse_known_args()
        sys.argv[1:] = extra_args
        if not os.environ.get('DF_CONF_SET', ''):
            os.environ['DF_CONF_SET'] = '1'
            self.set_options(options)
        self.run_script()

    def run_script(self):
        raise NotImplementedError


class DjangoCommand(ScriptCommand):
    """
    Main function, calling Django code for management commands. Retrieve some default values from Django settings.
    """

    def run_script(self):
        from django.conf import settings
        from django.core import management
        commands = {x: y for (x, y) in management.get_commands().items()
                    if x not in settings.DF_REMOVED_DJANGO_COMMANDS}

        def get_commands():
            return commands

        management.get_commands = get_commands
        if len(sys.argv) >= 2 and sys.argv[1] == 'runserver':
            from django.core.management.commands.runserver import Command as RunserverCommand
            ip_address, sep, port = settings.LISTEN_ADDRESS.rpartition(':')
            try:
                ipaddress.IPv6Address(ip_address)
                RunserverCommand.default_addr_ipv6 = ip_address
            except ipaddress.AddressValueError:
                RunserverCommand.default_addr = ip_address
            RunserverCommand.default_port = port

        try:
            from djangofloor.management import execute_from_command_line
            return execute_from_command_line(sys.argv)
        except BrokenPipeError:
            pass

    def __call__(self):
        if len(sys.argv) >= 2:
            if sys.argv[1] == 'worker':
                sys.argv += ['worker']
                return celery()
            elif sys.argv[1] == 'server':
                return gunicorn()
            elif sys.argv[1] == 'celery':
                return celery()
        return super().__call__()


class GunicornCommand(ScriptCommand):
    """ wrapper around gunicorn. Retrieve some default values from Django settings.

    :return:
    """

    def add_arguments(self, parser: ArgumentParser):
        from django.conf import settings
        if settings.WEBSOCKET_URL:
            worker_cls = 'aiohttp.worker.GunicornWebWorker'
        else:
            worker_cls = 'gunicorn.workers.gthread.ThreadWorker'
        self.add_argument(parser, '-b', '--bind', default=settings.LISTEN_ADDRESS)
        self.add_argument(parser, '--threads', default=settings.DF_SERVER_THREADS, type=int)
        self.add_argument(parser, '-w', '--workers', default=settings.DF_SERVER_PROCESSES, type=int)
        self.add_argument(parser, '--graceful-timeout', default=settings.DF_SERVER_GRACEFUL_TIMEOUT, type=int)
        self.add_argument(parser, '--max-requests', default=settings.DF_SERVER_MAX_REQUESTS, type=int)
        self.add_argument(parser, '--keep-alive', default=settings.DF_SERVER_KEEPALIVE, type=int)
        self.add_argument(parser, '-t', '--timeout', default=settings.DF_SERVER_TIMEOUT, type=int)
        self.add_argument(parser, '--keyfile', default=settings.DF_SERVER_SSL_KEY)
        self.add_argument(parser, '--certfile', default=settings.DF_SERVER_SSL_CERTIFICATE)
        self.add_argument(parser, '--reload', default=False, action='store_true')
        self.add_argument(parser, '-k', '--worker-class', default=worker_cls)

    def run_script(self):
        application = 'djangofloor.wsgi.aiohttp_runserver:application'
        if application not in sys.argv:
            sys.argv.append(application)
        from gunicorn.app.wsgiapp import run
        return run()


class CeleryCommand(ScriptCommand):

    def add_arguments(self, parser: ArgumentParser):
        from django.conf import settings
        parser.add_argument('-A', '--app', action='store', default='djangofloor')
        is_worker = len(sys.argv) > 1 and sys.argv[1] == 'worker'
        if is_worker:
            parser.add_argument('-c', '--concurrency', action='store', default=settings.CELERY_PROCESSES,
                                help='Number of child processes processing the queue. The'
                                'default is the number of CPUs available on your'
                                'system.')

    def run_script(self):
        from django.conf import settings
        from celery.bin.celery import main as celery_main
        if settings.DEBUG and 'worker' in sys.argv and '-h' not in sys.argv:
            python_reloader(celery_main, (sys.argv, ), {})
        else:
            celery_main(sys.argv)


def set_default_option(options, name: str):
    option_name = name.replace('_', '-')
    if hasattr(options, name) and getattr(options, name):
        sys.argv += ['--%s' % option_name, str(getattr(options, name))]


def get_merger_from_env() -> SettingMerger:
    """ Should be used after set_env(); determine all available settings in this order:

   * djangofloor.defaults
   * {project_name}.defaults (overrides djangofloor.defaults)
   * {root}/etc/{project_name}/settings.ini (overrides {project_name}.settings)
   * {root}/etc/{project_name}/settings.py (overrides {root}/etc/{project_name}/settings.ini)
   * ./local_settings.ini (overrides {root}/etc/{project_name}/settings.py)
   * ./local_settings.py (overrides ./local_settings.ini)

    """
    # required if set_env is not called
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangofloor.conf.settings')
    if 'PYCHARM_DJANGO_MANAGE_MODULE' in os.environ:
        # noinspection EmptyAlternationBranch
        pycharm_matcher = re.match(r'^([\w_\-.]+)-(\w+)(\.py|\.pyc|)$', os.environ['PYCHARM_DJANGO_MANAGE_MODULE'])
        if pycharm_matcher:
            os.environ.setdefault('DF_CONF_NAME', '%s:%s' % pycharm_matcher.groups()[:2])
    os.environ.setdefault('DF_CONF_NAME', '%s:%s' % ('django', 'django'))
    module_name, sep, script = os.environ['DF_CONF_NAME'].partition(':')
    module_name = module_name.replace('-', '_')
    if sep != ':':
        script = None

    prefix = os.path.abspath(sys.prefix)
    if prefix == '/usr':
        prefix = ''

    def search_providers(basename, suffix, cls):
        default_ini_filename = '%s/etc/%s/%s.%s' % (prefix, module_name, basename, suffix)
        ini_filenames = [default_ini_filename]
        ini_filenames.sort()
        return [cls(x) for x in ini_filenames]
    local_conf_filename = os.path.abspath('local_settings.ini')
    # global_conf_filename = '%s/etc/%s/settings.ini' % (prefix, module_name)

    config_providers = [PythonModuleProvider('djangofloor.conf.defaults')]
    if module_name != 'djangofloor':
        config_providers.append(PythonModuleProvider('%s.defaults' % module_name))
        mapping = '%s.iniconf:INI_MAPPING' % module_name
    else:
        mapping = 'djangofloor.conf.mapping:INI_MAPPING'
    config_providers += search_providers('settings', 'ini', IniConfigProvider)
    config_providers += search_providers('settings', 'py', PythonFileProvider)
    if script:
        config_providers += search_providers(script, 'ini', IniConfigProvider)
        config_providers += search_providers(script, 'py', PythonFileProvider)
    config_providers += [IniConfigProvider(local_conf_filename)]
    config_providers += [PythonFileProvider(os.path.abspath('local_settings.py'))]
    fields_provider = PythonConfigFieldsProvider(mapping)
    extra_values = {'DF_MODULE_NAME': module_name}
    if script:
        extra_values['SCRIPT_NAME'] = script
    else:
        extra_values['SCRIPT_NAME'] = 'noscript'
    return SettingMerger(fields_provider, config_providers, extra_values=extra_values)


def set_env(command_name: Union[str, None]=None, script_name: Union[str, None]=None):
    """Set the environment variable `DF_CONF_NAME` with the project name and the script name
    The value looks like "project_name:celery" or "project_name:django"

    determine the project name

        if the script is {xxx}-[gunicorn|manage][.py], then the project_name is assumed to be {xxx}
        if option --dfproject {xxx} is available, then the project_name is assumed to be {xxx}

    """

    # django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangofloor.conf.settings')
    if command_name is None:
        command_name = os.path.basename(sys.argv[0])
    # project name
    script_re = re.match(r'^([\w_\-.]+)-(\w+)(\.py|\.pyc)?$', command_name)
    if script_re:
        conf_name = '%s:%s' % (script_re.group(1), script_name or script_re.group(2))
    else:
        conf_name = 'djangofloor:django'
    os.environ.setdefault('DF_CONF_NAME', conf_name)
    return conf_name


def load_celery():
    """ Import Celery application unless Celery is disabled.
    Allow to automatically load tasks
    """
    from django.conf import settings
    if settings.USE_CELERY:
        from djangofloor.celery import app
        return app
    return None


def control():
    """
    A single command to rule them all… Replace django, gunicorn/aiohttp and celery commands.
    "myproject-ctl" command

    "worker" -> changed as "myproject-celery" "worker"
    "server" -> changed as "myproject-aiohttp"
    "celery" -> changed as "myproject-celery" command
    other value -> changed as "myproject-django" command

    """

    command = sys.argv[1] if len(sys.argv) >= 2 else None
    if command == 'worker':
        set_env(script_name='celery')
        return celery()
    elif command == 'celery':
        set_env(script_name='celery')
        del sys.argv[1]
        return celery()
    elif command == 'server':
        set_env(script_name='server')
        del sys.argv[1]
        from django.conf import settings
        return gunicorn()
    set_env(script_name='django')
    return django()


django = DjangoCommand()
gunicorn = GunicornCommand()
aiohttp = GunicornCommand()
celery = CeleryCommand()


def get_application(command_name: Union[str, None]=None, script_name: Union[str, None]=None):
    set_env(command_name=command_name, script_name=script_name)
    import django
    django.setup()
    from django.conf import settings
    logging.config.dictConfig(settings.LOGGING)
    from djangofloor.wsgi.aiohttp_runserver import get_application
    return get_application()


def uwsgi():
    set_env()
    from django.conf import settings
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    cmd = ['uwsgi', '--plugin', 'python', '--module', 'djangofloor.wsgi.uwsgi_runserver']
    parser.add_argument('--no-master', default=False, action='store_true',
                        help='disable master process')
    parser.add_argument('--no-http-websockets', default=False, action='store_true',
                        help='do not automatically detect websockets connections and put the session in raw mode')
    parser.add_argument('--no-enable-threads', default=False, action='store_true',
                        help='do not run each worker in prethreaded mode with the specified number of threads')
    parser.add_argument('--http-socket', default=settings.LISTEN_ADDRESS,
                        help='bind to the specified UNIX/TCP socket using HTTP protocol')
    parser.add_argument('--reload-mercy', default=5, type=int,
                        help='set the maximum time (in seconds) we wait for workers and other processes '
                             'to die during reload/shutdown')
    parser.add_argument('--worker-reload-mercy', default=5, type=int,
                        help='set the maximum time (in seconds) a worker can take to reload/shutdown (default is 5)')
    parser.add_argument('--mule-reload-mercy', default=5, type=int,
                        help='set the maximum time (in seconds) a mule can take to reload/shutdown (default is 5)')
    options, extra_args = parser.parse_known_args()
    if not options.no_master:
        cmd += ['--master']
    if not options.no_http_websockets:
        cmd += ['--http-websockets']
    if not options.no_enable_threads:
        cmd += ['--enable-threads']
    # cmd += ['--threads', text_type(options.threads)]
    cmd += ['--http-socket', options.http_socket, '--reload-mercy', str(options.reload_mercy),
            '--worker-reload-mercy', str(options.worker_reload_mercy),
            '--mule-reload-mercy', str(options.mule_reload_mercy)]
    cmd += list(extra_args)
    p = subprocess.Popen(cmd)
    p.wait()
    sys.exit(p.returncode)


def create_project():
    import djangofloor
    base_path = os.path.dirname(djangofloor.__file__)
    template_base_path = os.path.join(base_path, 'templates', 'djangofloor', 'create_project')
    template_values = {'today': datetime.date.today().strftime('%Y/%m/%d')}
    pipenv = find_executable('pipenv')
    default_values = [['project_name', 'Your new project name', 'MyProject'],
                      ['package_name', 'Python package name', ''],
                      ['version', 'Initial version', '0.1'],
                      ['dst_dir', 'Root project path', './project'],
                      ['use_celery', 'Use background tasks or websockets', 'y'],
                      ]
    if pipenv:
        default_values += [('use_pipenv', 'Use pipenv to create a working virtualenv', 'y')]
    for key, text, default_value in default_values:
        if key == 'package_name':
            default_value = re.sub(r'[^a-z0-9_]', '_', template_values['project_name'].lower())
            while default_value[0:1] in '0123456789_':
                default_value = default_value[1:]
            default_values[3][2] = './%s' % default_value
        value = None
        while not value:
            value = input('%s [%s] ' % (text, default_value))
            if not value:
                value = default_value
        template_values[key] = value
    dst_dir = template_values['dst_dir']

    if template_values['use_celery'] == 'y':
        template_values['settings'] = ''
    else:
        template_values['settings'] = """WEBSOCKET_URL = None\nUSE_CELERY = False\n"""

    if os.path.exists(dst_dir):
        value = ''
        while not value:
            value = input('\'%(dst_dir)s\' already exists. Do you want to remove it? [y/n] ' % template_values)
            value = value.lower()
            if value == 'n':
                return
            elif value != 'y':
                value = ''
        if os.path.isdir(dst_dir):
            shutil.rmtree(dst_dir)
        if os.path.exists(dst_dir):
            os.remove(dst_dir)

    for root, dirnames, filenames in os.walk(template_base_path):
        index = 0
        while index < len(dirnames):
            if dirnames[index] in ('__pycache__', ):
                del dirnames[index]
            else:
                index += 1
        for dirname in dirnames:
            src_path = os.path.join(root, dirname)
            dst_path = os.path.relpath(src_path, template_base_path)
            dst_path = dst_path.format(**template_values)
            dst_path = os.path.join(dst_dir, dst_path)
            print('%s -> %s' % (src_path, dst_path))
            if not os.path.isdir(dst_path):
                os.makedirs(dst_path)
        for filename in filenames:
            src_path = os.path.join(root, filename)
            dst_path = os.path.relpath(src_path, template_base_path)
            dst_path = dst_path.format(**template_values)
            if not dst_path.rpartition('/')[-1]:
                continue
            if dst_path.endswith('_tpl'):
                dst_path = dst_path[:-4]
            dst_path = os.path.join(dst_dir, dst_path)
            print('%s -> %s' % (src_path, dst_path))
            dirname = os.path.dirname(dst_path)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            with open(dst_path, 'w', encoding='utf-8') as out_fd:
                with open(src_path, 'r', encoding='utf-8') as in_fd:
                    content = in_fd.read().format(**template_values)
                    out_fd.write(content)

    if pipenv and template_values['use_pipenv'] == 'y':
        ctl = '%s-ctl.py' % template_values['package_name']
        env = os.environ.copy()
        if 'VIRTUAL_ENV' in env:
            del env['VIRTUAL_ENV']
        subprocess.check_call(['pipenv', 'check', '--venv'], cwd=dst_dir, env=env)
        subprocess.check_call(['pipenv', 'install'], cwd=dst_dir, env=env)
        subprocess.check_call(['pipenv', 'run', 'python', 'setup.py', 'develop'], cwd=dst_dir, env=env)
        subprocess.check_call(['pipenv', 'run', 'python', ctl, 'gen_dev_files', '.'], cwd=dst_dir, env=env)
