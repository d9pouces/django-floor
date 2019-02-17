import os

from djangofloor.scripts import django, set_env

__author__ = "Matthieu Gallet"
os.environ["DJANGO_SETTINGS_MODULE"] = "djangofloor.conf.settings"

set_env(command_name="djangofloor-django")
django()
