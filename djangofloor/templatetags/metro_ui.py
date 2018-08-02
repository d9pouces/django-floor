import logging

from django import template
from django.template import Context
from django.template.loader import render_to_string

register = template.Library()
__author__ = "Matthieu Gallet"
logger = logging.getLogger("django.request")


@register.filter
def metro_ui_message_level(message):
    for (tag, bound) in (("alert", 40), ("warning", 30), ("success", 25)):
        if message.level >= bound:
            return tag
    return "info"


@register.simple_tag(takes_context=True)
def metro_ui_messages(context, style="banner"):
    """
    Show django.contrib.messages Messages in Metro alert containers.
    In order to make the alerts dismissable (with the close button),
    we have to set the jquery parameter too when using the
    bootstrap_javascript tag.
    Uses the template ``bootstrap3/messages.html``.
    **Tag name**::
        metroui_messages
    **Parameters**:
        None.
    **Usage**::
        {% bootstrap_messages %}
    **Example**::
        {% bootstrap_javascript jquery=1 %}
        {% bootstrap_messages %}
    """

    if context and isinstance(context, Context):
        context = context.flatten()
    context.update({"message_style": style})
    return render_to_string("djangofloor/metro-ui/messages.html", context=context)
