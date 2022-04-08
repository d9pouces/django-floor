"""Setup file for the Djangofloor project.
"""

import sys

from setuptools import setup

python_version = (sys.version_info[0], sys.version_info[1])

extras_requirements = {
    "extra": [
        "django-pipeline",
        "django-debug-toolbar",
        "django-redis-sessions",
        "django-redis",
        "psutil",
    ],
    "doc": ["sphinx", "sphinx_rtd_theme", "sphinxcontrib-autoanysrc"],
}

try:
    from djangofloor.scripts import set_env
    # noinspection PyPackageRequirements
    import django

    set_env("djangofloor-setup")
    django.setup()
except ImportError:
    set_env, django = None, None

install_requires = [
    "django-bootstrap3>=9.0.0",
    "redis",
    "pip",
    "asyncio_redis",
    "gunicorn",
    "vine<5.0.0a1,>=1.1.3",
]
if sys.version_info >= (3, 8, 0):
    install_requires += [
        "celery",
        "django",
        "aiohttp",
        "attrs",
        "chardet",
        "multidict",
        "async_timeout",
        "yarl",
        "aiohttp-wsgi",
    ]
elif sys.version_info >= (3, 6, 0):
    install_requires += [
        "celery<5",
        "django>=1.11.15,<3.2",
        "aiohttp>=3.1.3,<4.0",
        "attrs>=17.3.0",
        "chardet>=2.0,<4.0",
        "multidict>=4.0,<5.0",
        "async_timeout>=1.2.0,<4.0",
        "yarl>=1.0,<2.0",
        "aiohttp-wsgi>=0.8.0,<0.9.0",
    ]
elif sys.version_info >= (3, 5, 3):
    install_requires += [
        "celery<5",
        "django>=2.2.9,<3.0",
        "aiohttp>=3.1.3,<4.0",
        "attrs>=17.3.0",
        "chardet>=2.0,<4.0",
        "multidict>=4.0,<5.0",
        "async_timeout>=1.2.0,<4.0",
        "yarl>=1.0,<1.4",
        "aiohttp-wsgi>=0.8.0,<0.9.0",
    ]
else:
    install_requires += [
        "celery<5",
        "django>=2.2.9,<3.0",
        "aiohttp>=2.3.1,<3",
        "multidict>=4.0,<5.0",
        "async_timeout>=1.2.0,<3.0",
        "yarl>=1.0,<2.0",
        "aiohttp-wsgi>=0.7.0,<0.8.0",
    ]

setup(
    install_requires=install_requires,
    extras_require=extras_requirements,
)
