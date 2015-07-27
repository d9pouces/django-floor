# -*- coding: utf-8 -*-
"""patches for creating Debian Packages with `multideb` and `stdeb`
"""
import shutil

__author__ = 'Matthieu Gallet'


# noinspection PyUnusedLocal
def fix_celery(package_name, package_version, deb_src_dir):
    shutil.rmtree('docs')
