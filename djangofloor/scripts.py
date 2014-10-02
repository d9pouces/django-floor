#coding=utf-8
"""
Define a main() function, allowing you to manage your Django project.
"""
from django.conf import settings
import re

from djangofloor import defaults


__author__ = 'flanker'


import os
import sys
from django import get_version
from django.core.management import LaxOptionParser


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
    script_re = re.match('^(\w+)-(manage|gunicorn|celery)(\.py|\.pyc|)$', sys.argv[0])
    if 'DJANGOFLOOR_PROJECT_NAME' in os.environ:
        project_name = os.environ['DJANGOFLOOR_PROJECT_NAME']
    elif script_re:
        project_name = script_re.group(1)
    else:
        project_name = 'djangofloor'
    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", option_list=[])
    parser.add_option('--dfproject', action='store', default=project_name, help='DjangoFloor project name')
    options, args = parser.parse_args(sys.argv)
    project_name = options.dfproject
    os.environ.setdefault('DJANGOFLOOR_PROJECT_SETTINGS', '%s.defaults' % project_name)
    os.environ['DJANGOFLOOR_PROJECT_NAME'] = project_name
    sys.argv = args

    conf_path = os.path.abspath(os.path.join('.', '%s_configuration.py' % project_name))
    if not os.path.isfile(conf_path):
        splitted_path = __file__.split(os.path.sep)
        if 'lib' in splitted_path:
            splitted_path = splitted_path[:splitted_path.index('lib')] + ['etc', project_name, 'settings.py']
            conf_path = os.path.sep.join(splitted_path)
            if not os.path.isfile(conf_path):
                conf_path = ''

    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", option_list=[])
    parser.add_option('--dfconf', action='store', default=conf_path, help='configuration file')
    options, args = parser.parse_args(sys.argv)
    os.environ.setdefault("DJANGOFLOOR_USER_SETTINGS", options.dfconf)
    sys.argv = args
    return project_name


def manage():
    """
    Main function, calling Django code for management commands. Retrieve some default values from Django settings.
    """
    set_env()
    from django.core.management import execute_from_command_line
    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", option_list=[])
    parser.add_option('-v', '--verbosity', action='store')
    parser.add_option('--settings', action='store')
    parser.add_option('--pythonpath', action='store')
    parser.add_option('--traceback', action='store_true')
    parser.add_option('--no-color', action='store_true')
    parser.add_option('-6', '--ipv6', action='store_true')
    parser.add_option('--nothreading', action='store_true')
    parser.add_option('--nostatic', action='store_true')
    parser.add_option('--noreload', action='store_true')
    parser.add_option('--insecure', action='store_true')
    parser.add_option('--version', action='store_true')
    options, sub_args = parser.parse_args(sys.argv)
    if len(sub_args) >= 2 and sub_args[1] == 'runserver':
        if len(sub_args) == 2:
            sys.argv += [settings.BIND_ADDRESS]
    return execute_from_command_line(sys.argv)


def load_celery():
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
    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", version=get_version(), option_list=[])
    parser.add_option('-b', '--bind', action='store', default=None, help=defaults.BIND_ADDRESS_help)
    parser.add_option('-p', '--pid', action='store', default=None, help=defaults.PID_FILE_help)
    parser.add_option('--forwarded-allow-ips', action='store', default=None)
    parser.add_option('--debug', action='store_true', default=False)
    parser.add_option('-t', '--timeout', action='store', default=None, help=defaults.REVERSE_PROXY_TIMEOUT_help)
    parser.add_option('--proxy-allow-from', action='store', default=None,
                      help='Front-end\'s IPs from which allowed accept proxy requests (comma separate)')
    parser.add_option('--error-logfile', action='store', default=None, help=defaults.GUNICORN_ERROR_LOG_FILE_help)
    parser.add_option('--access-logfile', action='store', default=None, help=defaults.GUNICORN_ACCESS_LOG_FILE_help)
    parser.add_option('--log-level', action='store', default=None, help=defaults.GUNICORN_LOG_LEVEL_help)
    options, args = parser.parse_args(sys.argv)
    if options.bind is None:
        sys.argv += ['--bind', settings.BIND_ADDRESS]
    if options.pid is None:
        sys.argv += ['--pid', settings.PID_FILE]
    if options.forwarded_allow_ips is None:
        sys.argv += ['--forwarded-allow-ips', ','.join(settings.REVERSE_PROXY_IPS)]
    if not options.debug and settings.DEBUG:
        sys.argv += ['--debug']
    if options.timeout is None:
        sys.argv += ['--timeout', str(settings.REVERSE_PROXY_TIMEOUT)]
    if options.proxy_allow_from is None:
        sys.argv += ['--proxy-allow-from', ','.join(settings.REVERSE_PROXY_IPS)]
    if options.error_logfile is None:
        sys.argv += ['--error-logfile', settings.ERROR_LOG_FILE]
    if options.access_logfile is None:
        sys.argv += ['--access-logfile', settings.ACCESS_LOG_FILE]
    if options.log_level is None:
        sys.argv += ['--log-level', settings.GUNICORN_LOG_LEVEL]

    application = 'djangofloor.wsgi:application'
    if application not in sys.argv:
        sys.argv.append(application)
    return run()


def celery():
    from celery.bin.celery import main as celery_main
    set_env()
    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", version=get_version(), option_list=[])
    parser.add_option('-A', '--app', action='store', default=None, help=defaults.BIND_ADDRESS_help)
    options, args = parser.parse_args(sys.argv)
    if options.app is None:
        sys.argv += ['--app', 'djangofloor']
    celery_main(sys.argv)