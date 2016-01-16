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
        return [{'signal': 'df.notify.info', 'options': {'message': 'Your name is %s' %
                                                         form.cleaned_data['first_name']}}]
    return [{'signal': 'df.notify.error', 'options': {'message': 'Invalid form. You must fill all fields'}}]


@connect(path='demo.test_websocket')
def test_websocket(request):
    txt = 'native' if settings.FLOOR_USE_WS4REDIS else 'emulated'
    call('df.notify.success', request, WINDOW, message='[WINDOW] received and sent through %s websockets.' % txt)
    call('df.notify.warning', request, BROADCAST, message='[BROADCAST] received and sent through %s websockets.' % txt)
    call('df.notify.error', request, SESSION, message='[SESSION] received and sent through %s websockets.' % txt)
    call('df.notify.info', request, USER, message='[USER] received and sent through %s websockets.' % txt)


@connect(path='demo.test_celery', delayed=True)
def test_celery(request):
    print('Celery demo task done')
    call('df.notify.success', request, WINDOW, message='[WINDOW] received and sent through Celery and websockets.')
    call('df.notify.warning', request, BROADCAST, message='[BROADCAST] received and sent through Celery and websockets.')
    call('df.notify.error', request, SESSION, message='[SESSION] received and sent through Celery and websockets.')
    call('df.notify.info', request, USER, message='[USER] received and sent through Celery and websockets.')
