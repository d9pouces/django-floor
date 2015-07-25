# -*- coding: utf-8 -*-
"""Generate Debian packages for all installed packages

python multideb.py

You should use a `stdeb.cfg` configuration file
"""
from __future__ import unicode_literals, print_function
import argparse
import glob
import os
import shutil
from tempfile import NamedTemporaryFile, mkdtemp

# noinspection PyPackageRequirements
import _warnings
import weakref
# noinspection PyPackageRequirements
from pip import get_installed_distributions
# noinspection PyPackageRequirements,PyProtectedMember
from pip._vendor.pkg_resources import Distribution
# noinspection PyPackageRequirements
from stdeb.downloader import get_source_tarball
# noinspection PyPackageRequirements
from stdeb.util import check_call
import sys

try:
    import configparser
except ImportError:
    # noinspection PyUnresolvedReferences,PyPep8Naming
    import ConfigParser as configparser

__author__ = 'Matthieu Gallet'


def normalize_package_name(name):
    return name.lower().replace('_', '-').strip()


class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everything contained
    in it are removed.
    """

    # Handle mkdtemp raising an exception
    name = None
    _closed = False

    # noinspection PyShadowingBuiltins
    def __init__(self, suffix="", prefix='tmp', dir=None):
        self.name = mkdtemp(suffix, prefix, dir)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    # noinspection PyUnusedLocal
    def __exit__(self, exc, value, tb):
        if self.name is not None and not self._closed:
            shutil.rmtree(self.name)
            self._closed = True


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--config', '-f', action='store', help='Configuration file', default='stdeb.cfg')
    args_parser.add_argument('--ignore-freeze', '-I', action='store_true', help='Add packages listed in `pip freeze`', default=False)
    args_parser.add_argument('--allow-unsafe-download', action='store_true', help='Allow unsafe downloads', default=False)
    args_parser.add_argument('--dest-dir', help='Destination dir', default='deb')

    args = args_parser.parse_args()
    config_parser = configparser.ConfigParser()
    config_parser.read([args.config])

    distribution_list = {}

    if not args.ignore_freeze:
        installed_distributions = get_installed_distributions(local_only=True)
        for distrib in installed_distributions:
            assert isinstance(distrib, Distribution)
            distribution_list[distrib.project_name] = distrib.version

    if config_parser.has_option('multideb', 'exclude'):
        excluded_packages = {x for x in config_parser.get('multideb', 'exclude').splitlines() if x.strip()}
    else:
        excluded_packages = set()

    if config_parser.has_section('multideb-packages'):
        for option_name in config_parser.options('multideb-packages'):
            option_value = config_parser.get('multideb-packages', option_name)
            package_name, sep, package_version = option_value.partition('==')
            distribution_list[package_name] = package_version

    deb_dest_dir = os.path.abspath(args.dest_dir)
    if not os.path.isdir(deb_dest_dir):
        os.makedirs(deb_dest_dir)
    if excluded_packages:
        print('List of packages excluded from deb. generation:')
        for package_name in excluded_packages:
            print(package_name)
    excluded_packages = {normalize_package_name(x) for x in excluded_packages}
    cwd = os.getcwd()
    with TemporaryDirectory() as temp_dir:
        # simplest way for storing .tar.gz files in a temp dir
        os.chdir(temp_dir)
        for package_name, package_version in distribution_list.items():
            if normalize_package_name(package_name) in excluded_packages:
                continue
            print('downloading %s %s' % (package_name, package_version))
            filename = get_source_tarball(package_name, verbose=False, release=package_version,
                                          allow_unsafe_download=args.allow_unsafe_download)
            with NamedTemporaryFile() as temp_config_file:
                # config file for each package
                if config_parser.has_section(package_name):
                    new_config_parser = configparser.ConfigParser()
                    new_config_parser.add_section('DEFAULT')
                    for option_name in config_parser.options(package_name):
                        option_value = config_parser.get(package_name, option_name)
                        new_config_parser.set('DEFAULT', option_name, option_value)
                    new_config_parser.write(temp_config_file)
                temp_config_file.flush()
                if os.path.isdir('deb_dist'):
                    shutil.rmtree('deb_dist')
                check_call(['py2dsc-deb', '-x', temp_config_file.name, filename])
            packages = glob.glob('deb_dist/*.deb')
            if not packages:
                raise ValueError('Unable to create %s-%s' % (package_name, package_version))
            os.rename(packages[0], os.path.join(deb_dest_dir, os.path.basename(packages[0])))
    os.chdir(cwd)

if __name__ == '__main__':
    main()
