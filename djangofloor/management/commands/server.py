import sys

import os
from argparse import ArgumentParser

from django.conf import settings

from djangofloor.management.base import BaseCommand
from djangofloor.scripts import gunicorn


class Command(BaseCommand):
    """placeholder for the "server" command.
    This command is directly handled if the "control" script is setup.

    """
    help = "Launch the server process"

    def add_arguments(self, parser: ArgumentParser):
        if settings.WEBSOCKET_URL:
            worker_cls = 'aiohttp.worker.GunicornWebWorker'
        else:
            worker_cls = 'gunicorn.workers.gthread.ThreadWorker'
        parser.add_argument('-b', '--bind', default=settings.LISTEN_ADDRESS)
        parser.add_argument('--threads', default=settings.DF_SERVER_THREADS, type=int)
        parser.add_argument('-w', '--workers', default=settings.DF_SERVER_PROCESSES, type=int)
        parser.add_argument('--graceful-timeout', default=settings.DF_SERVER_GRACEFUL_TIMEOUT, type=int)
        parser.add_argument('--max-requests', default=settings.DF_SERVER_MAX_REQUESTS, type=int)
        parser.add_argument('--keep-alive', default=settings.DF_SERVER_KEEPALIVE, type=int)
        parser.add_argument('-t', '--timeout', default=settings.DF_SERVER_TIMEOUT, type=int)
        parser.add_argument('--keyfile', default=settings.DF_SERVER_SSL_KEY)
        parser.add_argument('--certfile', default=settings.DF_SERVER_SSL_CERTIFICATE)
        parser.add_argument('--reload', default=False, action='store_true')
        parser.add_argument('-k', '--worker-class', default=worker_cls)

    def handle(self, *args, **options):
        while len(sys.argv) > 1:
            del sys.argv[1]
        os.environ['DF_CONF_SET'] = ''
        return gunicorn()
