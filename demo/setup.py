# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
import os
import re

"""Setup file for the DjangoFloor project.
"""

from setuptools import setup, find_packages
version = None
for line in codecs.open(os.path.join('demo', '__init__.py'), 'r', encoding='utf-8'):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)

entry_points = {'console_scripts': ['demo-manage = djangofloor.scripts:manage',
                                    'demo-gunicorn = djangofloor.scripts:gunicorn',
                                    'demo-celery = djangofloor.scripts:celery',
                                    'demo-uswgi = djangofloor.scripts:uswgi', ]}


setup(
    name='demo',
    version=version,
    description="No description yet.",
    long_description='no description yet',
    author='Matthieu Gallet',
    author_email='Gallet.Matthieu@19pouces.net',
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
