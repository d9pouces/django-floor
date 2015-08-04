# -*- coding: utf-8 -*-
"""patches for creating Debian Packages with `multideb` and `stdeb`
"""
from __future__ import unicode_literals
import codecs
import os
import shutil
import sys

__author__ = 'Matthieu Gallet'


# noinspection PyUnusedLocal
def fix_celery(package_name, package_version, deb_src_dir):
    shutil.rmtree('docs')


# noinspection PyUnusedLocal
def fix_pathlib(package_name, package_version, deb_src_dir):
    with codecs.open('MANIFEST.in', 'w', encoding='utf-8') as fd:
        fd.write("include setup.py pathlib.py test_pathlib.py *.txt *.rst\n")
        fd.write("recursive-include docs *.rst *.py make.bat Makefile\n")


# noinspection PyUnusedLocal
def fix_msgpack(package_name, package_version, deb_src_dir):
    with codecs.open('MANIFEST.in', 'w', encoding='utf-8') as fd:
        fd.write("include setup.py COPYING msgpack *.txt *.rst\n")
        fd.write("recursive-include docs *.rst *.py make.bat Makefile\n")


# noinspection PyUnusedLocal
def fix_django_redis(package_name, package_version, deb_src_dir):
    file_replace(os.path.join(deb_src_dir, 'debian', 'control'), '${misc:Depends}, ${python3:Depends}',
                 "python3 (>= 3.2), python3-msgpack, python3-redis (>= 1.8.0)")
    file_replace(os.path.join(deb_src_dir, 'debian', 'control'), '${misc:Depends}, ${python:Depends}',
                 "python (>= 2.7), python (<< 2.8), python-redis (>= 1.8.0), python-msgpack")


def file_replace(filename, pattern_to_replace, replacement):
    with codecs.open(filename, 'r', encoding='utf-8') as fd:
        content = fd.read()
    content = content.replace(pattern_to_replace, replacement)
    with codecs.open(filename, 'w', encoding='utf-8') as fd:
        fd.write(content)
