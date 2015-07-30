# -*- coding: utf-8 -*-
"""patches for creating Debian Packages with `multideb` and `stdeb`
"""
from __future__ import unicode_literals
import codecs
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
def fix_pipeline(package_name, package_version, deb_src_dir):
    if sys.version_info[0] == 2:
        return
    with codecs.open('setup.py', 'r', encoding='utf-8') as fd:
        content = fd.read()
    content = content.replace("'futures>=2.1.3',", "")
    with codecs.open('setup.py', 'w', encoding='utf-8') as fd:
        fd.write(content)

