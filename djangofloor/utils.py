"""Utility functions
=================

Define some utility functions like warning or walking through modules.

"""

import argparse
import os
import sys
from argparse import ArgumentParser

import pkg_resources
from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.utils.module_loading import import_string

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
    return path


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
