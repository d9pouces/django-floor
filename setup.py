# -*- coding: utf-8 -*-
"""Setup file for the Djangofloor project.
"""

import codecs
import os
import re

import sys
from setuptools import setup, find_packages

# avoid a from djangofloor import __version__ as version (that compiles djangofloor.__init__
#   and is not compatible with bdist_deb)
version = None
for line in codecs.open(os.path.join('djangofloor', '__init__.py'), 'r', encoding='utf-8'):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)
python_version = (sys.version_info[0], sys.version_info[1])

# get README content from README.md file
with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as fd:
    long_description = fd.read()


extras_requirements = {}
install_requirements = ['django>=1.8', 'celery', 'django-bootstrap3', 'redis', 'pip']
if python_version < (3, 3):
    install_requirements.append('funcsigs')
if python_version >= (3, 4):
    install_requirements += ['aiohttp-wsgi', 'aiohttp', 'asyncio_redis']
elif python_version < (2, 8):
    install_requirements += ['gunicorn']

entry_points = {'console_scripts': ['djangofloor-createproject = djangofloor.scripts:create_project']}
extras_requirements['deb'] = ['stdeb>=0.8.5']
extras_requirements['extra'] = ['django-pipeline', 'django-debug-toolbar', 'django-redis-sessions',
                                'django-redis', 'psutil']
extras_requirements['doc'] = ['sphinx', 'sphinx_rtd_theme', 'sphinxcontrib-autoanysrc']

try:
    from djangofloor.scripts import set_env
    import django
    set_env('djangofloor-setup')
    django.setup()
except ImportError:
    set_env, django = None, None

setup(
    name='djangofloor',
    version=version,
    description='Add configuration management and websockets to Django.',
    long_description=long_description,
    author='Matthieu Gallet',
    author_email='github@19pouces.net',
    license='CeCILL-B',
    url='',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='djangofloor.tests',
    install_requires=install_requirements,
    extras_require=extras_requirements,
    setup_requires=[],
    classifiers=['Development Status :: 4 - Beta', 'Operating System :: MacOS :: MacOS X',
                 'Operating System :: POSIX :: BSD', 'Operating System :: POSIX :: Linux', 'Operating System :: Unix',
                 'License :: OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)',
                 'Programming Language :: Python :: 3.4', 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6'],
)
