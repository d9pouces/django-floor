# -*- coding: utf-8 -*-
"""Utility functions
=================

Define some utility functions like warning or walking through modules.

"""
from __future__ import unicode_literals, print_function

import argparse
import os
import sys
import warnings
from argparse import ArgumentParser

import pkg_resources
from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.utils.module_loading import import_string

from djangofloor.conf.config_values import AutocreateDirectory, AutocreateFile, \
    SettingReference as OriginalSettingReference, CallableSetting as OriginalCallableSetting, \
    ExpandIterable as OriginalExpandIterable
from djangofloor.conf.merger import SettingMerger as OriginalSettingMerger
from djangofloor.conf.providers import PythonModuleProvider, PythonFileProvider, IniConfigProvider

__author__ = 'Matthieu Gallet'


class RemovedInDjangoFloor110Warning(DeprecationWarning):
    """Used for displaying functions or modules that will be removed in a near future."""
    pass


def is_package_present(package_name):
    """Return True is the `package_name` package is presend in your current Python environment."""
    try:
        import_module(package_name)
        return True
    except ImportError:
        return False


def ensure_dir(path, parent=True):
    """Ensure that the given directory exists

    :param path: the path to check
    :param parent: only ensure the existence of the parent directory

    """
    dirname = os.path.dirname(path) if parent else path
    if not os.path.isdir(dirname):
        os.makedirs(dirname)


def walk(module_name, dirname, topdown=True):
    """
    Copy of :func:`os.walk`, please refer to its doc. The only difference is that we walk in a package_resource
    instead of a plain directory.
    :type module_name: basestring
    :param module_name: module to search in
    :type dirname: basestring
    :param dirname: base directory
    :type topdown: bool
    :param topdown: if True, perform a topdown search.
    """

    def rec_walk(root):
        """
        Recursively list subdirectories and filenames from the root.
        :param root: the root path
        :type root: basestring
        """
        dirnames = []
        filenames = []
        for name in pkg_resources.resource_listdir(module_name, root):
            # noinspection PyUnresolvedReferences
            fullname = root + '/' + name
            isdir = pkg_resources.resource_isdir(module_name, fullname)
            if isdir:
                dirnames.append(name)
                if not topdown:
                    rec_walk(fullname)
            else:
                filenames.append(name)
        yield root, dirnames, filenames
        if topdown:
            for name in dirnames:
                # noinspection PyUnresolvedReferences
                for values in rec_walk(root + '/' + name):
                    yield values

    return rec_walk(dirname)


def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    # noinspection PyTypeChecker
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in range(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level package")
    return "%s.%s" % (package[:dot], name)


if six.PY3:
    # noinspection PyUnresolvedReferences
    from importlib import import_module
else:
    def import_module(name, package=None):
        """Import a module.

        The 'package' argument is required when performing a relative import. It
        specifies the package to use as the anchor point from which to resolve the
        relative import to an absolute import.

        """
        if name.startswith('.'):
            if not package:
                raise TypeError("relative imports require the 'package' argument")
            level = 0
            for character in name:
                if character != '.':
                    break
                level += 1
            name = _resolve_name(name[level:], package, level)
        __import__(name)
        return sys.modules[name]


def guess_version(defined_settings):
    """Guesss the project version. Expect __version__ in `your_project/__init__.py`

    :param defined_settings: all already defined settings (dict)
    :type defined_settings: :class:`dict`
    :return: should be something like `"1.2.3"`
    :rtype: :class:`str`
    """
    try:
        return import_string('%s.__version__' % defined_settings['DF_MODULE_NAME'])
    except ImportError:
        return '1.0.0'


def get_view_from_string(view_as_str):
    try:
        view = import_string(view_as_str)
    except ImportError:
        raise ImproperlyConfigured('Unable to import %s' % view_as_str)
    if hasattr(view, 'as_view') and callable(view.as_view):
        return view.as_view()
    elif callable(view):
        return view
    raise ImproperlyConfigured('%s is not callabled and does not have an "as_view" attribute')


def remove_arguments_from_help(parser, arguments):
    assert isinstance(parser, ArgumentParser)
    assert isinstance(arguments, set)
    # noinspection PyProtectedMember
    for action in parser._actions:
        if arguments & set(action.option_strings):
            action.help = argparse.SUPPRESS


# ##############################################################################
#
#   Deprecated functions
#
# ##############################################################################


class DirectoryPath(AutocreateDirectory):
    """.. deprecated:: 1.0 use :class:`djangofloor.conf.config_values.DirectoryPath`"""
    def __init__(self, value):
        warnings.warn('DirectoryPath is moved to djangofloor.conf.config_values.DirectoryPath',
                      RemovedInDjangoFloor110Warning)
        super(DirectoryPath, self).__init__(value)


class FilePath(AutocreateFile):
    """.. deprecated:: 1.0 use :class:`djangofloor.conf.config_values.AutocreateFile`"""
    def __init__(self, value):
        warnings.warn('DirectoryPath is moved to djangofloor.conf.config_values.AutocreateFile',
                      RemovedInDjangoFloor110Warning)
        super(FilePath, self).__init__(value)


class SettingReference(OriginalSettingReference):
    """.. deprecated:: 1.0 use :class:`djangofloor.conf.config_values.SettingReference`"""
    def __init__(self, value, func=None):
        warnings.warn('SettingReference is moved to djangofloor.conf.config_values.SettingReference',
                      RemovedInDjangoFloor110Warning)
        super(SettingReference, self).__init__(value, func=func)


class CallableSetting(OriginalCallableSetting):
    """.. deprecated:: 1.0 use :class:`djangofloor.conf.config_values.CallableSetting`"""
    def __init__(self, value, *required):
        warnings.warn('CallableSetting is moved to djangofloor.conf.config_values.CallableSetting',
                      RemovedInDjangoFloor110Warning)
        super(CallableSetting, self).__init__(value, *required)


class ExpandIterable(OriginalExpandIterable):
    """.. deprecated:: 1.0 use :class:`djangofloor.conf.config_values.ExpandIterable`"""
    def __init__(self, value):
        warnings.warn('ExpandIterable is moved to djangofloor.conf.config_values.ExpandIterable',
                      RemovedInDjangoFloor110Warning)
        super(ExpandIterable, self).__init__(value)


class SettingMerger(OriginalSettingMerger):
    """.. deprecated:: 1.0 use :class:`djangofloor.conf.merger.SettingMerger`
    """

    def __init__(self, project_name, default_settings_module_name, project_settings_module_name,
                 user_settings_path, djangofloor_config_path, djangofloor_mapping, doc_mode=False,
                 read_only=False):
        # noinspection PyUnusedLocal
        doc_mode = doc_mode
        warnings.warn('SettingMerger is moved to djangofloor.conf.merger.SettingMerger',
                      RemovedInDjangoFloor110Warning)
        from djangofloor.conf.providers import PythonConfigFieldsProvider
        extra_values = {'DF_MODULE_NAME': project_name}
        providers = []
        if default_settings_module_name:
            providers.append(PythonModuleProvider(default_settings_module_name))
        if project_settings_module_name:
            providers.append(PythonModuleProvider(project_settings_module_name))
        if user_settings_path:
            providers.append(PythonFileProvider(user_settings_path))
        if djangofloor_config_path:
            providers.append(IniConfigProvider(djangofloor_config_path))
        super(SettingMerger, self).__init__(PythonConfigFieldsProvider(djangofloor_mapping), providers,
                                            extra_values=extra_values,
                                            read_only=read_only)

    @staticmethod
    def import_file(filepath):
        """import the Python source file as a Python module.

        :param filepath: absolute path of the Python module
        :type filepath: :class:`str`
        :return: the imported module
        """
        warnings.warn('SettingMerger.import_file method will be removed', RemovedInDjangoFloor110Warning)
        if filepath and os.path.isfile(filepath):
            dirname = os.path.dirname(filepath)
            if dirname not in sys.path:
                sys.path.insert(0, dirname)
            conf_module = os.path.splitext(os.path.basename(filepath))[0]
            module_ = import_module(conf_module)
        elif filepath:
            import djangofloor.empty
            module_ = djangofloor.empty
        else:
            import djangofloor.empty
            module_ = djangofloor.empty
        return module_

    @staticmethod
    def ensure_dir(path_, parent_=True):
        """Ensure that the given directory exists

        :param path_: the path to check
        :param parent_: only ensure the existence of the parent directory

        """
        warnings.warn('SettingMerger.ensure_dir method will be removed', RemovedInDjangoFloor110Warning)
        dirname_ = os.path.dirname(path_) if parent_ else path_
        if not os.path.isdir(dirname_):
            try:
                os.makedirs(dirname_)
                print('Directory %s created.' % dirname_)
            except IOError:
                print('Unable to create directory %s.' % dirname_)
