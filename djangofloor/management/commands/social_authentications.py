import os
from argparse import ArgumentParser
from collections import OrderedDict
from configparser import RawConfigParser

from django.conf import settings

from djangofloor.conf.social_providers import (
    get_loaded_configurations,
    get_available_configurations,
    migrate,
)
from djangofloor.management.base import BaseCommand


class Command(BaseCommand):
    help = "Help you to add a social authentication to your website"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "action",
            help="show: display configured authentications,\n"
            "add: add another social authentication provider.",
        )

    def handle(self, **options):

        action = options["action"]
        try:
            if action == "show":
                self.show_config()
            elif action == "add":
                self.add_provider()
        except KeyboardInterrupt:
            self.stderr.write("\nCancelled.")

    def add_provider(self):
        providers = get_available_configurations()
        choices = OrderedDict(
            [
                (str(x + 1), y)
                for (x, y) in enumerate(
                    sorted(providers.values(), key=lambda x: x.provider_name)
                )
            ]
        )
        # select a provider
        self.stdout.write("Please select the provider to add:")
        for k, v in choices.items():
            self.stdout.write("[%s]: %s" % (k, v.provider_name))
        self.stdout.write("[0]: quit  ")
        while True:
            choice = input("")
            if choice == "0":
                return
            elif choice not in choices:
                self.stderr.write(
                    "Invalid choice (%s). Please enter a valid choice." % choice
                )
                continue
            provider = choices[choice]
            break
        if provider is None:
            return
        # check if the provider already exists in the current config file
        loaded_configurations = get_loaded_configurations()
        section = provider.provider_id
        if section in loaded_configurations:
            self.stderr.write(
                "%s is already defined. Overwrite its configuration? y/[N] "
            )
            if input().lower() != "y":
                return
        # get configuration for the selected provider
        content = provider.help_text
        self.stdout.write(content)
        new_values = {}
        for option, text in sorted(provider.attributes.items()):
            self.stdout.write(self.style.WARNING("%s:" % text))
            new_values[option] = input().strip()
        # update the config file
        parser = self.get_parser()
        if not parser.has_section(section):
            parser.add_section(section)
        parser.set(section, "django_app", provider.provider_app)
        for option, value in new_values.items():
            parser.set(section, option, value)
        self.stderr.write(
            "Write the configuration to %s? y/[N] "
            % settings.ALLAUTH_APPLICATIONS_CONFIG
        )
        if input().lower() != "y":
            return
        try:
            with open(settings.ALLAUTH_APPLICATIONS_CONFIG, "w") as fd:
                parser.write(fd)
            os.chmod(settings.ALLAUTH_APPLICATIONS_CONFIG, 0o600)
            self.stdout.write(
                self.style.SUCCESS(
                    'Do not forget to run the "migrate" command to load '
                    "this configuration and to restart all services."
                )
            )
        except Exception as e:
            self.stderr.write(
                "Unable to write %s (%s)." % (settings.ALLAUTH_APPLICATIONS_CONFIG, e)
            )

    def show_config(self):
        providers = get_loaded_configurations()
        self.stdout.write(
            self.style.SUCCESS(
                "configuration file: %s" % settings.ALLAUTH_APPLICATIONS_CONFIG
            )
        )
        self.stdout.write(self.style.SUCCESS("%d provider(s) found" % len(providers)))
        for provider in providers.values():
            self.stdout.write(
                self.style.SUCCESS("provider: %s" % provider.provider_name)
            )
            self.stdout.write("    Django app: %s" % provider.provider_app)
            for k, v in provider.values.items():
                self.stdout.write("    %s: %s" % (provider.attributes[k], v))
        if migrate(read_only=True):
            self.stdout.write(
                self.style.WARNING(
                    'Do not forget to run the "migrate" command to load '
                    "this configuration."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "database representations of these providers are valid."
                )
            )

    @classmethod
    def get_parser(cls):
        parser = RawConfigParser()
        if os.path.isfile(settings.ALLAUTH_APPLICATIONS_CONFIG):
            parser.read([settings.ALLAUTH_APPLICATIONS_CONFIG])
        return parser
