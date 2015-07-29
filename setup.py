# coding=utf-8
"""Setup file for the DjangoFloor project.
"""
from __future__ import unicode_literals
import re
import sys
import codecs
import os.path
from setuptools import setup, find_packages

# avoid a from djangofloor import __version__ as version (that compiles djangofloor.__init__ and is not compatible with bdist_deb)
version = None
for line in codecs.open(os.path.join('djangofloor', '__init__.py'), 'r', encoding='utf-8'):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)

# get README content from README.rst file
with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as fd:
    long_description = fd.read()
entry_points = {'console_scripts': ['djangofloor-manage = djangofloor.scripts:manage',
                                    'djangofloor-gunicorn = djangofloor.scripts:gunicorn',
                                    'djangofloor-celery = djangofloor.scripts:celery',
                                    'djangofloor-uwsgi = djangofloor.scripts:uwsgi', ],
                'distutils.commands': ['bdist_deb2 = djangofloor.management.commands.bdist_deb2:BdistDeb2']}

requirements = ['Django>=1.8.0',
                'django-allauth>=0.19.0',
                'gunicorn>=0.14.5',
                'django-bootstrap3>=5.0.0',
                'jsmin>=2.1.1',
                'django-debug-toolbar>=1.2.0',
                'django-admin-bootstrapped>=2.5.0',
                'django-pipeline>=1.5.2',
                'celery>=3.1.13',
                'django-redis>=3.8.3',
                'django-redis-cache>=0.13.1', ]
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
extras_require['deb'] = ['stdeb>=0.8.5', ]
extras_require['doc'] = ['Sphinx>=1.3.1', ]

setup(
    name='djangofloor',
    version=version,
    description="Base code for Django websites.",
    long_description=long_description,
    author='Matthieu Gallet',
    author_email='Matthieu Gallet@19pouces.net',
    license='CeCILL-b',
    url='https://github.com/d9pouces/django-floor',
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
                 'Operating System :: MacOS :: MacOS X',
                 'Operating System :: POSIX',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.2',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 ],
)
