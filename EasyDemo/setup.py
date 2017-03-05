# -*- coding: utf-8 -*-
"""Setup file for EasyDemo"""
import codecs
import os.path
import re
import sys
from setuptools import setup, find_packages

# avoid a from 'easydemo' import __version__ as version (that compiles easydemo.__init__
#   and is not compatible with bdist_deb)
version = None
for line in codecs.open(os.path.join('easydemo', '__init__.py'), 'r', encoding='utf-8'):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)
python_version = (sys.version_info[0], sys.version_info[1])

# get README content from README.md file
with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as fd:
    long_description = fd.read()

entry_points = dict(console_scripts=['easydemo-celery = djangofloor.scripts:celery',
                                     'easydemo-django = djangofloor.scripts:django',
                                     'easydemo-aiohttp = djangofloor.scripts:aiohttp',
                                     'easydemo-gunicorn = djangofloor.scripts:gunicorn', ])

setup(
    name='EasyDemo',
    version=version,
    description='Simple demo for the DjangoFloor project.',
    long_description=long_description,
    license='CeCILL-B',
    url='',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['djangofloor'],
    classifiers=['Development Status :: 3 - Alpha', 'Operating System :: MacOS :: MacOS X',
                 'Operating System :: Microsoft :: Windows', 'Operating System :: POSIX :: BSD',
                 'Operating System :: POSIX :: Linux', 'Operating System :: Unix',
                 'License :: OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)',
                 'Programming Language :: Python :: 2.6', 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.4', 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6'],
)
