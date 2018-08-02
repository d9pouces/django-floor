"""Setup file for the Djangofloor project.
"""

import os
import re

import sys
from setuptools import setup, find_packages

# avoid a from djangofloor import __version__ as version (that compiles djangofloor.__init__
#   and is not compatible with bdist_deb)
version = None
for line in open(os.path.join("djangofloor", "__init__.py"), "r", encoding="utf-8"):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)
python_version = (sys.version_info[0], sys.version_info[1])

# get README content from README.md file
with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as fd:
    long_description = fd.read()

extras_requirements = {}
entry_points = {
    "console_scripts": [
        "djangofloor-createproject = djangofloor.scripts:create_project"
    ]
}
extras_requirements["extra"] = [
    "django-pipeline",
    "django-debug-toolbar",
    "django-redis-sessions",
    "django-redis",
    "psutil",
]
extras_requirements["doc"] = ["sphinx", "sphinx_rtd_theme", "sphinxcontrib-autoanysrc"]

try:
    from djangofloor.scripts import set_env
    import django

    set_env("djangofloor-setup")
    django.setup()
except ImportError:
    set_env, django = None, None

install_requires = [
    "django>=1.11",
    "celery",
    "django-bootstrap3>=9.0.0",
    "redis",
    "pip",
    "asyncio_redis",
    "gunicorn",
]
if sys.version_info >= (3, 5, 3):
    install_requires += [
        "aiohttp>=3.1.3,<4.0",
        "attrs>=17.3.0",
        "chardet>=2.0,<4.0",
        "multidict>=4.0,<5.0",
        "async_timeout>=1.2.0",
        "yarl>=1.0,<2.0",
        "aiohttp-wsgi>=0.8.0,<0.9.0",
    ]
else:
    install_requires += [
        "aiohttp>=2.3.1,<3",
        "multidict>=4.0,<5.0",
        "async_timeout>=1.2.0,<3.0",
        "yarl>=1.0,<2.0",
        "aiohttp-wsgi>=0.7.0,<0.8.0",
    ]

setup(
    name="djangofloor",
    version=version,
    description="Add configuration management and websockets to Django.",
    long_description=long_description,
    author="Matthieu Gallet",
    author_email="github@19pouces.net",
    license="CeCILL-B",
    url="",
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite="djangofloor.tests",
    install_requires=install_requires,
    extras_require=extras_requirements,
    setup_requires=[],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Natural Language :: English",
        "Natural Language :: French",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
        "License :: OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
