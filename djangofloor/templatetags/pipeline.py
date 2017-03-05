# -*- coding: utf-8 -*-
"""Emulate django-pipeline templatetags
====================================

Allows you to use the same `javascript` and `stylesheet` template tags as with `django-pipeline`.
If you add `django-pipeline` to your `settings.INSTALLED_APPS`, these versions are ignored, using the original ones.

"""
from __future__ import unicode_literals, print_function, absolute_import

import warnings

from django import template
from django.conf import settings
from django.template.library import SimpleNode
from django.utils.safestring import mark_safe
from djangofloor.utils import RemovedInDjangoFloor110Warning
if settings.USE_PIPELINE:
    try:
        # noinspection PyPackageRequirements
        import pipeline.templatetags.pipeline as pipe
    except ImportError:
        pipe = None
else:
    pipe = None

__author__ = 'Matthieu Gallet'

register = template.Library()
_deprecated_files = {'bootstrap3/css/bootstrap.css', 'bootstrap3/css/bootstrap.css.map',
                     'bootstrap3/css/bootstrap.min.css', 'bootstrap3/css/bootstrap.min.css.map',
                     'bootstrap3/css/bootswatch.less', 'bootstrap3/css/variables.less',
                     'bootstrap3/fonts/glyphicons-halflings-regular.eot',
                     'bootstrap3/fonts/glyphicons-halflings-regular.svg',
                     'bootstrap3/fonts/glyphicons-halflings-regular.ttf',
                     'bootstrap3/fonts/glyphicons-halflings-regular.woff',
                     'bootstrap3/fonts/glyphicons-halflings-regular.woff2', 'bootstrap3/js/bootstrap.js',
                     'bootstrap3/js/bootstrap.min.js', 'css/bootstrap-select.css', 'css/bootstrap-select.min.css',
                     'css/djangofloor.css', 'css/font-awesome.css', 'css/font-awesome.min.css', 'fonts/FontAwesome.otf',
                     'fonts/fontawesome-webfont.eot', 'fonts/fontawesome-webfont.svg', 'fonts/fontawesome-webfont.ttf',
                     'fonts/fontawesome-webfont.woff', 'fonts/glyphicons-halflings-regular.eot',
                     'fonts/glyphicons-halflings-regular.svg', 'fonts/glyphicons-halflings-regular.ttf',
                     'fonts/glyphicons-halflings-regular.woff', 'fonts/glyphicons-halflings-regular.woff2',
                     'images/favicon.ico', 'images/favicon.png', 'js/bootstrap-notify.js', 'js/bootstrap-notify.min.js',
                     'js/bootstrap-select.js', 'js/bootstrap-select.min.js', 'js/djangofloor.js',
                     'js/html5shiv.js', 'js/jquery-1.10.2.js', 'js/jquery-1.10.2.min.map', 'js/jquery.min.js',
                     'js/respond.min.js', }
_warned_files = set()


@register.simple_tag
def javascript(key):
    """insert all javascript files corresponding to the given key"""
    if pipe and settings.PIPELINE['PIPELINE_ENABLED']:
        node = pipe.JavascriptNode(key)
        return node.render({key: key})
    filenames = settings.PIPELINE['JAVASCRIPT'][key]['source_filenames']
    context = {'type': 'text/javascript', 'charset': 'utf-8'}
    context.update(settings.PIPELINE['JAVASCRIPT'][key].get('extra_context', {}))
    extra = ' '.join('%s="%s"' % x for x in context.items())

    def fmt(filename):
        if filename in _deprecated_files and filename not in _warned_files:
            warnings.warn('%s is deprecated' % filename, RemovedInDjangoFloor110Warning, stacklevel=2)
            _warned_files.add(filename)
        return '<script src="%s%s" %s></script>' % (settings.STATIC_URL, filename, extra)

    node = '\n'.join([fmt(x) for x in filenames])
    return mark_safe(node)


@register.simple_tag
def stylesheet(key):
    """insert all javascript files corresponding to the given key"""
    if pipe and settings.PIPELINE['PIPELINE_ENABLED']:
        node = pipe.StylesheetNode(key)
        return node.render({key: key})
    filenames = settings.PIPELINE['STYLESHEETS'][key]['source_filenames']
    context = {'type': 'text/css', 'rel': 'stylesheet'}
    context.update(settings.PIPELINE['STYLESHEETS'][key].get('extra_context', {}))
    extra = ' '.join('%s="%s"' % x for x in context.items())

    def fmt(filename):
        return '<link href="%s%s" %s/>' % (settings.STATIC_URL, filename, extra)

    result = '\n'.join([fmt(x) for x in filenames])
    return mark_safe(result)
