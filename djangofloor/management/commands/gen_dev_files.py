"""Generate scripts (for creating packages) and documentation source.

One of the goal of this project is to standardize deployment methods. Documentation should also be standardized.

Takes two base folders (the one provided by DjangoFloor and one provided by your project).
Write all files which are in one of these folders. If a file is in both folders, then the one in DjangoFloor's
directory is ignored.

All these files are assumed to be Django templates. All Django settings are available as template variables.
If you override a default file by an empty one, this file will be ignored.

A few extra variables are currently added to the context:

  * `python_version` (like `python3.4`), corresponding to the current interpreter
  * `year` : datetime.datetime.now().year
  * `use_python3` : sys.version_info[0] == 3
  * `settings_merger` : :class:`djangofloor.utils.SettingMerger` with documentation settings

"""
from argparse import ArgumentParser

from django.conf import settings

from djangofloor.management.base import TemplatedBaseCommand
from djangofloor.tasks import get_expected_queues

__author__ = "Matthieu Gallet"


class Command(TemplatedBaseCommand):
    packaging_config_files = ["dev/config-doc.ini"]
    default_searched_locations = [
        ("djangofloor", "djangofloor/dev"),
        (settings.DF_MODULE_NAME, "%s/dev" % settings.DF_MODULE_NAME),
    ]
    include_folder = "djangofloor/include"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        assert isinstance(parser, ArgumentParser)
        parser.add_argument(
            "target", default=".", action="store", help='Target folder (probably ".")'
        )
        parser.add_argument(
            "--include",
            default=[],
            action="append",
            help="Where to search templates and static files.\n"
            ' If not used, use ["djangofloor:djangofloor/dev", "%s:%s/dev"].\n'
            'Syntax: "dotted.module.path:root/folder/from/templates". '
            "\nCan be used multiple times."
            % (settings.DF_MODULE_NAME, settings.DF_MODULE_NAME),
        )
        parser.add_argument(
            "--extra-context",
            nargs="*",
            help="Extra variable for the template system "
            "(--extra-context=NAME:VALUE)",
            default=[],
        )

    def handle(self, *args, **options):

        verbose_mode = options["verbosity"] > 1
        dry_mode = options["dry"]
        target_directory = options["target"]
        searched_locations = []
        for value in options["include"]:
            module_name, sep, folder_name = value.partition(":")
            if sep != ":":
                self.stderr.write('Invalid "include" value: %s' % value)
                continue
            searched_locations.append((module_name, folder_name))
        if not searched_locations:
            searched_locations = self.default_searched_locations

        if dry_mode:
            self.stdout.write(self.style.ERROR("[dry mode: no file will be written]"))
        extra_variables = options["extra_context"]
        config_files = options["config_file"]
        merger = self.get_merger(config_files)
        context = self.get_template_context(merger, extra_variables)
        if context is None:
            return
        writers = self.get_file_writers(searched_locations)
        for target_filename in sorted(writers):  # fix the writing order
            writer = writers[target_filename]
            writer.write(
                target_directory, context, dry_mode=dry_mode, verbose_mode=verbose_mode
            )

    def get_template_context(self, merger, extra_context):
        context = super().get_template_context(merger, extra_context)
        required_celery_queues = list(sorted(get_expected_queues()))
        setup_context = self.get_setup_context()
        if not setup_context:
            return None
        context.update(setup_context)
        context["LISTEN_PORT"] = settings.LISTEN_ADDRESS.partition(":")[2] or "8000"
        context["required_celery_queues"] = required_celery_queues
        context["pipeline"] = self.get_pipeline_context()
        context["INSTALL_ROOT"] = "/home/%s/.virtualenvs/%s" % (
            settings.DF_MODULE_NAME,
            settings.DF_MODULE_NAME,
        )
        return context
