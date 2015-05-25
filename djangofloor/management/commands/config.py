# coding=utf-8
from __future__ import unicode_literals
import os

from django.conf import settings
from django.core.management import BaseCommand
from django.utils.six import u
from django.utils.translation import ugettext as _, ugettext_lazy

from djangofloor import defaults, __version__ as version
from djangofloor.settings import project_settings, user_settings, floor_settings, ini_config_mapping

__author__ = 'flanker'


class Command(BaseCommand):

    def show_config(self, kind, env_variable, path):
        values = {'kind': kind, 'var': env_variable, 'path': path, }
        msg = _('%(kind)s: %(path)s') % values
        if env_variable:
            msg += _(' (defined in environment by %(var)s)') % values
        if not path:
            self.stdout.write(self.style.WARNING(msg))
        elif os.path.isfile(path):
            self.stdout.write(self.style.MIGRATE_HEADING(msg))
        else:
            self.stdout.write(self.style.ERROR(msg))

    def handle(self, *args, **options):
        lazy_cls = ugettext_lazy('').__class__
        project_default_conf = project_settings.__file__
        if project_default_conf.endswith('.pyc'):
            project_default_conf = project_default_conf[:-1]
        djangofloor_default_conf = floor_settings.__file__
        if djangofloor_default_conf.endswith('.pyc'):
            djangofloor_default_conf = djangofloor_default_conf[:-1]
        self.stdout.write('-' * 80)
        self.stdout.write(self.style.WARNING(_('Djangofloor version %(version)s') % {'version': version, }))
        self.show_config(_('Python local configuration'), 'DJANGOFLOOR_PYTHON_SETTINGS', settings.USER_SETTINGS_PATH)
        self.show_config(_('INI local configuration'), 'DJANGOFLOOR_INI_SETTINGS', settings.DJANGOFLOOR_CONFIG_PATH)
        self.show_config(_('Default project settings'), 'DJANGOFLOOR_PROJECT_DEFAULTS', project_default_conf)
        self.show_config(_('Other default settings'), None, djangofloor_default_conf)
        self.stdout.write('-' * 80)
        self.stdout.write(self.style.MIGRATE_LABEL(_('List of available settings:')))
        all_keys = defaults.__dict__.copy()
        all_keys.update(project_settings.__dict__)
        keys = set([key for key in defaults.__dict__ if key == key.upper() and key + '_HELP' in all_keys])
        keys |= set([key for key in project_settings.__dict__ if key == key.upper() and key + '_HELP' in all_keys])
        keys = list(keys)
        keys.sort()
        for key in keys:
            if not all_keys[key + '_HELP']:
                continue
            value = all_keys[key]
            is_redefined = key in user_settings.__dict__ or key in ini_config_mapping
            is_changed = is_redefined and getattr(settings, key) != defaults.__dict__[key]
            if isinstance(value, lazy_cls):
                value = u(value)
            actual_value = (getattr(settings, key))
            values = {'key': key, 'help': all_keys[key + '_HELP'], 'default': value, 'actual': actual_value}
            if is_changed:
                self.stdout.write(self.style.WARNING('%(key)s = %(default)r:') % values)
            elif is_redefined:
                self.stdout.write(self.style.MIGRATE_LABEL('%(key)s = %(default)r:') % values)
            else:
                self.stdout.write(_('%(key)s = %(default)r:\n') % values)
            if value != actual_value:
                self.stdout.write(_('     (actual value: %(actual)r)') % values)
            self.stdout.write('     %(help)s\n\n' % values)

        self.stdout.write(self.style.MIGRATE_HEADING(_('Use djangofloor.utils.[DirectoryPath|FilePath]("/{directory}/path") instead of "/{directory}/path"'
                          ' to automatically create required directories.')))
