"""Display some system info
========================

A class-based monitoring view, allowing to display some info.

Also define several widgets (:class:`MonitoringCheck`) that compose this view.
You should install the :mod:`psutil` module to add server info (like the CPU usage).


"""
import datetime
import logging
import os
import re

import pkg_resources
from django.conf import settings
from django.contrib import messages
from django.contrib.admin import site
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.checks import Info, Warning
from django.http import Http404
from django.http.response import HttpResponseRedirect
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from pkg_resources import parse_requirements, Distribution

from djangofloor.celery import app
from djangofloor.checks import settings_check_results
from djangofloor.conf.settings import merger
from djangofloor.forms import LogNameForm
from djangofloor.tasks import (
    set_websocket_topics,
    import_signals_and_functions,
    get_expected_queues,
)
from djangofloor.views.admin import admin_context

try:
    # noinspection PyPackageRequirements
    import psutil

    psutil.cpu_percent()
except ImportError:
    psutil = None

__author__ = "Matthieu Gallet"
logger = logging.getLogger("django.request")

stdlib_pkgs = ("python", "wsgiref", "argparse")


def get_installed_distributions():
    """
    Return a list of installed Distribution objects.
    Simplified version of the version provided by pip.
    """
    return [
        d
        for d in pkg_resources.working_set
        if d.key not in ("python", "wsgiref", "argparse")
    ]


class MonitoringCheck:
    """Base widget of the monitoring view."""

    template = None
    """name of the template used by this widget"""
    frequency = None
    """update frequency (currently unused)."""

    def render(self, request):
        """render the widget as HTML"""
        template = get_template(self.template)
        context = self.get_context(request)
        content = template.render(context, request)
        return mark_safe(content)

    def get_context(self, request):
        """ provide the context required to render the widget"""
        return {}

    def check_commandline(self):
        pass


class Packages(MonitoringCheck):
    """Check a list of given packages given by `settings.DF_CHECKED_REQUIREMENTS`.
    Each element is a requirement as listed by `pip freeze`.
    """

    template = "djangofloor/django/monitoring/packages.html"
    """base template """

    def get_context(self, request):
        """provide the installed distributions to the template"""
        distributions = self.get_installed_distributions(
            get_installed_distributions(), settings.DF_CHECKED_REQUIREMENTS
        )
        return {"installed_distributions": distributions}

    @staticmethod
    def get_installed_distributions(raw_installed_distributions, raw_requirements):
        """return a list of lists, each sublist having 6 elements:

            * the name of the package,
            * the installed version (or `None` if not installed),
            * the state ("danger"/"warning"/"success") as a CSS class,
            * the icon ("remove"/"ok"/"warning-sign")
            * list of specs as strings ['>= 1', '< 1.8.1']
            * list of parse_requirements(r) for the package

        """
        if raw_requirements:
            requirements = {}  # requirements[key] = [key, state="danger/warning/success", [specs_str], [parsed_req]]
            for r in raw_requirements:
                for p in parse_requirements(r):
                    requirements.setdefault(
                        p.key, [p.key, None, "danger", "remove", [], []]
                    )
                    requirements[p.key][4] += [" ".join(y) for y in p.specs]
                    requirements[p.key][5].append(p)
            for r in raw_installed_distributions:
                if r.key not in requirements:
                    continue
                requirements[r.key][1] = r.version
                d = Distribution(project_name=r.key, version=r.version)
                if requirements[r.key][2] == "danger":
                    requirements[r.key][2] = "success"
                    requirements[r.key][3] = "ok"
                for p in requirements[r.key][5]:
                    if d not in p:
                        requirements[r.key][2] = "warning"
                        requirements[r.key][3] = "warning-sign"
            installed_distributions = list(
                sorted(requirements.values(), key=lambda k: k[0].lower())
            )
        else:
            installed_distributions = [
                [y.key, y.version, "success", "ok", ["== %s" % y.version, [], []], []]
                for y in raw_installed_distributions
            ]
        return installed_distributions


class System(MonitoringCheck):
    template = "djangofloor/django/monitoring/system.html"
    excluded_mountpoints = {"/dev"}

    def get_context(self, request):
        if psutil is None:
            return {
                "cpu_count": None,
                "memory": None,
                "cpu_average_usage": None,
                "cpu_current_usage": None,
                "swap": None,
                "disks": None,
            }
        y = psutil.cpu_times()
        cpu_average_usage = int(
            (y.user + y.system) / (y.idle + y.user + y.system) * 100.
        )
        cpu_current_usage = int(psutil.cpu_percent(interval=0.1))
        cpu_count = psutil.cpu_count(logical=True), psutil.cpu_count(logical=False)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disks = []
        for y in psutil.disk_partitions(all=True):
            if y.mountpoint in self.excluded_mountpoints:
                continue
            # noinspection PyBroadException
            try:
                disk_data = (y.mountpoint, psutil.disk_usage(y.mountpoint))
                if disk_data[1].total > 0:
                    disks.append(disk_data)
            except Exception:
                pass
        # disks = [(y.mountpoint, psutil.disk_usage(y.mountpoint)) for y in psutil.disk_partitions(all=True)]
        # disks = [x for x in disks if x[1].total > 0]
        return {
            "cpu_count": cpu_count,
            "memory": memory,
            "cpu_average_usage": cpu_average_usage,
            "cpu_current_usage": cpu_current_usage,
            "swap": swap,
            "disks": disks,
        }

    @staticmethod
    def check_pid(pid: str):
        try:
            os.kill(int(pid), 0)
        except OSError:
            return False
        else:
            return True

    def check_commandline(self):
        if psutil is None:
            return
        for y in psutil.disk_partitions(all=True):
            if y.mountpoint in self.excluded_mountpoints:
                continue
            # noinspection PyBroadException
            try:
                usage = psutil.disk_usage(y.mountpoint)
                if usage.total > 0 and usage.percent > 95:
                    msg = "%s is almost full (%s %%)." % (y.mountpoint, usage.percent)
                    settings_check_results.append(Info(msg, obj="system"))
            except Exception:
                pass
        # if settings.PID_DIRECTORY:
        #     processes = self.get_expected_processes()
        #     for filename in glob.glob('%s/*.pid' % settings.PID_DIRECTORY):
        #         # list all PID files and read them
        #         data = self.read_pid_file(filename)
        #         self.analyse_pid_file(processes, data)
        #     for process, pids in processes.items():
        #         if not pids:
        #             settings_check_results.append(Warning('%s: no such process' % process, obj='system'))
        #         valid_pids = {pid for pid in pids if self.check_pid(pid)}
        #         invalid_pids = {pid for pid in pids if pid not in valid_pids}
        #         for pid in invalid_pids:
        #             msg = '%s: stale PID %s (in \'%s%s.pid\')' % (process, pid, settings.PID_DIRECTORY, pid)
        #             settings_check_results.append(Warning(msg, obj='system'))

    @staticmethod
    def analyse_pid_file(processes, data):
        command, pid = data.get("COMMAND"), data.get("PID")
        if command == "worker" and data.get("QUEUES"):
            for queue in data["QUEUES"].split("|"):
                command = "worker (queue '%s')" % queue
                if command and pid and re.match(r"^\d+$", pid):
                    processes.setdefault(command, []).append(pid)
        elif command and pid and re.match(r"^\d+$", pid):
            processes.setdefault(command, []).append(pid)

    @staticmethod
    def read_pid_file(filename):
        with open(filename) as fd:
            data = {}
            for line in fd:
                key, sep, value = line.strip().partition("=")
                if sep == "=" and key == key.upper():
                    data[key] = value
        return data

    @staticmethod
    def get_expected_processes():
        processes = {"server": []}
        if settings.USE_CELERY:
            processes.update(
                {"worker (queue '%s')" % x: [] for x in get_expected_queues()}
            )
        return processes


class CeleryStats(MonitoringCheck):
    template = "djangofloor/django/monitoring/celery_stats.html"

    def get_context(self, request):
        if not settings.USE_CELERY:
            return {"celery_required": False}
        celery_stats = app.control.inspect().stats()
        import_signals_and_functions()
        expected_queues = {x: ("danger", "remove") for x in get_expected_queues()}
        queue_stats = app.control.inspect().active_queues()
        if queue_stats is None:
            queue_stats = {}
        for stats in queue_stats.values():
            for queue_data in stats:
                # noinspection PyTypeChecker
                if queue_data["name"] in expected_queues:
                    # noinspection PyTypeChecker
                    expected_queues[queue_data["name"]] = ("success", "ok")
        missing_queues = {x for (x, y) in expected_queues.items() if y[0] == "danger"}
        if len(missing_queues) == 1:
            messages.error(
                request,
                _('There is no worker for the "%(name)s" Celery queue.')
                % {"name": missing_queues.pop()},
            )
        elif missing_queues:
            messages.error(
                request,
                _("There is no worker for the the following Celery queues: %(name)s.")
                % {"name": ", ".join(sorted(missing_queues))},
            )
        workers = []
        if celery_stats is None:
            celery_stats = {}
        for key in sorted(celery_stats.keys(), key=lambda y: y.lower()):
            worker = {"name": key}
            infos = celery_stats[key]
            url = "%s://%s" % (
                infos["broker"]["transport"],
                infos["broker"]["hostname"],
            )
            if infos["broker"].get("port"):
                url += ":%s" % infos["broker"]["port"]
            url += "/"
            if infos["broker"].get("virtual_host"):
                url += infos["broker"]["virtual_host"]
            worker["broker"] = url
            pids = [str(infos["pid"])] + [str(y) for y in infos["pool"]["processes"]]
            worker["pid"] = ", ".join(pids)
            worker["threads"] = infos["pool"]["max-concurrency"]
            worker["timeouts"] = sum(infos["pool"]["timeouts"])
            worker["state"] = ("success", "check")
            if worker["timeouts"] > 0:
                worker["state"] = ("danger", "remove")
            # noinspection PyTypeChecker
            worker["queues"] = list({y["name"] for y in queue_stats.get(key, [])})
            worker["queues"].sort()
            workers.append(worker)
        return {
            "workers": workers,
            "expected_queues": expected_queues,
            "celery_required": True,
        }


class RequestCheck(MonitoringCheck):
    template = "djangofloor/django/monitoring/request_check.html"
    common_headers = {
        "HTTP_ACCEPT": "Media type(s) that is(/are) acceptable for the response.",
        "HTTP_ACCEPT_CHARSET": "Character sets that are acceptable.",
        "HTTP_ACCEPT_ENCODING": "List of acceptable encodings. See HTTP compression.",
        "HTTP_ACCEPT_LANGUAGE": "List of acceptable human languages for response.",
        "HTTP_ACCEPT_DATETIME": "Acceptable version in time.",
        "HTTP_AUTHORIZATION": "Authentication credentials for HTTP authentication.",
        "HTTP_CACHE_CONTROL": "Used to specify directives that must be obeyed by caching mechanisms.",
        "HTTP_CONNECTION": "Control options for the current connection and list of hop-by-hop request fields.",
        "HTTP_COOKIE": "An HTTP cookie previously sent by the server with Set-Cookie (below).",
        "HTTP_CONTENT_LENGTH": "The length of the request body in octets (8-bit bytes).",
        "HTTP_CONTENT_MD5": "A Base64-encoded binary MD5 sum of the content of the request body.",
        "HTTP_CONTENT_TYPE": "The Media type of the body of the request (used with POST and PUT requests).",
        "HTTP_DATE": "The date and time that the message was originated",
        "HTTP_EXPECT": "Indicates that particular server behaviors are required by the client.",
        "HTTP_FORWARDED": "Disclose original information of a client connecting to a web server through an HTTP proxy.",
        "HTTP_FROM": "The email address of the user making the request.",
        "HTTP_HOST": "The domain name of the server (for virtual hosting), and the TCP port number.",
        "HTTP_IF_MATCH": "Only perform the action if the client supplied entity matches the same entity on the server.",
        "HTTP_IF_MODIFIED_SINCE": "Allows a 304 Not Modified to be returned if content is unchanged.",
        "HTTP_IF_NONE_MATCH": "Allows a 304 Not Modified to be returned if content is unchanged, see HTTP ETag.",
        "HTTP_IF_RANGE": "If the entity is unchanged, send me the part(s) that I am missing or send me the entity.",
        "HTTP_IF_UNMODIFIED_SINCE": "Only send the response if the entity has not been modified since a specific time.",
        "HTTP_MAX_FORWARDS": "Limit the number of times the message can be forwarded through proxies or gateways.",
        "HTTP_ORIGIN": "Initiates a request for cross-origin resource sharing.",
        "HTTP_PRAGMA": "Implementation-specific fields that may have various effects.",
        "HTTP_PROXY_AUTHORIZATION": "Authorization credentials for connecting to a proxy.",
        "HTTP_RANGE": "Request only part of an entity.",
        "HTTP_REFERER": "This is the address of the previous web page.",
        "HTTP_TE": "The transfer encodings the user agent is willing to accept.",
        "HTTP_USER_AGENT": "The user agent string of the user agent.",
        "HTTP_UPGRADE": "Ask the server to upgrade to another protocol.",
        "HTTP_VIA": "Informs the server of proxies through which the request was sent.",
        "HTTP_WARNING": "A general warning about possible problems with the entity body.",
        "HTTP_X_REQUESTED_WITH": "Mainly used to identify Ajax requests.",
        "HTTP_DNT": "Requests a web application to disable their tracking of a user.",
        "HTTP_X_FORWARDED_FOR": "A de facto standard for identifying the originating IP address.",
        "HTTP_X_FORWARDED_HOST": "A de facto standard for identifying the original host.",
        "HTTP_X_FORWARDED_PROTO": "A de facto standard for identifying the originating protocol",
        "HTTP_FRONT_END_HTTPS": "Non-standard header field used by Microsoft applications",
        "HTTP_PROXY_CONNECTION": "Implemented as a misunderstanding of the HTTP specifications.",
        "HTTP_X_CSRF_TOKEN": "Used to prevent cross-site request forgery.",
        "HTTP_X_REQUEST_ID": "Correlates HTTP requests between a client and server.",
        "HTTP_X_CORRELATION_ID": "Correlates HTTP requests between a client and server.",
    }

    def get_context(self, request):
        def django_fmt(y):
            return y.upper().replace("-", "_")

        def http_fmt(y):
            return y.upper().replace("_", "-")

        context = {
            "remote_user": None,
            "remote_address": request.META["REMOTE_ADDR"],
            "use_x_forwarded_for": None,
            "secure_proxy_ssl_header": None,
        }
        header = settings.DF_REMOTE_USER_HEADER
        if header:
            context["remote_user"] = (
                http_fmt(header),
                request.META.get(django_fmt(header)),
            )
        header = settings.USE_X_FORWARDED_FOR and "HTTP_X_FORWARDED_FOR"
        if header:
            context["use_x_forwarded_for"] = (
                http_fmt(header),
                request.META.get(django_fmt(header)),
            )
        context["secure_proxy_ssl_header"] = None
        if settings.SECURE_PROXY_SSL_HEADER:
            header, value = settings.SECURE_PROXY_SSL_HEADER
            context["secure_proxy_ssl_header"] = (
                http_fmt(header),
                request.META.get(django_fmt(header)),
                request.META.get(django_fmt(header)) == value,
            )
        host, sep, port = request.get_host().partition(":")
        context["allowed_hosts"] = settings.ALLOWED_HOSTS
        context["allowed_host"] = host in settings.ALLOWED_HOSTS
        context["request_host"] = host
        context["request_site"] = None
        context["cache_redis"] = settings.USE_REDIS_CACHE
        context["use_ssl"] = settings.USE_SSL
        context["session_redis"] = settings.USE_REDIS_SESSIONS
        context["websockets_required"] = settings.WEBSOCKET_URL is not None
        context["celery_required"] = settings.USE_CELERY
        # noinspection PyTypeChecker
        context["fake_username"] = getattr(
            settings, "DF_FAKE_AUTHENTICATION_USERNAME", None
        )
        # noinspection PyTypeChecker
        if hasattr(request, "site"):
            context["request_site"] = request.site
            context["request_site_valid"] = request.site == host
        context["server_name"] = settings.SERVER_NAME
        context["server_name_valid"] = settings.SERVER_NAME == host
        context["debug"] = settings.DEBUG
        context["request_headers"] = [
            (x, y, self.common_headers.get(x))
            for (x, y) in sorted(request.META.items())
        ]
        if settings.DEBUG:
            messages.warning(
                request,
                _(
                    "The DEBUG mode is activated. You should disable it for a production website."
                ),
            )
        if context["fake_username"]:
            messages.warning(
                request,
                _(
                    "DF_FAKE_AUTHENTICATION_USERNAME is set. "
                    "You should disable it for a production website."
                ),
            )
        context["settings_providers"] = [p for p in merger.providers]
        return context

    def check_commandline(self):
        if settings.DEBUG:
            settings_check_results.append(
                Warning(
                    "The DEBUG mode is activated. You should disable it in production",
                    obj="configuration",
                )
            )


class LogLastLines(MonitoringCheck):
    template = "djangofloor/django/monitoring/log_last_lines.html"

    def get_context(self, request):
        contents = []
        for filename in self.get_log_filenames():
            try:
                size = os.path.getsize(filename)
                with open(filename, "r", encoding="utf-8") as fd:
                    fd.seek(max(0, size - 4096))
                    content = fd.read(4096)
                contents.append((filename, "default", content))
            except Exception as e:
                contents.append(
                    (
                        filename,
                        "danger",
                        _("Unable to read %(filename)s") % {"filename": filename},
                    )
                )
                logger.exception(e)
        return {"contents": contents}

    @staticmethod
    def get_log_filenames():
        """Return the list of filenames used in all :class:`logging.FileHandler`.
        """
        handlers = [x for x in logging.root.handlers]
        for name, logger_obj in logging.root.manager.loggerDict.items():
            if not isinstance(logger_obj, logging.Logger):
                continue
            handlers += logger_obj.handlers
        handlers = [x for x in handlers if isinstance(x, logging.FileHandler)]
        filenames = {x.baseFilename for x in handlers}
        if settings.LOG_DIRECTORY:
            filenames |= {
                os.path.join(settings.LOG_DIRECTORY, x)
                for x in os.listdir(settings.LOG_DIRECTORY)
                if x.endswith(".log")
            }
        filenames = list(filenames)
        filenames.sort()
        return filenames


class LogAndExceptionCheck(MonitoringCheck):
    template = "djangofloor/django/monitoring/errors.html"

    def get_context(self, request):
        form = LogNameForm()
        return {"logname_form": form, "celery_required": settings.USE_CELERY}


class AuthenticationCheck(MonitoringCheck):
    """Presents all activated authentication methods
    """

    template = "djangofloor/django/monitoring/authentication.html"

    def get_context(self, request):
        context = {
            "ldap": bool(settings.AUTH_LDAP_SERVER_URI),
            "allow_user_creation": settings.DF_ALLOW_USER_CREATION,
            "session_age": datetime.timedelta(seconds=settings.SESSION_COOKIE_AGE),
            "basic_auth": settings.USE_HTTP_BASIC_AUTH,
            "remote_user": settings.DF_REMOTE_USER_HEADER,
            "remote_user_groups": settings.DF_DEFAULT_GROUPS,
            "allauth": settings.ALLAUTH_PROVIDER_APPS,
            "pam": settings.USE_PAM_AUTHENTICATION,
            "local_users": settings.DF_ALLOW_LOCAL_USERS,
        }

        return context


system_checks = [import_string(x)() for x in settings.DF_SYSTEM_CHECKS]


@never_cache
@login_required(login_url="df:login")
def system_state(request):
    if not request.user or not request.user.is_superuser:
        raise Http404
    components_values = [y.render(request) for y in system_checks]
    template_values = admin_context(
        {
            "components": components_values,
            "site_header": site.site_header,
            "site_title": site.site_title,
            "title": _("System state"),
            "has_permission": request.user.is_active and request.user.is_staff,
        }
    )
    set_websocket_topics(request)
    # noinspection PyUnresolvedReferences
    return TemplateResponse(
        request,
        template="djangofloor/django/system_state.html",
        context=template_values,
    )


@never_cache
@user_passes_test(lambda x: x.is_superuser)
def raise_exception(request):
    if not request.user.is_superuser:
        raise Http404
    messages.warning(
        request,
        _("An exception (division by zero) has been raised in a Django HTTP request"),
    )
    # noinspection PyStatementEffect
    1 / 0


@never_cache
@user_passes_test(lambda x: x.is_superuser)
def generate_log(request):
    if not request.user.is_superuser:
        raise Http404
    form = LogNameForm(request.POST)
    if form.is_valid():
        logname = (
            form.cleaned_data["other_log_name"]
            or form.cleaned_data["log_name"]
            or "django.request"
        )
        level = form.cleaned_data["level"]
        message = form.cleaned_data["message"]
        logger_ = logging.getLogger(logname)
        logger_.log(int(level), message)
        messages.success(
            request,
            _('message "%(message)s" logged to "%(logname)s" at level %(level)s.')
            % {"message": message, "level": level, "logname": logname},
        )
    else:
        messages.error(
            request, _("please specify a message, a logger name and a log level.")
        )
    return HttpResponseRedirect(redirect_to=reverse("df:system_state"))
