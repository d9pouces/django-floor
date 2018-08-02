"""Templatetags for media files, websockets, notifications
=======================================================

Various templatetags provided by DjangoFloor.

"""
import logging
import warnings
from urllib.parse import urljoin

from django import template
from django.conf import settings
from django.core import signing
from django.template import Context
from django.templatetags.static import PrefixNode, StaticNode
from django.urls import reverse

# noinspection PyProtectedMember
from django.utils.html import _js_escapes, escape
from django.utils.safestring import mark_safe

from djangofloor.tasks import set_websocket_topics
from djangofloor.utils import RemovedInDjangoFloor200Warning

__author__ = "Matthieu Gallet"
register = template.Library()
logger = logging.getLogger("django.request")


@register.simple_tag(takes_context=True)
def df_init_websocket(context, *topics):
    """Set the websocket URL with the access token. Allow to access the right topics."""
    if not settings.WEBSOCKET_URL:
        return ""
    elif not context.get("df_has_ws_topics") and not topics:
        return ""
    elif not context.get("df_has_ws_topics") and context.get("df_http_request"):
        set_websocket_topics(context["df_http_request"], *topics)
    ws_token = context["df_window_key"]
    session_id = context["df_session_id"]
    signer = signing.Signer(session_id)
    signed_token = signer.sign(ws_token)
    protocol = "wss" if settings.USE_SSL else "ws"
    site_name = "%s:%s" % (settings.SERVER_NAME, settings.SERVER_PORT)
    script = '$.df._wsConnect("%s://%s%s?token=%s");' % (
        protocol,
        site_name,
        settings.WEBSOCKET_URL,
        signed_token,
    )
    script += '$.df._wsToken="%s";' % signed_token
    script = "$(document).ready(function(){%s});" % script
    init_value = '<script type="application/javascript">%s</script>' % script
    init_value += (
        '<script type="text/javascript" src="%s" charset="utf-8"></script>'
        % reverse("df:signals")
    )
    return mark_safe(init_value)


class _MediaNode(StaticNode):
    @classmethod
    def handle_simple(cls, path):
        return urljoin(PrefixNode.handle_simple("MEDIA_URL"), path)


@register.tag("media")
def do_media(parser, token):
    """
    Joins the given path with the MEDIA_URL setting.

    Usage::

        {% media path [as varname] %}

    Examples::

    .. code-block:: html

        {% media "myapp/css/base.css" %}
        {% media variable_with_path %}
        {% media "myapp/css/base.css" as admin_base_css %}
        {% media variable_with_path as varname %}

    """
    return _MediaNode.handle_token(parser, token)


def media(path):
    """If you want to reuse the template tag in your Python code."""
    return _MediaNode.handle_simple(path)


@register.simple_tag
def fontawesome_icon(
    name,
    large=False,
    fixed=False,
    spin=False,
    li=False,
    rotate=None,
    border=False,
    color=None,
):
    """Add font-awesome icons in your HTML code"""
    if isinstance(large, int) and 2 <= large <= 5:
        large = " fa-%dx" % large
    elif large:
        large = " fa-lg"
    else:
        large = ""
    return mark_safe(
        '<i class="fa fa-{name}{large}{fixed}{spin}{li}{rotate}{border}"{color}></i>'.format(
            name=name,
            large=large,
            fixed=" fa-fw" if fixed else "",
            spin=" fa-spin" if spin else "",
            li=" fa-li" if li else "",
            rotate=" fa-rotate-%s" % str(rotate) if rotate else "",
            border=" fa-border" if border else "",
            color='style="color:%s;"' % color if color else "",
        )
    )


@register.simple_tag
def django_icon(name, color=None):
    """Add font-awesome icons in your HTML code"""
    return mark_safe(
        '<i class="di di-{name}" {color}></i>'.format(
            name=name, color='style="color:%s;"' % color if color else ""
        )
    )


@register.simple_tag
def django_form(form):
    result = ""
    for field in form:
        result += '<div class="form-row">'
        if field.errors:
            result += field.errors.as_ul()
        if field.label_tag():
            result += field.label_tag()
        result += str(field)
        if field.help_text:
            result += '<div class="help">'
            result += escape(field.help_text)
            result += "</div>"
        result += "</div>"
    result += ""
    return mark_safe(result)


@register.filter(name="df_level")
def df_level(value, bounds="80:95"):
    """Convert a numeric value to "success", "warning" or "danger".
     The two required bounds are given by a string.
     """
    # noinspection PyTypeChecker
    warning, error = [float(x) for x in bounds.split(":")]
    if value < warning <= error or error <= warning < value:
        return "success"
    elif warning <= value < error or error < value <= warning:
        return "warning"
    return "danger"


@register.simple_tag(takes_context=True)
def df_messages(context, style="banner"):
    """Show django.contrib.messages Messages in Metro alert containers.
    In order to make the alerts dismissable (with the close button),
    we have to set the jquery parameter too when using the
    bootstrap_javascript tag.
    Uses the template ``bootstrap3/messages.html``.

    :param context: current template context
    :param style:  "notification", "banner", "modal" or "system"

    Example for your template:

    .. code-block:: html

        {% df_messages style='banner' %}
        {% df_messages style='notification' %}

    """

    if context and isinstance(context, Context):
        context = context.flatten()

    def message_level(msg):
        for (tag, bound) in (("danger", 40), ("warning", 30), ("success", 25)):
            if msg.level >= bound:
                return tag
        return "info"

    result = '<script type="text/javascript">\n'
    for message in context.get("messages", []):
        result += (
            '$.df.call("df.notify", {style: "%s", level: "%s", content: "%s"});\n'
            % (style, message_level(message), str(message).translate(_js_escapes))
        )
    get_notifications = context.get("df_get_notifications", lambda: [])
    values = get_notifications()
    for notification in values:
        result += (
            '$.df.call("df.notify", {style: "%s", level: "%s", content: "%s", timeout: %s, title: "%s"});\n'
            % (
                notification.display_mode,
                notification.level,
                notification.content.translate(_js_escapes),
                notification.auto_hide_seconds * 1000,
                notification.title,
            )
        )
    result += "</script>"
    return mark_safe(result)


@register.simple_tag(takes_context=False)
def df_deprecation(value):
    """.. deprecated:: 1.0 do not use it"""
    warnings.warn(value, RemovedInDjangoFloor200Warning)
    return ""


# TODO remove the following functions
@register.simple_tag(takes_context=True)
def df_window_key(context):
    """.. deprecated:: 1.0 do not use it"""
    warnings.warn(
        "df_window_key template tag has been replaced by df_init_websocket",
        RemovedInDjangoFloor200Warning,
    )
    return df_init_websocket(context)


@register.filter
def df_inivalue(value):
    """.. deprecated:: 1.0 do not use it"""
    warnings.warn(
        "df_inivalue template tag will be removed", RemovedInDjangoFloor200Warning
    )
    if not value:
        return ""
    return mark_safe("\n    ".join(value.splitlines()))
