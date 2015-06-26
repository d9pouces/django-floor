# -*- coding: utf-8 -*-
import os
import subprocess
from django.conf import settings
from django.utils.translation import ugettext as _
import shutil

__author__ = 'Matthieu Gallet'


class BaseAdaptater(object):
    def __init__(self, name, db_options):
        self.name = name
        self.db_options = db_options

    def dump(self, filename):
        raise NotImplementedError

    @staticmethod
    def get_adaptater(name, db_options):
        engine = db_options['ENGINE'].lower()
        if 'mysql' in engine:
            return MySQL(name, db_options)
        elif 'postgresql' in engine:
            return PostgreSQL(name, db_options)
        elif 'sqlite' in engine:
            return SQLite(name, db_options)
        raise ValueError(_('Unknown database engine: %(ENGINE)s') % db_options)


class MySQL(BaseAdaptater):

    def dump(self, filename):
        cmd = self.dump_cmd_list()
        cmd = [x % self.db_options for x in cmd]
        env = os.environ.copy()
        env.update(self.get_env())
        if filename is not None:
            with open(filename, 'wb') as fd:
                p = subprocess.Popen(cmd, env=env, stdout=fd)
        else:
            p = subprocess.Popen(cmd, env=env)
        p.communicate()

    def dump_cmd_list(self):
        command = ['mysqldump',  '--user', '%(USER)s',  '--password', '%(PASSWORD)s']
        if self.db_options.get('HOST'):
            command += ['--host', '%(HOST)s']
        if self.db_options.get('PORT'):
            command += ['--port', '%(PORT)s']
        command += ['%(NAME)']
        return command

    def get_env(self):
        """Extra environment variables to be passed to shell execution"""
        return {}


class PostgreSQL(MySQL):

    def dump_cmd_list(self):
        command = ['pg_dump',  '--username', '%(USER)s']
        if self.db_options.get('HOST'):
            command += ['--host', '%(HOST)s']
        if self.db_options.get('PORT'):
            command += ['--port', '%(PORT)s']
        if settings.FLOOR_BACKUP_SINGLE_TRANSACTION:
            command += ['--single-transaction']
        command += ['%(NAME)']
        return command

    def get_env(self):
        """Extra environment variables to be passed to shell execution"""
        return {'PGPASSWORD': '%(PASSWORD)s' % self.db_options}


class SQLite(BaseAdaptater):

    def dump(self, filename):
        if filename is None:
            p = subprocess.Popen(['cat', self.db_options['NAME']])
            p.communicate()
        else:
            shutil.copy(self.db_options['NAME'], filename)
