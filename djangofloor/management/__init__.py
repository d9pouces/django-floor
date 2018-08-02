import os

import sys
from django.conf import settings
from django.core.management import (
    ManagementUtility,
    get_commands,
    color_style,
    CommandParser,
    BaseCommand,
    base,
)

__author__ = "Matthieu Gallet"


def main_help_text(self, commands_only=False):
    """
    Returns the script's main help text, as a string.
    """
    if commands_only:
        usage = sorted(get_commands().keys())
    else:
        usage = [
            "",
            "Type '%s help <subcommand>' for help on a specific subcommand."
            % self.prog_name,
            "",
            "Available subcommands:",
        ]
        commands = []
        for name, app in get_commands().items():
            commands.append(name)
        style = color_style()
        for name in sorted(commands):
            usage.append("    %s" % name)
        # Output an extra note if settings are not properly configured
        if self.settings_exception is not None:
            usage.append(
                style.NOTICE(
                    "Note that only Django core commands are listed "
                    "as settings are not properly configured (error: %s)."
                    % self.settings_exception
                )
            )

    return "\n".join(usage)


def create_parser(self, prog_name, subcommand):
    """
    Create and return the ``ArgumentParser`` which will be used to
    parse the arguments to this command.
    """
    parser = CommandParser(
        self,
        prog="%s %s" % (os.path.basename(prog_name), subcommand),
        description=self.help or None,
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        action="store",
        dest="verbosity",
        default=1,
        type=int,
        choices=[0, 1, 2, 3],
        help="Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        dest="no_color",
        default=False,
        help="Don't colorize the command output.",
    )
    self.add_arguments(parser)
    return parser


def handle_default_options(options):
    """
    Include any default options that all commands should accept here
    so that ManagementUtility can handle them before searching for
    user commands.
    """
    options.settings = None
    options.pythonpath = None
    options.traceback = False
    if options.pythonpath:
        sys.path.insert(0, options.pythonpath)


def execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    if not settings.DEVELOPMENT:
        BaseCommand.create_parser = create_parser
        ManagementUtility.main_help_text = main_help_text
        base.handle_default_options = handle_default_options
    from django.core import management

    management.execute_from_command_line(argv=argv)
