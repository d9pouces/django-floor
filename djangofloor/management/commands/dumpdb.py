# -*- coding: utf-8 -*-
import os
from django.conf import settings
from django.core.management import BaseCommand
from djangofloor.dbadapters import BaseAdaptater

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')
        parser.add_argument('--filename', default=None)

    def handle(self, *args, **options):
        if args:
            selected_names = set(args)
        else:
            selected_names = set(settings.DATABASES)
        filename = options['filename']

        for name, db_options in settings.DATABASES.items():
            if name not in selected_names:
                continue
            if filename:
                if name != 'default':
                    filename, sep, ext = filename.rpartition('.')
                    filename = '%s-%s.%s' % (filename, name, ext)
                if not os.path.dirname(filename):
                    os.makedirs(os.path.dirname(filename))
            adaptater = BaseAdaptater.get_adaptater(name, db_options)
            adaptater.dump(filename=filename)
