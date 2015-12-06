# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
# noinspection PyUnresolvedReferences
from django.utils.six.moves.urllib.parse import urljoin
from django import template
from django.templatetags.static import StaticNode, PrefixNode
from django.utils.safestring import mark_safe

__author__ = 'Matthieu Gallet'

register = template.Library()


class MediaNode(StaticNode):

    @classmethod
    def handle_simple(cls, path):
        return urljoin(PrefixNode.handle_simple('MEDIA_URL'), path)


@register.tag('media')
def do_media(parser, token):
    """
    Joins the given path with the MEDIA_URL setting.

    Usage::

        {% media path [as varname] %}

    Examples::

        {% media "myapp/css/base.css" %}
        {% media variable_with_path %}
        {% media "myapp/css/base.css" as admin_base_css %}
        {% media variable_with_path as varname %}

    """
    return MediaNode.handle_token(parser, token)


def media(path):
    return MediaNode.handle_simple(path)


@register.simple_tag
def fontawesome_icon(name, large=False, fixed=False, spin=False, li=False, rotate=None, border=False, color=None):
    if isinstance(large, int) and 2 <= large <= 5:
        large = ' fa-%dx' % large
    elif large:
        large = ' fa-lg'
    else:
        large = ''
    return mark_safe('<i class="fa fa-{name}{large}{fixed}{spin}{li}{rotate}{border}"{color}></i>'.format(
        name=name,
        large=large,
        fixed=' fa-fw' if fixed else '',
        spin=' fa-spin' if spin else '',
        li=' fa-li' if li else '',
        rotate=' fa-rotate-%s' % str(rotate) if rotate else '',
        border=' fa-border' if border else '',
        color='style="color:%s;"' % color if color else ''
    ))


@register.simple_tag(takes_context=True)
def df_window_key(context):
    window_key = context.get('df_window_key', '[INVALID]')
    return mark_safe('<script type="application/javascript">$(function () {df.ws4redis_connect("%s");});</script>'
                     % window_key)
