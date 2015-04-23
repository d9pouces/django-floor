# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from django import template

__author__ = 'flanker'

register = template.Library()


@register.simple_tag
def fontawesome_icon(icon, large=False, fixed=False, spin=False, li=False, rotate=False):
    return '<i class="fa fa-{icon} {large} {fixed} {spin} {li} {rotate}"></i>'.format(
        icon=icon,
        large='fa-lg' if large is True else '',
        fixed='fa-fw' if fixed else '',
        spin='fa-spin' if spin else '',
        li='fa-li' if li else '',
        rotate='fa-rotate-%s' % str(rotate) if rotate else ''
    )


if __name__ == '__main__':
    import doctest

    doctest.testmod()