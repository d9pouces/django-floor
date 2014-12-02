#coding=utf-8
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
    install_requires=['Django>=1.7', 'django-allauth', 'gunicorn', 'django-bootstrap3', 'django-pipeline',
                      'django-debug-toolbar', 'django-fontawesome', 'django-admin-bootstrapped',
                      'celery', 'slimit', 'jsmin'],
    setup_requires=[],
    classifiers=[],
)