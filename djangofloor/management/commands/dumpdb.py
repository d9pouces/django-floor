"""
Dump the content of the databases to stdout or to a file.

Currently only works for sqlite, mysql and postresql.
"""
import os
import shutil
import subprocess
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.translation import ugettext as _

__author__ = "Matthieu Gallet"


class BaseDumper:
    """ base class for a given database engine. An instance is returned by :py:func:`Command.get_dumper` """

    def __init__(self, name, db_options):
        self.name = name
        self.db_options = db_options

    def dump(self, filename):
        """ dump the content of the database to `stdout` or to a `file`.

        If `filename` is given, its parent directory must already exist.

        :param filename: filename, or None if the content is must be dumped to `stdout`
        :type filename: :class:`str` or `None`
        :return: `None`
        """
        raise NotImplementedError


class MySQL(BaseDumper):
    """ dump the content of a MySQL database, with `mysqldump`"""

    def dump(self, filename):
        cmd = self.dump_cmd_list()
        cmd = [x % self.db_options for x in cmd]
        env = os.environ.copy()
        env.update(self.get_env())
        if filename is not None:
            with open(filename, "wb") as fd:
                p = subprocess.Popen(cmd, env=env, stdout=fd)
        else:
            p = subprocess.Popen(cmd, env=env)
        p.communicate()

    def dump_cmd_list(self):
        """ :return:
        :rtype: :class:`list` of :class:`str`
        """
        command = ["mysqldump", "--user", "%(USER)s", "--password=%(PASSWORD)s"]
        if self.db_options.get("HOST"):
            command += ["--host", "%(HOST)s"]
        if self.db_options.get("PORT"):
            command += ["--port", "%(PORT)s"]
        command += ["%(NAME)s"]
        return command

    def get_env(self):
        """Extra environment variables to be passed to shell execution"""
        return {}


class PostgreSQL(MySQL):
    """ dump the content of a PostgreSQL database, with `pg_dump`"""

    def dump_cmd_list(self):
        command = ["pg_dump", "--username", "%(USER)s"]
        if self.db_options.get("HOST"):
            command += ["--host", "%(HOST)s"]
        if self.db_options.get("PORT"):
            command += ["--port", "%(PORT)s"]
        if settings.FLOOR_BACKUP_SINGLE_TRANSACTION:
            command += ["--single-transaction"]
        command += ["%(NAME)s"]
        return command

    def get_env(self):
        """Extra environment variables to be passed to shell execution"""
        return {"PGPASSWORD": "%(PASSWORD)s" % self.db_options}


class SQLite(BaseDumper):
    """copy the SQLite database to another file, or write its content to `stdout`"""

    def dump(self, filename):
        if filename is None:
            p = subprocess.Popen(["cat", self.db_options["NAME"]])
            p.communicate()
        else:
            shutil.copy(self.db_options["NAME"], filename)


class Command(BaseCommand):
    """Dump the content of one (or more) database for backup to stdout or to a file.

    Just call the pg_dump/mysql_dump/… tools, allowing you to forget questions about their syntax.
    Currently only works for sqlite, mysql and postresql databases.

      * If no database is given, only the default one is dumped,
      * if multiple databases are given, all their dumps will be dumped and merged to stdout!
      * if `--filename` is given, the content is dumped to this file (without compression),
      * if `--filename` is given (say, "backup.sql") and multiple databases are given,
        the written file will be "backup-default.sql", "backup-other.sql", and so on).

    """

    help = "Dump the content of one (or more) database"

    def add_arguments(self, parser):
        parser.add_argument(
            "args",
            nargs="*",
            help="Name of the databases to dump. If not given, the default database is dumped.",
        )
        parser.add_argument(
            "--filename",
            default=None,
            help="Destination file for the dump. "
            "If multiple databases are selected, the written file is named filename-$database.ext",
        )

    def handle(self, *args, **options):
        """ execute the command"""
        if args:
            selected_names = set(args)
        else:
            # noinspection PySetFunctionToLiteral
            selected_names = set(["default"])
        filename = options["filename"]

        for name, db_options in settings.DATABASES.items():
            if name not in selected_names:
                continue
            if filename:
                if len(options) > 1:
                    filename, sep, ext = filename.rpartition(".")
                    filename = "%s-%s.%s" % (filename, name, ext)
                if not os.path.dirname(filename):
                    os.makedirs(os.path.dirname(filename))
            adaptater = self.get_dumper(name, db_options)
            adaptater.dump(filename=filename)

    @staticmethod
    def get_dumper(name, db_options):
        """ return a valid dumper for the given database, based on the `ENGINE` key.

        :param name: name of the database (one of the keys in the `DATABASES` setting)
        :type name: :class:`str`
        :param db_options: dictionnary  (one of the values in the `DATABASES` setting)
        :type db_options: :class:`dict`
        :rtype: :class:`BaseDumper`
        """
        engine = db_options["ENGINE"].lower()
        if "mysql" in engine:
            return MySQL(name, db_options)
        elif "postgresql" in engine:
            return PostgreSQL(name, db_options)
        elif "sqlite" in engine:
            return SQLite(name, db_options)
        raise ValueError(_("Unknown database engine: %(ENGINE)s") % db_options)
