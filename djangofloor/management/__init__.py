from django.conf import settings
from django.core.management import ManagementUtility, get_commands, color_style

__author__ = 'Matthieu Gallet'


class CleanedManagementUtility(ManagementUtility):
    def main_help_text(self, commands_only=False):
        """
        Returns the script's main help text, as a string.
        """
        if commands_only:
            usage = sorted(get_commands().keys())
        else:
            usage = [
                "",
                "Type '%s help <subcommand>' for help on a specific subcommand." % self.prog_name,
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
                usage.append(style.NOTICE(
                    "Note that only Django core commands are listed "
                    "as settings are not properly configured (error: %s)."
                    % self.settings_exception))

        return '\n'.join(usage)


def execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    if settings.DEVELOPMENT:
        utility = ManagementUtility(argv)
    else:
        utility = CleanedManagementUtility(argv)
    utility.execute()
