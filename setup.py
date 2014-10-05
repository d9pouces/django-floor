#coding=utf-8
"""Setup file for the DjangoFloor project.
"""

import codecs
import os.path

import ez_setup

ez_setup.use_setuptools()
from setuptools import setup, find_packages

# get README content from README.rst file
with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as fd:
    long_description = fd.read()

# get version value from VERSION file
with codecs.open(os.path.join(os.path.dirname(__file__), 'VERSION'), encoding='utf-8') as fd:
    version = fd.read().strip()
entry_points = {'console_scripts': ['djangofloor-manage = djangofloor.scripts:manage',
                                    'djangofloor-gunicorn = djangofloor.scripts:gunicorn',
                                    'djangofloor-celery = djangofloor.scripts:celery',
                                    ]}

setup(
    name='djangofloor',
    version=version,
    description="No description yet.",
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
    install_requires=['django>=1.7', 'django-allauth', 'gunicorn', 'django-bootstrap3', 'django-pipeline',
                      'django-debug-toolbar', 'django-fontawesome', 'django-admin-bootstrapped',
                      'celery', 'slimit', 'jsmin'],
    setup_requires=['django>=1.7', 'django-allauth', 'gunicorn', 'django-bootstrap3', 'django-pipeline',
                    'django-debug-toolbar', 'django-fontawesome', 'django-admin-bootstrapped', ],
    classifiers=[],
)