# coding=utf-8
from __future__ import unicode_literals, absolute_import
# noinspection PyCompatibility
from pathlib import PosixPath
from django.utils import six
import sys

__author__ = 'Matthieu Gallet'


class DirectoryPath(PosixPath):
    def __repr__(self):
        return repr(str(self))


class FilePath(PosixPath):
    def __repr__(self):
        return repr(str(self))


def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
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
