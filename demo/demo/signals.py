# coding=utf-8
from __future__ import unicode_literals
from django.conf import settings
from django.template.loader import render_to_string
from djangofloor.decorators import connect, SerializedForm
from demo.forms import SimpleForm
from djangofloor.tasks import call, SESSION, BROADCAST, USER, WINDOW

__author__ = 'Matthieu Gallet'


# noinspection PyUnusedLocal
@connect(path='demo.test_signal', auth_required=False)
def test_signal(request):
    html = render_to_string('demo/modal_content.html')
    return [{'signal': 'df.modal.show', 'options': {'html': html}}]


# noinspection PyUnusedLocal
@connect(path='demo.test_form')
def test_form(request, form):
    form = SerializedForm(SimpleForm)(form)
    if form.is_valid() and form.cleaned_data['first_name']:
        return [{'signal': 'df.messages.info', 'options': {'html': 'Your name is %s' % form.cleaned_data['first_name']}}]
    return [{'signal': 'df.messages.error', 'options': {'html': 'Invalid form. You must provide your first name'}}]


@connect(path='demo.test_websocket')
def test_websocket(request):
    txt = 'native' if settings.FLOOR_USE_WS4REDIS else 'emulated'
    call('df.messages.success', request, WINDOW, html='[WINDOW] Message received and sent through %s websockets.' % txt)
    call('df.messages.warning', request, BROADCAST, html='[BROADCAST] Message received and sent through %s websockets.' % txt)
    call('df.messages.error', request, SESSION, html='[SESSION] Message received and sent through %s websockets.' % txt)
    call('df.messages.info', request, USER, html='[USER] Message received and sent through %s websockets.' % txt)


@connect(path='demo.test_celery', delayed=True)
def test_celery(request):
    print('Celery demo task done')
    call('df.messages.success', request, WINDOW, html='[WINDOW] This message has been received and sent through Celery and websockets.')
    call('df.messages.warning', request, BROADCAST, html='[BROADCAST] This message has been received and sent through Celery and websockets.')
    call('df.messages.error', request, SESSION, html='[SESSION] This message has been received and sent through Celery and websockets.')
    call('df.messages.info', request, USER, html='[USER] This message has been received and sent through Celery and websockets.')
