import os
import signal
import ssl

import time
from celery.bin.celery import main as celery_main
from django.conf import settings

from djangofloor.wsgi.aiohttp_runserver import run_server
from django.core.management import BaseCommand

from djangofloor.tasks import get_expected_queues


class Command(BaseCommand):

    child_pids = {}
    continue_loop = True

    def handle(self, *args, **options):
        expected_queues = get_expected_queues()
        signal.signal(signal.SIGINT, self.signal_handler)
        for queue in expected_queues:
            self.launch_celery(queue)
        self.launch_aiohttp()
        while self.continue_loop:
            time.sleep(0.5)

    def launch_celery(self, queue):
        pid = os.fork()
        if pid == 0:
            celery_main(['worker', '-Q', queue])
        else:
            self.child_pids[pid] = 'Celery worker for queue %s' % queue

    # noinspection PyUnusedLocal
    def signal_handler(self, sig, frame):
        self.continue_loop = False
        for k, v in self.child_pids.items():
            os.kill(k, signal.SIGINT)

    def launch_aiohttp(self):
        pid = os.fork()
        if pid == 0:
            if settings.DF_SERVER_SSL_KEY and settings.DF_SERVER_SSL_CERTIFICATE:
                sslcontext = ssl.create_default_context()
                sslcontext.load_cert_chain(settings.DF_SERVER_SSL_CERTIFICATE, settings.DF_SERVER_SSL_KEY)
            else:
                sslcontext = None
            host, sep, port = settings.LISTEN_ADDRESS.partition(':')
            run_server(host, port, sslcontext=sslcontext)
        else:
            self.child_pids[pid] = 'aiohttp worker'
