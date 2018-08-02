"""DjangoFloor utility views
=========================

Also define two functions:

  * :meth:`read_file_in_chunks`: generate an iterator that reads a file object in chunks
  * :meth:`send_file`: return an efficient :class:`django.http.response.HttpResponse` for reading files
"""
import mimetypes
import os
import warnings
from collections import OrderedDict

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.syndication.views import add_domain
from django.http import HttpResponse
from django.http import HttpResponsePermanentRedirect
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.template.response import TemplateResponse
from django.templatetags.static import static
from django.urls import reverse
from django.utils.lru_cache import lru_cache
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from djangofloor.decorators import REGISTERED_SIGNALS, REGISTERED_FUNCTIONS, everyone

# noinspection PyProtectedMember
from djangofloor.tasks import import_signals_and_functions
from djangofloor.utils import RemovedInDjangoFloor200Warning
from djangofloor.wsgi.window_info import WindowInfo

__author__ = "Matthieu Gallet"


# noinspection PyUnusedLocal
def favicon(request):
    """Redirect "/favicon.ico" to the favicon in the static files """
    return HttpResponsePermanentRedirect(static("favicon/favicon.ico"))


def robots(request):
    """Basic robots file"""
    current_site = get_current_site(request)
    base_url = add_domain(current_site.domain, "/", request.is_secure())[:-1]
    template_values = {"base_url": base_url}
    return TemplateResponse(
        request, "djangofloor/robots.txt", template_values, content_type="text/plain"
    )


@lru_cache()
def __get_js_mimetype():
    # noinspection PyTypeChecker
    if hasattr(settings, "PIPELINE_MIMETYPES"):
        for (mimetype, ext) in settings.PIPELINE_MIMETYPES:
            if ext == ".js":
                return mimetype
    return "text/javascript"


def read_file_in_chunks(fileobj, chunk_size=32768):
    """ read a file object in chunks of the given size.

    Return an iterator of data

    :param fileobj:
    :param chunk_size: max size of each chunk
    :type chunk_size: `int`
    """
    for data in iter(lambda: fileobj.read(chunk_size), b""):
        yield data


@never_cache
def signals(request):
    """Generate a JS file with the list of signals. Also configure jQuery with a CSRF header for AJAX requests.
    """
    signal_request = WindowInfo.from_request(request)
    import_signals_and_functions()
    if settings.DF_PUBLIC_SIGNAL_LIST:
        valid_signal_names = list(REGISTERED_SIGNALS.keys())
        valid_function_names = list(REGISTERED_FUNCTIONS.keys())
    else:
        valid_signal_names = []
        for signal_name, list_of_connections in REGISTERED_SIGNALS.items():
            if any(
                x.is_allowed_to is everyone or x.is_allowed_to(x, signal_request, None)
                for x in list_of_connections
            ):
                valid_signal_names.append(signal_name)
        valid_function_names = []
        for function_name, connection in REGISTERED_FUNCTIONS.items():
            if connection.is_allowed_to is everyone or connection.is_allowed_to(
                connection, signal_request, None
            ):
                valid_function_names.append(function_name)

    function_names_dict = {}
    for name in valid_function_names:
        function_names_dict[name] = (
            'function(opts) { return $.df._wsCallFunction("%(name)s", opts); }'
            % {"name": name}
        )
        name, sep, right = name.rpartition(".")
        while sep == ".":
            function_names_dict.setdefault(name, "{}")
            name, sep, right = name.rpartition(".")
    functions = OrderedDict()
    for key in sorted(function_names_dict):
        functions[key] = function_names_dict[key]

    protocol = "wss" if settings.USE_SSL else "ws"
    site_name = "%s:%s" % (settings.SERVER_NAME, settings.SERVER_PORT)

    # noinspection PyTypeChecker
    csrf_header_name = getattr(settings, "CSRF_HEADER_NAME", "HTTP_X_CSRFTOKEN")
    template_values = {
        "SIGNALS": valid_signal_names,
        "FUNCTIONS": functions,
        "WEBSOCKET_HEARTBEAT": settings.WEBSOCKET_HEARTBEAT,
        "WEBSOCKET_HEADER": settings.WEBSOCKET_HEADER,
        "CSRF_COOKIE_NAME": settings.CSRF_COOKIE_NAME,
        "DEBUG": settings.DEBUG,
        "CSRF_HEADER_NAME": csrf_header_name[5:].replace("_", "-"),
    }
    if settings.WEBSOCKET_URL:
        template_values["WEBSOCKET_URL"] = "%s://%s%s" % (
            protocol,
            site_name,
            settings.WEBSOCKET_URL,
        )
    return TemplateResponse(
        request,
        "djangofloor/signals.html",
        template_values,
        content_type=__get_js_mimetype(),
    )


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
    :rtype: :class:`django.http.response.StreamingHttpResponse` or :class:`django.http.response.HttpResponse`
    """
    if mimetype is None:
        (mimetype, encoding) = mimetypes.guess_type(filepath)
        if mimetype is None:
            mimetype = "text/plain"
    if isinstance(mimetype, bytes):
        # noinspection PyTypeChecker
        mimetype = mimetype.decode("utf-8")
    filepath = os.path.abspath(filepath)
    response = None
    if settings.USE_X_SEND_FILE:
        response = HttpResponse(content_type=mimetype)
        response["X-SENDFILE"] = filepath
    elif settings.X_ACCEL_REDIRECT:
        for dirpath, alias_url in settings.X_ACCEL_REDIRECT:
            if filepath.startswith(dirpath):
                response = HttpResponse(content_type=mimetype)
                response["Content-Disposition"] = "attachment; filename={0}".format(
                    os.path.basename(filepath)
                )
                response["X-Accel-Redirect"] = alias_url + filepath
                break
    if response is None:
        # noinspection PyTypeChecker
        fileobj = open(filepath, "rb")
        response = StreamingHttpResponse(
            read_file_in_chunks(fileobj), content_type=mimetype
        )
        response["Content-Length"] = os.path.getsize(filepath)
    if force_download or not (
        mimetype.startswith("text") or mimetype.startswith("image")
    ):
        response["Content-Disposition"] = "attachment; filename={0}".format(
            os.path.basename(filepath)
        )
    return response


class IndexView(TemplateView):
    """index view using the default bootstrap3 view.
You can only override the default template or populate the context. """

    template_name = "djangofloor/bootstrap3/index.html"

    def get(self, request, *args, **kwargs):
        """single defined method"""
        context = self.get_context(request)
        return self.render_to_response(context)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_context(self, request):
        """provide the template context """
        return {}


def index(request):
    """.. deprecated:: 1.0"""
    warnings.warn(
        "djangofloor.views.index is deprecated. Use class-based index view instead.",
        RemovedInDjangoFloor200Warning,
    )
    if settings.FLOOR_INDEX is not None:
        return HttpResponseRedirect(reverse(settings.FLOOR_INDEX))
    template_values = {}
    return TemplateResponse(request, "djangofloor/index.html", template_values)
