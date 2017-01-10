# coding=utf-8
from __future__ import unicode_literals
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from demo.forms import SimpleForm
from demo.tasks import add
from django.views.decorators.cache import never_cache
from djangofloor.tasks import call

__author__ = 'Matthieu Gallet'


@never_cache
def test(request):
    messages.info(request, _('Message test'))
    # add.delay(4, 5)
    template_values = {'form': SimpleForm(),
                       'FLOOR_USE_WS4REDIS': settings.FLOOR_USE_WS4REDIS,
                       'USE_CELERY': settings.USE_CELERY,
                       'WS4REDIS_EMULATION_INTERVAL': settings.WS4REDIS_EMULATION_INTERVAL,
                       'window_key': request.window_key,
                       'session_key': request.session.session_key,
                       }
    call('demo.test_celery', request)
    return render_to_response('demo/test.html', template_values, RequestContext(request))
