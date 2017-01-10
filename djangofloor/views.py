# coding=utf-8
"""Default index and views tied to the signal system
=================================================
"""
from __future__ import unicode_literals
import json
import mimetypes
import os

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.syndication.views import add_domain
from django.template.response import TemplateResponse
from django.utils.lru_cache import lru_cache
from django.utils.module_loading import import_string
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.six import string_types, binary_type

from djangofloor.decorators import REGISTERED_SIGNALS
from djangofloor.df_redis import fetch_signal_calls
from djangofloor.exceptions import InvalidRequest
from djangofloor.tasks import import_signals, df_call, RETURN, get_signal_decoder, get_signal_encoder

__author__ = 'Matthieu Gallet'
mimetypes.init()


def read_file_in_chunks(fileobj, chunk_size=32768):
    """ read a file object in chunks of the given size.

    Return an iterator of data

    :param fileobj:
    :param chunk_size: max size of each chunk
    :type chunk_size: `int`
    """
    for data in iter(lambda: fileobj.read(chunk_size), b''):
        yield data


@lru_cache()
def __get_js_mimetype():
    for (mimetype, ext) in settings.PIPELINE_MIMETYPES:
        if ext == '.js':
            return mimetype
    return 'text/javascript'


@never_cache
def signals(request):
    """Generate a HttpResponse to register Python signals from the JS side
    """
    import_signals()
    interval = settings.WS4REDIS_EMULATION_INTERVAL
    if isinstance(interval, int) and request.user.is_anonymous():
        interval = 0
    elif isinstance(interval, string_types):
        interval = import_string(interval)
    if callable(interval):
        interval = interval(request)
    return TemplateResponse(request, 'djangofloor/signals.html',
                            {'signals': REGISTERED_SIGNALS, 'use_ws4redis': settings.FLOOR_USE_WS4REDIS,
                             'CSRF_COOKIE_NAME': settings.CSRF_COOKIE_NAME,
                             'CSRF_HEADER_NAME': settings.CSRF_HEADER_NAME[5:].replace('_', '-'),
                             'WS4REDIS_EMULATION_INTERVAL': interval}, content_type=__get_js_mimetype())


@never_cache
def signal_call(request, signal):
    """ Called by JS code when websockets are not available. Allow to call Python signals from JS.
    Arguments are passed in the request body, serialized as JSON.

    :param request: Django HTTP request
    :param signal: name of the called signal
    :type signal: :class:`str`
    """
    import_signals()
    request.window_key = request.GET.get('window_key')
    if request.body:
        kwargs = json.loads(request.body.decode('utf-8'), cls=get_signal_decoder())
    else:
        kwargs = {}
    try:
        result = df_call(signal, request, sharing=RETURN, from_client=True, kwargs=kwargs)
    except InvalidRequest:
        result = []
    return JsonResponse(result, safe=False, encoder=get_signal_encoder())


@never_cache
def get_signal_calls(request):
    """ Regularly called by JS code when websockets are not available. Allows Python code to call JS signals.

    The polling frequency is set with `WS4REDIS_EMULATION_INTERVAL` (in milliseconds).

    Return all signals called by Python code as a JSON-list
    """
    request.window_key = request.GET.get('window_key')
    return JsonResponse(fetch_signal_calls(request), safe=False)


def send_file(filepath, mimetype=None, force_download=False):
    """Send a local file. This is not a Django view, but a function that is called at the end of a view.

    If `settings.USE_X_SEND_FILE` (mod_xsendfile is a mod of Apache), then return an empty HttpResponse with the
    correct header. The file is directly handled by Apache instead of Python.
    If `settings.X_ACCEL_REDIRECT_ARCHIVE` is defined (as a list of tuple (directory, alias_url)) and filepath is
    in one of the directories, return an empty HttpResponse with the correct header.
    This is only available with Nginx.

    Otherwise, return a StreamingHttpResponse to avoid loading the whole file in memory.

    :param filepath: absolute path of the file to send to the client.
    :param mimetype: MIME type of the file (returned in the response header)
    :param force_download: always force the client to download the file.
    :rtype: `StreamingHttpResponse` or `HttpResponse`
    """
    if mimetype is None:
        (mimetype, encoding) = mimetypes.guess_type(filepath)
        if mimetype is None:
            mimetype = 'text/plain'
    if isinstance(mimetype, binary_type):
        mimetype = mimetype.decode('utf-8')
    filepath = os.path.abspath(filepath)
    if settings.USE_X_SEND_FILE:
        response = HttpResponse(content_type=mimetype)
        response['X-SENDFILE'] = filepath
    else:
        for dirpath, alias_url in settings.X_ACCEL_REDIRECT:
            if filepath.startswith(dirpath):
                response = HttpResponse(content_type=mimetype)
                response['Content-Disposition'] = 'attachment; filename={0}'.format(os.path.basename(filepath))
                response['X-Accel-Redirect'] = alias_url + filepath
                break
        else:
            fileobj = open(filepath, 'rb')
            response = StreamingHttpResponse(read_file_in_chunks(fileobj), content_type=mimetype)
            response['Content-Length'] = os.path.getsize(filepath)
    if force_download or not (mimetype.startswith('text') or mimetype.startswith('image')):
        response['Content-Disposition'] = 'attachment; filename={0}'.format(os.path.basename(filepath))
    return response


def robots(request):
    current_site = get_current_site(request)
    base_url = add_domain(current_site.domain, '/', request.is_secure())[:-1]
    template_values = {'base_url': base_url}
    return TemplateResponse(request, 'djangofloor/robots.txt', template_values, content_type='text/plain')


def index(request):
    if settings.FLOOR_INDEX is not None:
        return HttpResponseRedirect(reverse(settings.FLOOR_INDEX))
    template_values = {}
    return TemplateResponse(request, 'djangofloor/index.html', template_values)
