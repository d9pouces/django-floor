# coding=utf-8
from __future__ import unicode_literals
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from djangofloor.demo.forms import SimpleForm
from djangofloor.demo.tasks import add

__author__ = 'flanker'


def test(request):
    messages.info(request, _('Message test'))
    # add.delay(4, 5)
    template_values = {'form': SimpleForm()}
    return render_to_response('demo/test.html', template_values, RequestContext(request))
