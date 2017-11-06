from djangofloor.management.base import BaseCommand
from djangofloor.scripts import celery


class Command(BaseCommand):
    """placeholder for the "celery" "worker" command.
    This command is directly handled if the "control" script is setup.

    """
    help = "Launch the server process"

    def run_from_argv(self, argv):
        """
        Set up any environment changes requested (e.g., Python path
        and Django settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        return celery()

    def handle(self, *args, **options):
        return celery()
