# coding=utf-8
from __future__ import unicode_literals
import json
import mimetypes
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, StreamingHttpResponse, HttpResponsePermanentRedirect, JsonResponse, HttpResponseRedirect
from django.contrib.sites.models import get_current_site
from django.contrib.syndication.views import add_domain
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.lru_cache import lru_cache
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from djangofloor.decorators import REGISTERED_SIGNALS
from djangofloor.df_redis import fetch_signal_calls
from djangofloor.exceptions import InvalidRequest
from djangofloor.tasks import import_signals, df_call, RETURN

__author__ = 'flanker'
mimetypes.init()


def read_file_in_chunks(fileobj, chunk_size=32768):
    """ read a file object in chunks of the given size.

    Return an iterator of data
    :param fileobj:
    :param chunk_size: max size of each chunk
    :type chunk_size: `int`
    """
    while True:
        data = fileobj.read(chunk_size)
        if not data:
            break
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
    return render_to_response('djangofloor/signals.html',
                              {'signals': REGISTERED_SIGNALS, 'use_ws4redis': settings.FLOOR_USE_WS4REDIS,
                               'WS4REDIS_EMULATION_INTERVAL': settings.WS4REDIS_EMULATION_INTERVAL},
                              RequestContext(request), content_type=__get_js_mimetype())


@csrf_exempt
@never_cache
def signal_call(request, signal):
    """ Called by JS code when websockets are not available. Allow to call Python signals from JS.
    Arguments are passed in the request body, serialized as JSON.

    :param signal: name of the called signal
    """
    import_signals()
    if request.body:
        kwargs = json.loads(request.body.decode('utf-8'))
    else:
        kwargs = {}
    try:
        result = df_call(signal, request, sharing=RETURN, from_client=True, kwargs=kwargs)
    except InvalidRequest:
        result = []
    return JsonResponse(result, safe=False)


@never_cache
def get_signal_calls(request):
    """ Regularly called by JS code when websockets are not available. Allow Python code to call JS signals.

    Return all signals called by Python code as a JSON-list
    """
    return JsonResponse(fetch_signal_calls(request), safe=False)


def send_file(filepath, mimetype=None, force_download=False):
    """Send a static file. This is not a Django view, but rather a function that is called at the end of a view.

    If `settings.USE_X_SEND_FILE` (mod_xsendfile is a mod of Apache), then return an empty HttpResponse with the correct header.
    The file is directly handled by Apache instead of Python (that is more efficient).

    If `settings.X_ACCEL_REDIRECT_ARCHIVE` is defined (as a list of tuple (directory, alias_url)) and filepath is in one of the directories,
        return an empty HttpResponse with the correct header. This is only available with Nginx.

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
    return render_to_response('djangofloor/robots.txt', template_values, RequestContext(request),
                              content_type='text/plain')


def index(request):
    if settings.FLOOR_INDEX is not None:
        return HttpResponseRedirect(reverse(settings.FLOOR_INDEX))
    template_values = {}
    return render_to_response('djangofloor/index.html', template_values, RequestContext(request))
