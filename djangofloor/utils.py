"""Utility functions
=================

Define some utility functions like warning or walking through modules.

"""

import argparse
import json
import os
import re
from argparse import ArgumentParser
from importlib import import_module

import pkg_resources
import zlib
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from pip.req import InstallRequirement

__author__ = 'Matthieu Gallet'


class RemovedInDjangoFloor110Warning(DeprecationWarning):
    """Used for displaying functions or modules that will be removed in a near future."""
    pass


class RemovedInDjangoFloor200Warning(DeprecationWarning):
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


def guess_version(defined_settings):
    """Guesss the project version.
    Expect an installed version (findable with pkg_resources) or __version__ in `your_project/__init__.py`.
    If not found

    :param defined_settings: all already defined settings (dict)
    :type defined_settings: :class:`dict`
    :return: should be something like `"1.2.3"`
    :rtype: :class:`str`
    """
    try:
        project_distribution = pkg_resources.get_distribution(defined_settings['DF_MODULE_NAME'])
        return project_distribution.version
    except pkg_resources.DistributionNotFound:
        pass
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


def smart_pipfile_url(url: str) -> str:
    """
    Given a `pip install URL`, return a valid PipFile line.

    >>> smart_pipfile_url('git://git.myproject.org/MyProject#egg=MyProject')
    "MyProject = { git = 'git://git.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('git+http://git.myproject.org/MyProject#egg=MyProject')
    "MyProject = { git = 'http://git.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('git+https://git.myproject.org/MyProject#egg=MyProject')
    "MyProject = { git = 'https://git.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('git+ssh://git.myproject.org/MyProject#egg=MyProject')
    "MyProject = { git = 'ssh://git.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('git+git://git.myproject.org/MyProject#egg=MyProject')
    "MyProject = { git = 'git://git.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('git+file://git.myproject.org/MyProject#egg=MyProject')
    "MyProject = { git = 'file://git.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('git+git@git.myproject.org:MyProject#egg=MyProject')
    "MyProject = { git = 'git://git@git.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('git://git.myproject.org/MyProject.git@master#egg=MyProject')
    "MyProject = { git = 'git://git.myproject.org/MyProject.git', ref = 'master', editable = true }"

    >>> smart_pipfile_url('git://git.myproject.org/MyProject.git@v1.0#egg=MyProject')
    "MyProject = { git = 'git://git.myproject.org/MyProject.git', ref = 'v1.0', editable = true }"

    >>> smart_pipfile_url('git://git.myproject.org/MyProject.git@da39a3ee5e6b4b0d3255bfef#egg=MyProject')
    "MyProject = { git = 'git://git.myproject.org/MyProject.git', ref = 'da39a3ee5e6b4b0d3255bfef', editable = true }"

    >>> smart_pipfile_url('hg+http://hg.myproject.org/MyProject#egg=MyProject')
    "MyProject = { hg = 'http://hg.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('hg+https://hg.myproject.org/MyProject#egg=MyProject')
    "MyProject = { hg = 'https://hg.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('hg+ssh://hg.myproject.org/MyProject#egg=MyProject')
    "MyProject = { hg = 'ssh://hg.myproject.org/MyProject', editable = true }"

    >>> smart_pipfile_url('hg+http://hg.myproject.org/MyProject@da39a3ee5e6b#egg=MyProject')
    "MyProject = { hg = 'http://hg.myproject.org/MyProject', ref = 'da39a3ee5e6b', editable = true }"

    >>> smart_pipfile_url('svn+svn://svn.myproject.org/svn/MyProject#egg=MyProject')
    "MyProject = { svn = 'svn://svn.myproject.org/svn/MyProject', editable = true }"

    >>> smart_pipfile_url('svn+http://svn.myproject.org/svn/MyProject/trunk@2019#egg=MyProject')
    "MyProject = { svn = 'http://svn.myproject.org/svn/MyProject/trunk', ref = '2019', editable = true }"

    >>> smart_pipfile_url('bzr+http://bzr.myproject.org/MyProject/trunk#egg=MyProject')
    "MyProject = { bzr = 'http://bzr.myproject.org/MyProject/trunk', editable = true }"

    >>> smart_pipfile_url('bzr+sftp://user@myproject.org/MyProject/trunk#egg=MyProject')
    "MyProject = { bzr = 'sftp://user@myproject.org/MyProject/trunk', editable = true }"

    >>> smart_pipfile_url('bzr+ssh://user@myproject.org/MyProject/trunk#egg=MyProject')
    "MyProject = { bzr = 'ssh://user@myproject.org/MyProject/trunk', editable = true }"

    >>> smart_pipfile_url('requests[socks]')
    "requests = { extras = ['socks'] }"

    >>> smart_pipfile_url('requests[socks,all]')
    "requests = { extras = ['socks', 'all'] }"

    >>> smart_pipfile_url('records>0.5.0')
    "records = '>0.5.0'"

    >>> smart_pipfile_url('git+https://github.com/django/django.git@1.11.4')
    "django = { git = 'https://github.com/django/django.git', ref = '1.11.4', editable = true }"

    >>> smart_pipfile_url('https://github.com/divio/django-cms/archive/release/3.4.x.zip')
    '"7377c666" = { file = \\'https://github.com/divio/django-cms/archive/release/3.4.x.zip\\' }'

    >>> smart_pipfile_url('pywinusb;python_version<"2.7"')
    "pywinusb = '*'"

    """
    def pip_repr(value: dict):
        return '{ %s }' % ', '.join(['%s = %r' % (k, v) for (k, v) in value.items()])

    class TRUE:
        def __repr__(self):
            return 'true'

    url_matcher = re.match(r'^(svn\+|git\+|hg\+|bzr\+)?(([^:]+)://[^/]+/[^@#]+)(@[^#]+)?(#.+)?$', url)
    git_matcher = re.match(r'^git\+([^@]+)@([^:]+):([^#]+)#egg=(.*)$', url)
    pkg_matcher = re.match(r'^([^\[;=<>~]+)(\[[^\]]+\])?((===|!=|<=|>=|<|>|==|~=)[^;]+)?(;.*)?$', url.replace(' ', ''))
    egg_name = None
    values = {}
    if url_matcher:
        versionning_protocol, url, scheme, tag, anchor = url_matcher.groups()
        if versionning_protocol is None:
            if scheme == 'git':
                versionning_protocol = scheme
            else:
                versionning_protocol = 'file'
        else:
            versionning_protocol = versionning_protocol[:-1]
        if url.endswith('.git'):
            egg_name = url.rpartition('/')[2].rpartition('.')[0]
        elif versionning_protocol == 'git':
            egg_name = url.rpartition('/')[2]
        if anchor and anchor.startswith('#egg='):
            egg_name = anchor[5:]
        values[versionning_protocol] = url
        if tag:
            values['ref'] = tag[1:]
        if versionning_protocol != 'file':
            values['editable'] = TRUE()
        if not egg_name:
            egg_name = ('"%X"' % zlib.crc32(url.encode())).lower()
    elif git_matcher:
        login, host, project, egg_name = git_matcher.groups()
        values['git'] = 'git://%s@%s/%s' % (login, host, project)
        values['editable'] = TRUE()
    elif pkg_matcher:
        egg_name, extra, spec, __, markers = pkg_matcher.groups()
        if extra:
            values['extras'] = extra[1:-1].split(',')
        if spec:
            values['version'] = spec
        elif not values:
            values['version'] = '*'
    if len(values) == 1 and 'version' in values:
        return '%s = %r' % (egg_name, values['version'])
    return '%s = %s' % (egg_name, pip_repr(values))
