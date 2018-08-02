from argparse import ArgumentParser

from django.core.management import BaseCommand
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from djangofloor.conf.settings import merger


class Command(BaseCommand):
    valid_commands = ["apache", "nginx", "supervisor", "systemd"]
    args = "<%s>" % "|".join(valid_commands)
    help = _("Display example configurations for Apache, NGinx or Supervisor")
    requires_system_checks = False

    def add_arguments(self, parser):
        assert isinstance(parser, ArgumentParser)
        parser.add_argument("config", default=[], nargs="*", help=self.help)

    def handle(self, *args, **options):
        commands = options["config"]
        if not commands:
            self.stderr.write(
                "Please provide at least one config %s" % "|".join(self.valid_commands)
            )
            return
        template_values = self.get_template_values()
        for cmd in commands:
            if cmd not in self.valid_commands:
                print("unknown command: %s" % cmd)
            else:
                template = "djangofloor/commands/%(cmd)s.conf" % {"cmd": cmd}
                string = render_to_string(template, template_values)
                self.stdout.write(string)

    # noinspection PyMethodMayBeStatic
    def get_template_values(self):
        return merger.settings
