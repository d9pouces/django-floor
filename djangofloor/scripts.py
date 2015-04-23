# coding=utf-8
from __future__ import unicode_literals, absolute_import

"""
Define a main() function, allowing you to manage your Django project.
"""
from argparse import ArgumentParser
import subprocess
import re
import os
import sys

from setuptools import Command


__author__ = 'flanker'


class TestCommand(Command):
    description = 'Run all Django tests from setup.py'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    # noinspection PyMethodMayBeStatic
    def run(self):
        manage()


# noinspection PyShadowingBuiltins
def check_extra_option(name, default, *argnames):
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]")
    parser.add_argument(*argnames, action='store', default=default)
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    return getattr(options, name)


def set_default_option(options, name, default_value):
    option_name = name.replace('_', '-')
    if getattr(options, name):
        sys.argv += ['--%s' % option_name, default_value]


def set_env():
    """
    Determine project-specific and user-specific settings.
    Set several environment variable, update sys.argv and return the name of current djangofloor project.


    1) determine the project name

        if the script is {xxx}-[gunicorn|manage][.py], then the project_name is assumed to be {xxx}
        if option --project {xxx} is available, then the project_name is assumed to be {xxx}

    2) determine project-specific settings

        project-specific settings are expected to be in the module {xxx}.floor_settings
        Can be overridden by the DJANGOFLOOR_PROJECT_SETTINGS environment variable.

    3) determine user-specific settings

        if option --conf_file {yyy} is available, the {yyy} is used as user-specific settings file
        else if {xxx}_configuration.py exists in working directory, then it is used.
        else if [prefix]/etc/{xxx}/settings.py exists, then it is used.
        Can be overridden by the DJANGOFLOOR_USER_SETTINGS environment variable.

    4) standard Django settings module is djangofloor.settings.

        of course, you can always leave out djangofloor's settings system and override DJANGO_SETTINGS_MODULE

    """
    # django settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangofloor.settings")

    # project name
    script_re = re.match(r'^([\w_\-\.]+)-(manage|gunicorn|celery|uwsgi)(\.py|\.pyc|)$', os.path.basename(sys.argv[0]))
    if 'DJANGOFLOOR_PROJECT_NAME' in os.environ:
        project_name = os.environ['DJANGOFLOOR_PROJECT_NAME']
    elif script_re:
        project_name = script_re.group(1)
    else:
        project_name = 'djangofloor'
    project_name = check_extra_option('dfproject', project_name, '--dfproject')
    os.environ.setdefault('DJANGOFLOOR_PROJECT_SETTINGS', '%s.defaults' % project_name)
    os.environ.setdefault('DJANGOFLOOR_PROJECT_NAME', project_name)

    conf_path = os.path.abspath(os.path.join('.', '%s_configuration.py' % project_name))
    if not os.path.isfile(conf_path):
        splitted_path = __file__.split(os.path.sep)
        if 'lib' in splitted_path:
            splitted_path = splitted_path[:splitted_path.index('lib')] + ['etc', project_name, 'settings.py']
            conf_path = os.path.sep.join(splitted_path)
            if not os.path.isfile(conf_path):
                conf_path = ''

    conf_path = check_extra_option('dfconf', conf_path, '--dfconf')
    os.environ.setdefault("DJANGOFLOOR_USER_SETTINGS", conf_path)
    return project_name


def manage():
    """
    Main function, calling Django code for management commands. Retrieve some default values from Django settings.
    """
    set_env()
    from django.conf import settings
    from django.core.management import execute_from_command_line
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]")
    options, extra_args = parser.parse_known_args()
    if len(extra_args) == 1 and extra_args[0] == 'runserver':
        sys.argv += [settings.BIND_ADDRESS]
    return execute_from_command_line(sys.argv)


def load_celery():
    """ Import Celery application unless Celery is disabled.
    Allow to automatically load tasks
    :return:
    """
    from django.conf import settings
    if not settings.USE_CELERY:
        return
    from djangofloor.celery import app
    return app


def gunicorn():
    """ wrapper around gunicorn. Retrieve some default values from Django settings.

    :return:
    """
    from gunicorn.app.wsgiapp import run

    set_env()
    from django.conf import settings
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]")
    parser.add_argument('-b', '--bind', action='store', default=None, help=settings.BIND_ADDRESS_HELP)
    # noinspection PyUnresolvedReferences
    parser.add_argument('-p', '--pid', action='store', default=None, help=settings.GUNICORN_PID_FILE_HELP)
    parser.add_argument('--forwarded-allow-ips', action='store', default=None)
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('-t', '--timeout', action='store', default=None, help=settings.REVERSE_PROXY_TIMEOUT_HELP)
    parser.add_argument('--proxy-allow-from', action='store', default=None,
                        help='Front-end\'s IPs from which allowed accept proxy requests (comma separate)')
    parser.add_argument('--error-logfile', action='store', default=None, help=settings.GUNICORN_ERROR_LOG_FILE_HELP)
    parser.add_argument('--access-logfile', action='store', default=None, help=settings.GUNICORN_ACCESS_LOG_FILE_HELP)
    parser.add_argument('--log-level', action='store', default=None, help=settings.GUNICORN_LOG_LEVEL_HELP)
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    if not options.debug and settings.DEBUG:
        sys.argv += ['--debug']
    set_default_option(options, 'bind', settings.BIND_ADDRESS)
    set_default_option(options, 'pid', settings.GUNICORN_PID_FILE)
    set_default_option(options, 'forwarded_allow_ips', ','.join(settings.REVERSE_PROXY_IPS))
    set_default_option(options, 'timeout', str(settings.REVERSE_PROXY_TIMEOUT))
    set_default_option(options, 'proxy_allow_from', ','.join(settings.REVERSE_PROXY_IPS))
    set_default_option(options, 'error_logfile', settings.GUNICORN_ERROR_LOG_FILE)
    set_default_option(options, 'access_logfile', settings.GUNICORN_ACCESS_LOG_FILE)
    set_default_option(options, 'log_level', settings.GUNICORN_LOG_LEVEL)

    application = 'djangofloor.wsgi_http:application'
    if application not in sys.argv:
        sys.argv.append(application)
    return run()


def celery():
    set_env()
    from celery.bin.celery import main as celery_main
    from django.conf import settings
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]")
    parser.add_argument('-A', '--app', action='store', default=settings.CELERY_APP, help=settings.BIND_ADDRESS_HELP)
    parser.add_argument('--pidfile', action='store', default=None, help=settings.GUNICORN_PID_FILE_HELP)
    parser.add_argument('--logfile', action='store', default=settings.CELERY_LOG_FILE)
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    set_default_option(options, 'app', 'djangofloor')
    set_default_option(options, 'pidfile', settings.GUNICORN_PID_FILE)
    celery_main(sys.argv)


def uwsgi():
    set_env()
    from django.conf import settings
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]")
    parser.add_argument('--mode', default='both', choices=('both', 'http', 'websockets'))
    parser.add_argument('-b', '--bind', action='store', default=settings.BIND_ADDRESS, help=settings.BIND_ADDRESS_HELP)
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    argv = list(sys.argv)
    # websocket + http
    # uwsgi --virtualenv /path/to/virtualenv --http :80 --gevent 100 --http-websockets --module wsgi
    # http only
    # uwsgi --virtualenv /path/to/virtualenv --socket /path/to/django.socket --buffer-size=32768 --workers=5 --master --module wsgi_django
    # websockets only
    # uwsgi --virtualenv /path/to/virtualenv --http-socket /path/to/web.socket --gevent 1000 --http-websockets --workers=2 --master --module wsgi_websocket

    if options.mode == 'both':
        argv += ['--module', 'djangofloor.wsgi']
        argv += ['--http', options.bind]
    elif options.mode == 'http':
        argv += ['--module', 'djangofloor.wsgi_http']
    elif options.mode == 'websocket':
        argv += ['--module', 'djangofloor.wsgi_websockets']

    # ok, we can now run uwsgi
    argv[0] = 'uwsgi'
    p = subprocess.Popen(argv)
    p.wait()
    sys.exit(p.returncode)