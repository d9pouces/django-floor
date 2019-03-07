"""load Celery and discover tasks
==============================

You should not use this module (or rename it), as it is only used to auto-discover tasks.

"""
import logging.config

from celery import Celery, signals
from django.apps import apps
from django.conf import settings

from djangofloor.scripts import set_env

__author__ = "Matthieu Gallet"
project_name = set_env()
app = Celery(project_name)
app.config_from_object(settings)

app.autodiscover_tasks([a.name for a in apps.app_configs.values()])


# noinspection PyUnusedLocal
@signals.setup_logging.connect
def setup_celery_logging(**kwargs):
    """Use to setup the logs, overriding the default Celery configuration """
    logging.config.dictConfig(settings.LOGGING)


# Moving the call here works
app.log.setup()
