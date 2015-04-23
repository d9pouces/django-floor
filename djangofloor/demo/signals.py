# coding=utf-8
from __future__ import unicode_literals
from djangofloor.decorators import connect, SerializedForm
from djangofloor.demo.forms import SimpleForm
from djangofloor.tasks import call, SESSION

__author__ = 'flanker'


# noinspection PyUnusedLocal
@connect(path='demo.test_signal')
def test_signal(request):
    return [{'signal': 'df.messages.warning', 'options': {'html': 'This is a server-side message'}}]


# noinspection PyUnusedLocal
@connect(path='demo.test_form')
def test_form(request, form):
    form = SerializedForm(SimpleForm)(form)
    if form.is_valid() and form.cleaned_data['first_name']:
        return [{'signal': 'df.messages.info', 'options': {'html': 'Your name is %s' % form.cleaned_data['first_name']}}]
    return [{'signal': 'df.messages.error', 'options': {'html': 'Invalid form. You must provide your first name'}}]


@connect(path='demo.test_websocket')
def test_websocket(request):
    call('df.messages.info', request, SESSION, html='This message has been sent through websockets.')


@connect(path='demo.test_redis')
def test_redis(request):
    call('df.messages.info', request, SESSION, html='This message has been received and sent through websockets.')


@connect(path='demo.test_celery', delayed=True)
def test_celery(request):
    call('df.messages.info', request, SESSION, html='This message has been received and sent through Celery and websockets.')
