# coding=utf-8
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.functional import lazy
from django.utils.translation import ugettext as _, ugettext_lazy

from djangofloor import defaults
from djangofloor.settings import project_settings as project


__author__ = 'flanker'


class Command(BaseCommand):
    def handle(self, *args, **options):
        lazy_cls = ugettext_lazy('').__class__
        conf_path = settings.USER_SETTINGS_PATH
        print(_('Configuration file: %(path)s') % {'path': conf_path})
        default_conf = defaults.__file__
        if default_conf.endswith('.pyc'):
            default_conf = default_conf[:-1]
        print(_('Default values: %(path)s') % {'path': default_conf})
        print('-' * 80)
        print(_('List of available settings:'))
        all_keys = defaults.__dict__.copy()
        all_keys.update(project.__dict__)
        keys = set([key for key in defaults.__dict__ if key == key.upper() and key + '_HELP' in all_keys])
        keys |= set([key for key in project.__dict__ if key == key.upper() and key + '_HELP' in all_keys])
        keys = list(keys)
        keys.sort()
        for key in keys:
            if all_keys[key + '_HELP']:
                value = all_keys[key]
                if isinstance(value, lazy_cls):
                    value = str(value)
                print(_('%(key)s = %(default)r:\n     %(help)s\n') %
                      {'key': key, 'help': all_keys[key + '_HELP'], 'default': value})

        print(_('Use djangofloor.utils.[DirectoryPath|FilePath]("/{directory}/path") instead of "/{directory}/path"'
                ' to automatically create required directories.'))


if __name__ == '__main__':
    import doctest

    doctest.testmod()