"""Python shortcuts for JS Bootstrap3 signals
==========================================


This module only defines shortcuts to existing JS signals that are linked to Boostrap3.
"""
from djangofloor.tasks import WINDOW, scall
from djangofloor.wsgi.window_info import render_to_string

__author__ = "mgallet"

NOTIFICATION, BANNER, MODAL, SYSTEM = "notification", "banner", "modal", "system"
STYLES = [NOTIFICATION, BANNER, MODAL, SYSTEM]
INFO, DEFAULT, SUCCESS, DANGER, WARNING = (
    "info",
    "default",
    "success",
    "danger",
    "warning",
)
LEVELS = [DEFAULT, INFO, SUCCESS, DANGER, WARNING]


def notify(
    window_info,
    content,
    title=None,
    timeout=5000,
    style=NOTIFICATION,
    level=INFO,
    to=WINDOW,
):
    """Display a notification to the selected users.
    Can be a banner (on the top of the page), a Growl-like notification (bubble on the top-right), a modal or a system
    notification.

    :param window_info: a :class:`djangofloor.wsgi.window_info.WindowInfo` object
    :param content: content of the notification
    :param title: title of the notification
    :param timeout: number of milliseconds before hiding the message
    :param style: one of `djangofloor.signals.bootstrap3.{NOTIFICATION,BANNER,MODAL,SYSTEM}`
    :param level: one of `djangofloor.signals.bootstrap3.{INFO,DEFAULT,SUCCESS,DANGER,WARNING}`
    :param to: list of signal clients
    """
    return scall(
        window_info,
        "df.notify",
        to=to,
        content=content and str(content) or None,
        title=title and str(title) or None,
        timeout=timeout,
        style=style,
        level=level,
    )


def modal_show(window_info, html_content, width=None, to=WINDOW):
    return scall(window_info, "df.modal.show", to=to, width=width, html=html_content)


def render_to_modal(
    window_info, template_name, context, width=None, to=WINDOW, using=None
):
    """ render a template and display the result in a modal window on every selected clients

    :param window_info: a :class:`djangofloor.wsgi.window_info.WindowInfo` object
    :param template_name: name of the Django template
    :param context: template context (a dict)
    :param width: width of the modal, in pixels
    :param to: list of signal clients
    :param using: the `using` parameter of Django templates
    """
    html_content = render_to_string(template_name, context=context, using=using)
    return scall(window_info, "df.modal.show", to=to, width=width, html=html_content)


def modal_hide(window_info, to=WINDOW):
    return scall(window_info, "df.modal.hide", to=to)
