from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as BaseCommand
)
from djangofloor.conf.settings import merger


# noinspection PyClassHasNoInit
class Command(BaseCommand):
    def handle(self, **options):
        merger.call_method_on_config_values("pre_collectstatic")
        super().handle(**options)
        merger.call_method_on_config_values("post_collectstatic")
