# coding=utf-8
"""Setup file for the DjangoFloor project.
"""
from __future__ import unicode_literals
import re
import sys
import codecs
import os.path
from setuptools import setup, find_packages

# avoid 'from djangofloor import __version__ as version' (compiles djangofloor.__init__, not compatible with bdist_deb)
version = None
for line in codecs.open(os.path.join('djangofloor', '__init__.py'), 'r', encoding='utf-8'):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)

# get README content from README.rst file
with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as fd:
    long_description = fd.read()
suffix = '' if sys.version_info[0] == 2 else '%s' % sys.version_info[0]
entry_points = {'console_scripts': [],
                'distutils.commands': ['bdist_deb_django = '
                                       'djangofloor.management.commands.bdist_deb_django:BdistDebDjango']}

requirements = ['Django>=1.9.0', 'Django<1.10.0',
                'django-allauth>=0.24.0',
                'gunicorn>=0.14.5',
                'django-bootstrap3>=6.2.0',
                'django-debug-toolbar>=1.4',
                'django-pipeline>=1.6.0', 'django-pipeline<1.7.0',
                'celery>=3.1.13',
                'django-redis>=3.8.3',
                'django-redis-cache>=0.13.1', ]

extras_require = {}
version_infos = (sys.version_info[0], sys.version_info[1])
if version_infos < (3, 3):
    requirements.append('funcsigs')
if version_infos < (3, 0):
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
    author_email='Gallet.Matthieu@19pouces.net',
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
