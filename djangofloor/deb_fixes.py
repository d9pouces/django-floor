"""patches for creating Debian Packages with `multideb` and `stdeb`
"""
import os
import shutil
import sys

__author__ = 'Matthieu Gallet'


# noinspection PyUnusedLocal
def fix_celery(package_name, package_version, deb_src_dir=None):
    shutil.rmtree('docs')


# noinspection PyUnusedLocal
def fix_pathlib(package_name, package_version, deb_src_dir=None):
    with open('MANIFEST.in', 'w', encoding='utf-8') as fd:
        fd.write("include setup.py pathlib.py test_pathlib.py *.txt *.rst\n")
        fd.write("recursive-include docs *.rst *.py make.bat Makefile\n")


# noinspection PyUnusedLocal
def fix_msgpack(package_name, package_version, deb_src_dir=None):
    with open('MANIFEST.in', 'w', encoding='utf-8') as fd:
        fd.write("include setup.py COPYING msgpack *.txt *.rst\n")
        fd.write("recursive-include docs *.rst *.py make.bat Makefile\n")


# noinspection PyUnusedLocal
def fix_django_redis(package_name, package_version, deb_src_dir):
    file_replace(os.path.join(deb_src_dir, 'debian', 'control'), '${misc:Depends}, ${python3:Depends}',
                 "python3 (>= 3.2), python3-msgpack, python3-redis (>= 1.8.0)")
    file_replace(os.path.join(deb_src_dir, 'debian', 'control'), '${misc:Depends}, ${python:Depends}',
                 "python (>= 2.7), python (<< 2.8), python-redis (>= 1.8.0), python-msgpack")


# noinspection PyUnusedLocal
def fix_django(package_name, package_version, deb_src_dir=None):
    if sys.version_info[0] == 3:
        os.rename(os.path.join('django', 'bin', 'django-admin.py'), os.path.join('django', 'bin', 'django-admin3.py'))
        file_replace('setup.py', 'django-admin', 'django-admin3')
    for root, dirnames, filenames in os.walk(os.path.join('django', 'conf', 'app_template')):
        for filename in filenames:
            # noinspection PyTypeChecker
            open(os.path.join(root, filename), 'wb').close()


def file_replace(filename, pattern_to_replace, replacement):
    with open(filename, 'r', encoding='utf-8') as fd:
        content = fd.read()
    content = content.replace(pattern_to_replace, replacement)
    with open(filename, 'w', encoding='utf-8') as fd:
        fd.write(content)
