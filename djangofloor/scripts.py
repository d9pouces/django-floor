# coding=utf-8
""" "Main" functions for Django, Celery, Gunicorn and uWSGI
========================================================

Define "main" functions for your scripts using the Django `manage.py` system or Gunicorn/Celery/uWSGI.
"""
from __future__ import unicode_literals, absolute_import, print_function

import codecs
import logging
import logging.config
import os
import re
import shutil
import subprocess
import sys
from argparse import ArgumentParser

from django.utils.six import text_type
from djangofloor.conf.merger import SettingMerger
from djangofloor.conf.providers import PythonModuleProvider, PythonFileProvider, IniConfigProvider, \
    PythonConfigFieldsProvider

__author__ = 'Matthieu Gallet'


def __get_extra_option(name, default, *argnames):
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser.add_argument(*argnames, action='store', default=default)
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    return getattr(options, name)


def __set_default_option(options, name):
    option_name = name.replace('_', '-')
    if getattr(options, name):
        sys.argv += ['--%s' % option_name, text_type(getattr(options, name))]


def get_merger_from_env(read_only=False):
    """ Should be used after set_env(); determine all available settings in this order:

   * djangofloor.defaults
   * {project_name}.defaults (overrides djangofloor.defaults)
   * {root}/etc/{project_name}/settings.ini (overrides {project_name}.settings)
   * {root}/etc/{project_name}/settings.py (overrides {root}/etc/{project_name}/settings.ini)
   * ./local_settings.ini (overrides {root}/etc/{project_name}/settings.py)
   * ./local_settings.py (overrides ./local_settings.ini)

    """

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
    return SettingMerger(fields_provider, config_providers, extra_values=extra_values, read_only=read_only)


def set_env(command_name=None):
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
    script_re = re.match(r'^([\w_\-.]+)-(\w+)(\.py|\.pyc|)$',
                         command_name)
    if script_re:
        conf_name = '%s:%s' % (script_re.group(1), script_re.group(2))
    else:
        conf_name = __get_extra_option('dfproject', 'djangofloor', '--dfproject')
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
    """Main user function, with commands for deploying, migrating data, backup or running services
    """
    conf_name = set_env()
    project_name = conf_name.partition(':')[0]
    try:
        # noinspection PyPackageRequirements
        from gevent import monkey
        monkey.patch_all()
    except ImportError:
        # noinspection PyUnusedLocal
        monkey = None
    from django.conf import settings
    command_commands = settings.COMMON_COMMANDS
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    script, command = command_commands.get(cmd, (None, None))
    invalid_script = 'Invalid script name: %(cmd)s' % {'cmd': script}
    invalid_command = 'Usage: %(name)s %(cmd)s' % {'name': sys.argv[0], 'cmd': '|'.join(command_commands)}
    if cmd not in command_commands:
        print(invalid_command)
        return 1
    scripts = {'django': django, 'gunicorn': gunicorn, 'celery': celery, 'uwsgi': uwsgi, 'aiohttp': aiohttp}
    if script not in scripts:
        print(invalid_script)
        return 1
    os.environ['DF_CONF_NAME'] = '%s:%s' % (project_name, script)
    script_re = re.match(r'^([\w_\-.]+)-ctl(\.py|\.pyc|)$', os.path.basename(sys.argv[0]))
    if script_re:
        sys.argv[0] = '%s-%s%s' % (script_re.group(1), script, script_re.group(2))
    if command:
        sys.argv[1] = command
    else:
        sys.argv[1:2] = []
    return scripts[script]()


def django():
    """
    Main function, calling Django code for management commands. Retrieve some default values from Django settings.
    """
    set_env()
    from django.conf import settings
    from django.core.management import execute_from_command_line
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    options, extra_args = parser.parse_known_args()
    env_set = bool(os.environ.get('DF_CONF_SET', ''))
    if not env_set:
        if len(extra_args) >= 1 and extra_args[0] == 'runserver':
            sys.argv += [settings.LISTEN_ADDRESS]
        os.environ['DF_CONF_SET'] = '1'

    import django
    django.setup()
    from django.core import management
    commands = {x: y for (x, y) in management.get_commands().items() if x not in settings.DF_REMOVED_DJANGO_COMMANDS}

    def get_commands():
        return commands

    management.get_commands = get_commands

    return execute_from_command_line(sys.argv)


def gunicorn():
    """ wrapper around gunicorn. Retrieve some default values from Django settings.

    :return:
    """
    # noinspection PyPackageRequirements
    from gunicorn.app.wsgiapp import run
    set_env()
    from django.conf import settings
    use_gevent = False
    try:
        # noinspection PyPackageRequirements
        from gevent import monkey
        monkey.patch_all()
        use_gevent = True
    except ImportError:
        # noinspection PyUnusedLocal
        monkey = None
    logging.config.dictConfig(settings.LOGGING)
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser.add_argument('-b', '--bind', default=settings.LISTEN_ADDRESS)
    parser.add_argument('--reload', default=False, action='store_true')
    if use_gevent:
        parser.add_argument('-k', '--worker-class', default='geventwebsocket.gunicorn.workers.GeventWebSocketWorker')
    else:
        parser.add_argument('-k', '--worker-class', default='gunicorn.workers.gthread.ThreadWorker')
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    env_set = bool(os.environ.get('DF_CONF_SET', ''))
    if not env_set:
        os.environ['DF_CONF_SET'] = '1'
        __set_default_option(options, 'bind')
        __set_default_option(options, 'worker_class')
        if settings.DEBUG and not options.reload:
            sys.argv += ['--reload']
    application = 'djangofloor.wsgi.gunicorn_runserver:application'
    if application not in sys.argv:
        sys.argv.append(application)
    return run()


def aiohttp():
    set_env()
    from django.conf import settings
    import django as base_django
    if base_django.VERSION[:2] >= (1, 7):
        base_django.setup()
    logging.config.dictConfig(settings.LOGGING)
    from djangofloor.wsgi.aiohttp_runserver import run_server

    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser.add_argument('-b', '--bind', default=settings.LISTEN_ADDRESS)
    options, args = parser.parse_known_args()
    host, sep, port = options.bind.partition(':')
    host = host or settings.SERVER_NAME
    port = int(port) or settings.SERVER_PORT
    return run_server(host, port)


def celery():
    set_env()
    from celery.bin.celery import main as celery_main
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser.add_argument('-A', '--app', action='store', default='djangofloor')
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    __set_default_option(options, 'app')
    celery_main(sys.argv)


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
    cmd += ['--http-socket', options.http_socket, '--reload-mercy', text_type(options.reload_mercy),
            '--worker-reload-mercy', text_type(options.worker_reload_mercy),
            '--mule-reload-mercy', text_type(options.mule_reload_mercy)]
    cmd += list(extra_args)
    p = subprocess.Popen(cmd)
    p.wait()
    sys.exit(p.returncode)


# noinspection PyUnresolvedReferences
def create_project():
    import djangofloor
    inp = input
    if sys.version_info[0] == 2:
        # noinspection PyUnresolvedReferences
        inp = raw_input
    base_path = os.path.dirname(djangofloor.__file__)
    template_base_path = os.path.join(base_path, 'templates', 'djangofloor', 'create_project')
    template_values = {}
    default_values = [('project_name', 'Your new project name', 'MyProject'),
                      ('package_name', 'Python package name', ''),
                      ('version', 'Initial version', '0.1'),
                      ('dst_dir', 'Root project path', '.'),
                      ('use_celery', 'Use background tasks or websockets', 'y'),
                      ]
    for key, text, default_value in default_values:
        if key == 'package_name':
            default_value = re.sub('[^a-z0-9_]', '_', template_values['project_name'].lower())
            while default_value[0:1] in '0123456789_':
                default_value = default_value[1:]
        value = None
        while not value:
            value = inp('%s [%s] ' % (text, default_value))
            if not value:
                value = default_value
        template_values[key] = value
    dst_dir = template_values['dst_dir']

    if template_values['use_celery'] == 'y':
        template_values['celery_script'] = ("'%s-celery = djangofloor.scripts:celery',\n"
                                            "                                    ")  % template_values['package_name']
        template_values['celery_script_name'] = '%s-celery.py' % template_values['package_name']
    else:
        template_values['celery_script'] = ''
        template_values['celery_script_name'] = ''

    if os.path.exists(dst_dir):
        value = ''
        while not value:
            value = inp('%s already exists. Do you want to remove it? [Y/n]')
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
            with codecs.open(dst_path, 'w', encoding='utf-8') as out_fd:
                with codecs.open(src_path, 'r', encoding='utf-8') as in_fd:
                    content = in_fd.read().format(**template_values)
                    out_fd.write(content)
