import datetime
import hashlib
import os
import re
import shutil
import string
import sys
from argparse import ArgumentParser
from difflib import unified_diff
from email import message_from_string

import pkg_resources
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import (
    BaseCommand as OriginalBaseCommand,
    CommandError,
    handle_default_options,
)
from django.core.management.base import SystemCheckError
from django.db import connections
from django.template import TemplateDoesNotExist
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string

from djangofloor.checks import get_pipeline_requirements
from djangofloor.conf.providers import IniConfigProvider
from djangofloor.scripts import get_merger_from_env
from djangofloor.utils import remove_arguments_from_help, walk

__author__ = "Matthieu Gallet"


# noinspection PyClassHasNoInit
class BaseCommand(OriginalBaseCommand):
    """Create a Makefile """

    #
    # def create_parser(self, prog_name, subcommand):
    #     """
    #     Create and return the ``ArgumentParser`` which will be used to
    #     parse the arguments to this command.
    #     """
    #     parser = CommandParser(
    #         self,
    #         prog="%s %s" % (os.path.basename(prog_name), subcommand),
    #         description=self.help or None,
    #     )
    #     self.add_arguments(parser)
    #     return parser
    #
    # def set_default_options(self, options):
    #     options.version = self.get_version()
    #     options.verbosity = 0
    #     options.settings = None
    #     options.pythonpath = None
    #     options.traceback = False
    #     options.no_color = False

    def run_from_argv(self, argv):
        """
        Set up any environment changes requested (e.g., Python path
        and Django settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])

        options = parser.parse_args(argv[2:])
        # self.set_default_options(options)
        cmd_options = vars(options)
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop("args", ())
        handle_default_options(options)
        try:
            self.execute(*args, **cmd_options)
        except Exception as e:
            if options.traceback or not isinstance(e, CommandError):
                raise
            # SystemCheckError takes care of its own formatting.
            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write("%s: %s" % (e.__class__.__name__, e))
            sys.exit(1)
        finally:
            connections.close_all()

    def handle(self, *args, **options):
        raise NotImplementedError

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        pass


# noinspection PyClassHasNoInit
class TemplatedBaseCommand(OriginalBaseCommand):
    packaging_config_files = []
    transparent_suffix = "_tpl"
    ignored_suffix = "_inc"

    def handle(self, *args, **options):
        raise NotImplementedError

    def add_arguments(self, parser):
        assert isinstance(parser, ArgumentParser)
        parser.add_argument(
            "--config-file",
            help="Config file(s) to use",
            default=self.packaging_config_files,
            action="append",
        )
        parser.add_argument(
            "--dry",
            default=False,
            action="store_true",
            help="Dry mode: do not write any file",
        )
        remove_arguments_from_help(
            parser, {"--settings", "--traceback", "--pythonpath", "--no-color"}
        )

    @staticmethod
    def get_merger(config_files):
        merger = get_merger_from_env()
        for config_file in config_files:
            merger.add_provider(IniConfigProvider(os.path.abspath(config_file)))
        merger.process()
        merger.post_process()
        return merger

    def get_setup_context(self):
        """extract required informations from the setup.py command (like the description or the installed scripts)"""
        module_name = settings.DF_MODULE_NAME
        try:
            project_distribution = pkg_resources.get_distribution(module_name)
        except pkg_resources.DistributionNotFound:
            if hasattr(sys, "real_prefix"):  # we are inside a virtualenv
                self.stderr.write(
                    "You must run 'python setup.py install' or 'python setup.py develop' "
                    "before using this command"
                )
            else:
                self.stderr.write(
                    "You must run 'python3 setup.py install --user' or "
                    "'python3 setup.py develop --user' before using this command."
                )
            return {}
        context = {
            "version": project_distribution.version,
            "name": module_name,
            "processes": {},
            "control_command": None,
            "available_python_versions": [],
        }
        # analyze scripts to detect which processes to launch on startup
        entry_map = pkg_resources.get_entry_map(module_name)
        for script_name, entry_point in entry_map.get("console_scripts").items():
            script_value = entry_point.module_name
            if entry_point.attrs:
                script_value += ":%s" % entry_point.attrs[:1]
            if entry_point.extras:
                script_value += " %s" % entry_point.extras[:1]
            if (
                entry_point.module_name == "djangofloor.scripts"
                and entry_point.attrs == ("control",)
            ):
                context["control_command"] = entry_point.name
            context["processes"][script_name] = script_value
        # print(context['processes'])
        maintainer = [None, None]
        # noinspection PyBroadException
        pkg_info = project_distribution.get_metadata("PKG-INFO")
        msg = message_from_string(pkg_info)
        for k, v in msg.items():
            if v == "UNKNOWN":
                continue
            elif k == "License":
                context["license"] = v
            elif k == "Description":
                content = []
                for index, line in enumerate(v.splitlines()):
                    if index == 0:
                        content.append(line)
                    else:
                        content.append(line[8:])
                context["description"] = "\n".join(content)
            elif k == "Home-page":
                context["url"] = v
            elif k == "Author":
                maintainer[0] = v
            elif k == "Author-email":
                maintainer[1] = v
            elif k == "Classifier":
                matcher = re.match(r"Programming Language :: Python :: (3.\d+)", v)
                if matcher:
                    context["available_python_versions"].append(matcher.group(1))
        if maintainer[0] and maintainer[1]:
            context["maintainer"] = "%s <%s>" % tuple(maintainer)
            context["vendor"] = "%s <%s>" % tuple(maintainer)
        context["available_python_versions"].sort()
        context["requirements"] = [str(x) for x in project_distribution.requires()]
        return context

    @staticmethod
    def get_pipeline_context():
        """
        Return a dict with programs required by `django-pipeline` (like sass or livescript).
        Distinguishes between 'npm' and 'gem' packages.
        """
        return get_pipeline_requirements()

    def get_template_context(self, merger, extra_context):
        """

        :param merger: SettingMerger
        :param extra_context: list of "template_variable=value"
        :return: template context (dict)
        """
        context = {key: value for (key, value) in merger.settings.items()}
        context["year"] = datetime.datetime.now().year
        context["python_version"] = "python%s.%s" % (
            sys.version_info[0],
            sys.version_info[1],
        )
        context["use_python3"] = sys.version_info[0] == 3
        context["settings_merger"] = merger
        provider = IniConfigProvider()
        merger.write_provider(provider, include_doc=True)
        to_str = provider.to_str()
        context["settings_ini"] = to_str
        for variable in extra_context:
            key, sep, value = variable.partition(":")
            if sep != ":":
                self.stderr.write(
                    self.style.WARNING(
                        "Invalid variable %s (should be like KEY:VALUE)" % variable
                    )
                )
                continue
            context[key] = value
        return context

    @classmethod
    def browser_folder(
        cls, src_module, src_folder, searched_folder="templates/", context=None
    ):
        """Return the set of all filenames in the `src_folder` (relative to the `src_module` Python module).
        If the filename ends with '_tpl', then this suffix will be removed (for compatibility reasons).
        If the filename ends with '_inc', then it is ignored.

        Returned filenames are relative to this base folder.
        You can use formatted filenames: given the `{'var': 'myproject'}` context, the `'{var}/models.py'` filename
         will be returned as `'myproject/models.py'`.


        >>> m = TemplatedBaseCommand.browser_folder
        >>> result = m('djangofloor', 'djangofloor/test', context={'var': 'my_project'})
        >>> for x in sorted(result.items()):
        ...     print(x)
        ('subtest/index.html', 'djangofloor/test/subtest/index.html_tpl')
        ('subtest/my_project.txt', 'djangofloor/test/subtest/{var}.txt')
        ('text.txt', 'djangofloor/test/text.txt')

        """
        formatter = string.Formatter()
        result = {}
        template_root_len = len(searched_folder)
        filename_root_len = len(src_folder)
        if not src_folder.endswith("/"):
            filename_root_len += 1
        searched_base = searched_folder + src_folder
        if pkg_resources.resource_isdir(src_module, searched_base):
            for (root, dirnames, filenames) in walk(src_module, searched_base):
                for filename in filenames:
                    if filename.endswith(cls.ignored_suffix):
                        continue
                    src_path = os.path.join(root, filename)[template_root_len:]
                    if src_path.endswith(cls.transparent_suffix):
                        dst_path = src_path[
                            filename_root_len : -len(cls.transparent_suffix)
                        ]
                    else:
                        dst_path = src_path[filename_root_len:]
                    if context and "{" in dst_path:
                        format_values = {}
                        for (
                            literal_text,
                            field_name,
                            format_spec,
                            conversion,
                        ) in formatter.parse(dst_path):
                            if field_name is not None:
                                format_values[field_name] = context[field_name]
                        if format_values:
                            dst_path = formatter.format(dst_path, **format_values)
                    result[dst_path] = src_path
        return result

    def get_file_writers(self, searched_locations, context=None):
        writers = {}
        for (module_name, folder_name) in searched_locations:
            msg = "Looking for static files in %s:[static/]%s" % (
                module_name,
                folder_name,
            )
            self.stdout.write(self.style.SUCCESS(msg))
            new_templates = self.browser_folder(
                module_name, folder_name, searched_folder="static/", context=context
            )
            for target_filename, source_filename in new_templates.items():
                writers[target_filename] = StaticWriter(
                    target_filename,
                    source_filename,
                    stdout=self.stdout,
                    style=self.style,
                )
            msg = "Looking for template files in %s:[templates/]%s" % (
                module_name,
                folder_name,
            )
            self.stdout.write(self.style.SUCCESS(msg))
            new_templates = self.browser_folder(
                module_name, folder_name, searched_folder="templates/", context=context
            )
            for target_filename, template_filename in new_templates.items():
                writers[target_filename] = TemplateWriter(
                    target_filename,
                    template_filename,
                    stdout=self.stdout,
                    style=self.style,
                )
        return writers


class Writer:
    def __init__(self, target_filename, source_filename, stdout=sys.stdout, style=None):
        self.target_filename = target_filename
        self.source_filename = source_filename
        self.stdout = stdout
        self.style = style

    def write(
        self, target_directory=None, context=None, dry_mode=False, verbose_mode=False
    ):
        raise NotImplementedError

    @staticmethod
    def checksum(target_filename):
        sha1 = hashlib.sha1()
        with open(target_filename, "rb") as fd:
            for data in iter(lambda: fd.read(4096), b""):
                sha1.update(data)
            return sha1.hexdigest()

    def notice(self, msg):
        if self.style:
            self.stdout.write(self.style.MIGRATE_LABEL(msg))
        else:
            self.stdout.write(msg)

    def error(self, msg):
        if self.style:
            self.stdout.write(self.style.ERROR(msg))
        else:
            self.stdout.write(msg)


class TemplateWriter(Writer):
    def write(
        self, target_directory=None, context=None, dry_mode=False, verbose_mode=False
    ):
        target_filename = os.path.join(target_directory, self.target_filename)
        try:
            new_content = render_to_string(self.source_filename, context)
        except TemplateDoesNotExist as e:
            self.error("[ERROR]: %s: %s (does not exist)" % (self.source_filename, e))
            return
        except TemplateSyntaxError as e:
            self.error("[ERROR]: %s: %s (syntax error)" % (self.source_filename, e))
            return
        if len(new_content) == 0:
            self.notice("[SKIPPED]: %s (empty)" % self.source_filename)
            return
        new_checksum = hashlib.sha1(new_content.encode("utf-8")).hexdigest()
        if os.path.isfile(target_filename):
            previous_checksum = self.checksum(target_filename)
            if new_checksum == previous_checksum:
                self.notice("[SKIPPED]: %s (identical)" % self.source_filename)
                return
            elif verbose_mode:
                with open(target_filename, "r", encoding="utf-8") as fd:
                    previous_content = fd.read()
                for line in unified_diff(
                    previous_content.splitlines(),
                    new_content.splitlines(),
                    fromfile="%s-before" % target_filename,
                    tofile="%s-after" % target_filename,
                ):
                    self.stdout.write(line)
        if dry_mode:
            self.notice("[DRY]: %s -> %s" % (self.source_filename, target_filename))
            return
        self.notice("[OK] %s -> %s" % (self.source_filename, target_filename))
        pkg_resources.ensure_directory(target_filename)
        with open(target_filename, "w", encoding="utf-8") as fd:
            fd.write(new_content)


class StaticWriter(Writer):
    def write(
        self, target_directory=None, context=None, dry_mode=False, verbose_mode=False
    ):
        # noinspection PyUnusedLocal
        verbose_mode = verbose_mode
        # noinspection PyUnusedLocal
        context = context
        target_filename = os.path.join(target_directory, self.target_filename)
        source_absolute_path = finders.find(self.source_filename)
        new_checksum = self.checksum(source_absolute_path)
        if os.path.isfile(target_filename):
            previous_checksum = self.checksum(target_filename)
            if new_checksum == previous_checksum:
                self.notice("[SKIPPED]: %s (identical)" % source_absolute_path)
                return
        if dry_mode:
            self.notice("[DRY]: %s -> %s" % (source_absolute_path, target_filename))
            return
        self.notice("[OK] %s -> %s" % (source_absolute_path, target_filename))
        pkg_resources.ensure_directory(target_filename)
        try:
            os.link(source_absolute_path, target_filename)
        except OSError:
            shutil.copy(source_absolute_path, target_filename)
