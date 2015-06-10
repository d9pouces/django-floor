# coding=utf-8
from __future__ import unicode_literals
import sys

"""Setup file for the DjangoFloor project.
"""

import codecs
import os.path
from setuptools import setup, find_packages
from djangofloor import __version__ as version

# get README content from README.rst file
with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as fd:
    long_description = fd.read()
entry_points = {'console_scripts': ['djangofloor-manage = djangofloor.scripts:manage',
                                    'djangofloor-gunicorn = djangofloor.scripts:gunicorn',
                                    'djangofloor-celery = djangofloor.scripts:celery',
                                    'djangofloor-uswgi = djangofloor.scripts:uswgi', ]}

requirements = ['Django>=1.8', 'django-allauth', 'gunicorn', 'django-bootstrap3', 'jsmin',
                'django-debug-toolbar', 'django-admin-bootstrapped',
                'django-pipeline', 'celery', 'django-redis', 'django-redis-cache', ]
PY2 = sys.version_info[0] == 2

extras_require = {}
try:
    import pathlib
except ImportError:
    pathlib = None
    requirements.append('pathlib')
try:
    from inspect import signature
except ImportError:
    signature = None
    requirements.append('funcsigs')
if PY2:
    extras_require['websocket'] = ['django-websocket-redis', 'gevent', 'uwsgi']
extras_require['scss'] = ['pyScss', ]

setup(
    name='djangofloor',
    version=version,
    description="infrastructure for Django websites.",
    long_description=long_description,
    author='flanker',
    author_email='flanker@19pouces.net',
    license='CeCILL-b',
    url='',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='djangofloor.tests',
    install_requires=requirements,
    extras_require=extras_require,
    setup_requires=[],
    classifiers=['Environment :: Web Environment',
                 'Framework :: Django :: 1.8',
                 'License :: OSI Approved',
                 'Operating System :: MacOS :: MacOS X', 'Operating System :: POSIX',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.2',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 ],
)
