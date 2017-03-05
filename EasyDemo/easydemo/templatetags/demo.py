# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

import logging
import random

from django import template

__author__ = 'Matthieu Gallet'
register = template.Library()
logger = logging.getLogger('django.request')


@register.simple_tag(takes_context=False)
def demo_template_tag(log=None):
    value = random.randint(1, 10000)
    if log:
        logger.warning('Random value %s' % value)
    return str(value)
