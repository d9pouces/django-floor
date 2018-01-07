"""Define checks integrated to the Django check framework
=====================================================

Django offers a system check framework, but that is called only after the Django setup.
However, settings based on callables (like :class:`djangofloor.conf.config_values.CallableSetting`)  can
also trigger some :class:`django.core.checks.Warning` during the setting loading.
Just append them to the `settings_check_results` list to delay them and display them just after the Django setup.

"""
import sys

import os
from distutils.spawn import find_executable

from django.core.checks import register, Error

from djangofloor.utils import is_package_present

__author__ = 'Matthieu Gallet'

settings_check_results = []


def missing_package(package_name, desc=''):
    if hasattr(sys, 'real_prefix'):  # inside a virtualenv
        cmd = 'Try \'pip install %s\' to install it.' % package_name
    elif __file__.startswith(os.environ.get('HOME', '/home')):
        cmd = 'Try \'pip3 install --user %s\' to install it.' % package_name
    else:
        cmd = 'Try \'sudo pip3 install %s\' to install it.' % package_name
    return Error('Python package \'%s\' is required%s. %s' % (package_name, desc, cmd), obj='configuration')


# noinspection PyUnusedLocal
@register()
def settings_check(app_configs, **kwargs):
    from djangofloor.views.monitoring import MonitoringCheck
    from django.utils.module_loading import import_string
    from djangofloor.conf.settings import merger
    for check_str in merger.settings['DF_SYSTEM_CHECKS']:
        check = import_string(check_str)()
        if isinstance(check, MonitoringCheck):
            check.check_commandline()
    return settings_check_results


def get_pipeline_requirements():
    from djangofloor.conf.settings import merger
    engines = [merger.settings.get('PIPELINE_CSS_COMPRESSOR', ''),
               merger.settings.get('PIPELINE_JS_COMPRESSOR', '')]
    engines += merger.settings.get('PIPELINE_COMPILERS', [])

    binaries = {'pipeline.compilers.coffee.CoffeeScriptCompiler': 'COFFEE_SCRIPT_BINARY',
                'pipeline.compilers.livescript.LiveScriptCompiler': 'LIVE_SCRIPT_BINARY',
                'pipeline.compilers.less.LessCompiler': 'LESS_BINARY',
                'pipeline.compilers.sass.SASSCompiler': 'SASS_BINARY',
                'pipeline.compilers.stylus.StylusCompiler': 'STYLUS_BINARY',
                'pipeline.compilers.es6.ES6Compiler': 'BABEL_BINARY',
                'pipeline.compressors.yuglify.YuglifyCompressor': 'YUGLIFY_BINARY',
                'pipeline.compressors.yui.YUICompressor': 'YUI_BINARY',
                'pipeline.compressors.closure.ClosureCompressor': 'CLOSURE_BINARY',
                'pipeline.compressors.uglifyjs.UglifyJSCompressor': 'UGLIFYJS_BINARY',
                'pipeline.compressors.csstidy.CSSTidyCompressor': 'CSSTIDY_BINARY',
                'pipeline.compressors.cssmin.CSSMinCompressor': 'CSSMIN_BINARY',
                }
    pip_packages = {'pipeline.compressors.jsmin.JSMinCompressor': ('jsmin', 'jsmin'),
                    'pipeline.compressors.slimit.SlimItCompressor': ('slimit', 'slimit'),
                    'djangofloor.templatetags.pipeline.RcssCompressor': ('rcssmin', 'rcssmin'),
                    'djangofloor.templatetags.pipeline.PyScssCompiler': ('scss', 'pyScss'),
                    }
    npm_packages = {'lsc', }
    gem_packages = {}
    result = {'gem': [], 'pip': [], 'npm': [], 'other': [], 'all': []}
    for engine in engines:
        if engine in binaries:
            name = merger.settings.get(binaries[engine], 'program')
            result['all'].append(name)
            if name in npm_packages:
                result['npm'].append(name)
            elif name in gem_packages:
                result['gem'].append(name)
            else:
                result['other'].append(name)
        elif engine in pip_packages:
            result['pip'].append(pip_packages[engine])
    for v in result.values():
        v.sort()
    return result


# noinspection PyUnusedLocal
@register()
def pipeline_check(app_configs, **kwargs):
    """Check if dependencies used by `django-pipeline` are installed.
    """
    check_results = []
    requirements = get_pipeline_requirements()
    for name in requirements['all']:
        if not find_executable(name):
            check_results.append(Error('\'%s\' is required by \'django-pipeline\' and is not found in PATH.' %
                                       name, obj='configuration'))
    for name, package in requirements['pip']:
        if not is_package_present(name):
            check_results.append(missing_package(package, ' by \'django-pipeline\''))
    return check_results
