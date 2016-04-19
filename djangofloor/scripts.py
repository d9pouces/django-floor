# coding=utf-8
""" "Main" functions for Django, Celery, Gunicorn and uWSGI
========================================================

Define "main" functions for your scripts using the Django `manage.py` system or Gunicorn/Celery/uWSGI.
"""
from __future__ import unicode_literals, absolute_import
from argparse import ArgumentParser
import subprocess
import re
import os
import sys

__author__ = 'Matthieu Gallet'


def __check_extra_option(name, default, *argnames):
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser.add_argument(*argnames, action='store', default=default)
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    return getattr(options, name)


def __set_default_option(options, name):
    option_name = name.replace('_', '-')
    if getattr(options, name):
        sys.argv += ['--%s' % option_name, getattr(options, name)]


def set_env():
    """Determine project-specific and user-specific settings and set several environment variable, update sys.argv and return the name of current djangofloor project.

    1) determine the project name

        if the script is {xxx}-[gunicorn|manage][.py], then the project_name is assumed to be {xxx}
        if option --project {xxx} is available, then the project_name is assumed to be {xxx}

    2) determine project-specific settings

        project-specific settings are expected to be in the module {xxx}.defaults
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
    project_name = __check_extra_option('dfproject', project_name, '--dfproject')
    project_name = project_name.replace('-', '_')
    os.environ.setdefault('DJANGOFLOOR_PROJECT_DEFAULTS', '%s.defaults' % project_name)
    os.environ.setdefault('DJANGOFLOOR_PROJECT_NAME', project_name)

    python_settings_path = os.path.abspath(os.path.join('.', '%s_configuration.py' % project_name))
    prefix = sys.prefix
    if prefix == '/usr':
        prefix = ''
    if not os.path.isfile(python_settings_path):
        python_settings_path = '%s/etc/%s/settings.py' % (prefix, project_name)
    ini_settings_path = os.path.abspath(os.path.join('.', '%s_configuration.ini' % project_name))
    if not os.path.isfile(ini_settings_path):
        ini_settings_path = '%s/etc/%s/settings.ini' % (prefix, project_name)

    python_settings_path = __check_extra_option('dfconf', os.path.abspath(python_settings_path), '--dfconf')
    os.environ.setdefault("DJANGOFLOOR_PYTHON_SETTINGS", python_settings_path)
    os.environ.setdefault("DJANGOFLOOR_INI_SETTINGS", os.path.abspath(ini_settings_path))
    os.environ.setdefault("DJANGOFLOOR_MAPPING", '%s.iniconf.INI_MAPPING' % project_name)
    return project_name


def load_celery():
    """ Import Celery application unless Celery is disabled.
    Allow to automatically load tasks
    """
    from django.conf import settings
    if settings.USE_CELERY:
        from djangofloor.celery import app
        return app
    return None


def manage():
    """
    Main function, calling Django code for management commands. Retrieve some default values from Django settings.
    """
    set_env()
    from django.conf import settings
    from django.core.management import execute_from_command_line
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    options, extra_args = parser.parse_known_args()
    if len(extra_args) == 1 and extra_args[0] == 'runserver':
        sys.argv += [settings.BIND_ADDRESS]
    return execute_from_command_line(sys.argv)


def gunicorn():
    """ wrapper around gunicorn. Retrieve some default values from Django settings.

    :return:
    """
    from gunicorn.app.wsgiapp import run

    set_env()
    from django.conf import settings
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser.add_argument('-b', '--bind', action='store', default=settings.BIND_ADDRESS, help=settings.BIND_ADDRESS_HELP)
    # parser.add_argument('--forwarded-allow-ips', action='store', default=','.join(settings.REVERSE_PROXY_IPS))
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('-t', '--timeout', action='store', default=str(settings.REVERSE_PROXY_TIMEOUT),
                        help=settings.REVERSE_PROXY_TIMEOUT_HELP)
    parser.add_argument('--proxy-allow-from', action='store', default=','.join(settings.REVERSE_PROXY_IPS),
                        help='Front-end\'s IPs from which allowed accept proxy requests (comma separate)')
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    __set_default_option(options, 'bind')
    # __set_default_option(options, 'forwarded_allow_ips')
    __set_default_option(options, 'timeout')
    __set_default_option(options, 'proxy_allow_from')
    application = 'djangofloor.wsgi_http:application'
    if application not in sys.argv:
        sys.argv.append(application)
    return run()


def celery():
    set_env()
    from celery.bin.celery import main as celery_main
    from django.conf import settings
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
    parser.add_argument('-A', '--app', action='store', default='djangofloor', help=settings.BIND_ADDRESS_HELP)
    options, extra_args = parser.parse_known_args()
    sys.argv[1:] = extra_args
    __set_default_option(options, 'app')
    celery_main(sys.argv)


def uwsgi():
    set_env()
    from django.conf import settings
    parser = ArgumentParser(usage="%(prog)s subcommand [options] [args]", add_help=False)
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
