# coding=utf-8
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.translation import ugettext as _

from djangofloor import defaults
from djangofloor.settings import project_settings as project


__author__ = 'flanker'


class Command(BaseCommand):
    def handle(self, *args, **options):
        conf_path = settings.USER_SETTINGS_PATH
        print(_('Configuration file: %(path)s') % {'path': conf_path})
        default_conf = defaults.__file__
        if default_conf.endswith('.pyc'):
            default_conf = default_conf[:-1]
        print(_('Default values: %(path)s') % {'path': default_conf})
        print('-' * 80)
        print(_('List of available settings:'))
        keys = set([key for key in defaults.__dict__ if key == key.upper() and key + '_help' in defaults.__dict__])
        keys |= set([key for key in project.__dict__ if key == key.upper() and key + '_help' in project.__dict__])
        keys = list(keys)
        keys.sort()
        for key in keys:
            print(_('%(key)s = %(default)r:\n     %(help)s\n') %
                  {'key': key, 'help': defaults.__dict__[key + '_help'], 'default': defaults.__dict__[key]})


if __name__ == '__main__':
    import doctest

    doctest.testmod()