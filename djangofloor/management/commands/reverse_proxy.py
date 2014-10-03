# coding=utf-8
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.translation import ugettext as _


class Command(BaseCommand):
    help = _('Display example configurations for Apache or NGinx')

    def get_template_values(self):

        return {'admins': settings.ADMINS,
                'bind_address': settings.BIND_ADDRESS}