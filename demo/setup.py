# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Setup file for the DjangoFloor project.
"""

from demo import __version__ as version
from setuptools import setup, find_packages

entry_points = {'console_scripts': ['demo-manage = djangofloor.scripts:manage',
                                    'demo-gunicorn = djangofloor.scripts:gunicorn',
                                    'demo-celery = djangofloor.scripts:celery',
                                    'demo-uswgi = djangofloor.scripts:uswgi', ]}


setup(
    name='demo',
    version=version,
    description="No description yet.",
    long_description='no description yet',
    author='flanker',
    author_email='flanker@19pouces.net',
    license='CeCILL-b',
    url='',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='djangofloor.tests',
    install_requires=['djangofloor'],
    setup_requires=[],
    classifiers=[],
)