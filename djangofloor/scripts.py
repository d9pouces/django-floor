# coding=utf-8
"""
Define a main() function, allowing you to manage your Django project.
"""
import re

from setuptools import Command


__author__ = 'flanker'


import os
import sys
from django import get_version
from django.core.management import LaxOptionParser


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
    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", option_list=[])
    parser.add_option(*argnames, action='store', default=None)
    options, args = parser.parse_args(sys.argv)
    value = getattr(options, name)
    if value is not None:
        for arg in argnames:
            dfindex = sys.argv.index(arg)
            del sys.argv[dfindex]
            del sys.argv[dfindex]
            break
        return value
    return default


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
    script_re = re.match(r'^([\w_]+)-(manage|gunicorn|celery)(\.py|\.pyc|)$', os.path.basename(sys.argv[0]))
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
    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", option_list=[])
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
    from django.conf import settings
    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", version=get_version(), option_list=[])
    parser.add_option('-b', '--bind', action='store', default=None, help=settings.BIND_ADDRESS_HELP)
    # noinspection PyUnresolvedReferences
    parser.add_option('-p', '--pid', action='store', default=None, help=settings.GUNICORN_PID_FILE_HELP)
    parser.add_option('--forwarded-allow-ips', action='store', default=None)
    parser.add_option('--debug', action='store_true', default=False)
    parser.add_option('-t', '--timeout', action='store', default=None, help=settings.REVERSE_PROXY_TIMEOUT_HELP)
    parser.add_option('--proxy-allow-from', action='store', default=None,
                      help='Front-end\'s IPs from which allowed accept proxy requests (comma separate)')
    parser.add_option('--error-logfile', action='store', default=None, help=settings.GUNICORN_ERROR_LOG_FILE_HELP)
    parser.add_option('--access-logfile', action='store', default=None, help=settings.GUNICORN_ACCESS_LOG_FILE_HELP)
    parser.add_option('--log-level', action='store', default=None, help=settings.GUNICORN_LOG_LEVEL_HELP)
    options, args = parser.parse_args(sys.argv)
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

    application = 'djangofloor.wsgi:application'
    if application not in sys.argv:
        sys.argv.append(application)
    return run()


def celery():
    from celery.bin.celery import main as celery_main
    set_env()
    from django.conf import settings
    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", version=get_version(), option_list=[])
    parser.add_option('-A', '--app', action='store', default=settings.CELERY_APP, help=settings.BIND_ADDRESS_HELP)
    parser.add_option('--pidfile', action='store', default=None, help=settings.GUNICORN_PID_FILE_HELP)
    parser.add_option('--logfile', action='store', default=settings.CELERY_LOG_FILE)
    options, args = parser.parse_args(sys.argv)
    set_default_option(options, 'app', 'djangofloor')
    set_default_option(options, 'pidfile', settings.GUNICORN_PID_FILE)
    celery_main(sys.argv)