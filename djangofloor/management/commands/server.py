import sys

from django.conf import settings

from djangofloor.management.base import BaseCommand
from djangofloor.scripts import gunicorn, aiohttp


class Command(BaseCommand):
    """placeholder for the "server" command.
    This command is directly handled if the "control" script is setup.

    """
    help = "Launch the server process"

    def handle(self, *args, **options):
        while len(sys.argv) > 1:
            del sys.argv[1]
        return gunicorn()
