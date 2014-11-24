#coding=utf-8
import os

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, StreamingHttpResponse, HttpResponsePermanentRedirect
from django.contrib.sites.models import get_current_site
from django.contrib.syndication.views import add_domain
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from djangofloor.tasks import add


__author__ = 'flanker'


def read_file_in_chunks(fileobj, chunk_size=32768):
    while True:
        data = fileobj.read(chunk_size)
        if not data:
            break
        yield data


def send_file(xsend_path, mimetype=None):
    if settings.USE_X_SEND_FILE:
        response = HttpResponse(content_type=mimetype)
        response['Content-Disposition'] = 'attachment; filename={0}'.format(os.path.basename(xsend_path))
        response['X-SENDFILE'] = xsend_path
        return response
    for dirpath, alias_url in settings.X_ACCEL_REDIRECT_ARCHIVE:
        if xsend_path.startswith(dirpath):
            response = HttpResponse(content_type=mimetype)
            response['Content-Disposition'] = 'attachment; filename={0}'.format(os.path.basename(xsend_path))
            response['X-Accel-Redirect'] = alias_url + xsend_path
            return response
    fileobj = open(xsend_path, 'rb')
    response = StreamingHttpResponse(read_file_in_chunks(fileobj), content_type=mimetype)
    if mimetype[0:4] != 'text' and mimetype[0:5] != 'image':
        response['Content-Disposition'] = 'attachment; filename={0}'.format(os.path.basename(xsend_path))
    response['Content-Length'] = os.path.getsize(xsend_path)
    return response


def robots(request):
    current_site = get_current_site(request)
    base_url = add_domain(current_site.domain, '/', request.is_secure())[:-1]
    template_values = {'base_url': base_url}
    return render_to_response('djangofloor/robots.txt', template_values, RequestContext(request),
                              content_type='text/plain')


def index(request):
    if settings.FLOOR_INDEX is not None:
        return HttpResponsePermanentRedirect(reverse(settings.FLOOR_INDEX))
    template_values = {}
    return render_to_response('djangofloor/index.html', template_values, RequestContext(request))


def test(request):
    messages.info(request, _('Message test'))
    template_values = {}
    add.delay(4, 5)
    return render_to_response('djangofloor/index.html', template_values, RequestContext(request))
