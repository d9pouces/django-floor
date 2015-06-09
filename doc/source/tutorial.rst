Tutorial
========

This tutorial shows you how to create a new DjangoFloor-based website.

Basically, there are two ways for creating a new project: from scratch, or with `StarterPyth <https://github.com/d9pouces/StarterPyth>`.

Creating a new project from scratch
-----------------------------------

Let assume that our great idea will be GreatProject.

As always, we start by creating a new virtualenv::

    mkvirtualenv greatproject -p `which python2.7`
    pip install djangofloor

We can create required files and directories::

    mkdir -p GreatProject/greatproject/tests GreatProject/greatproject/static GreatProject/greatproject/templates
    cd GreatProject
    touch greatproject/models.py
    echo "__version__ = '1.0.0'" > greatproject/__init__.py

    cat << EOF > greatproject-manage.py
    from djangofloor.scripts import manage
    manage()
    EOF
    cat << EOF > greatproject-gunicorn.py
    from djangofloor.scripts import gunicorn
    gunicorn()
    EOF
    cat << EOF > greatproject-celery.py
    from djangofloor.scripts import celery
    celery()
    EOF
    cat << EOF > greatproject-uwsgi.py
    from djangofloor.scripts import uwsgi
    uwsgi()
    EOF

    cat << EOF > setup.py
    # -*- coding: utf-8 -*-
    from setuptools import setup, find_packages
    from greatproject import __version__ as version
    entry_points = {'console_scripts': ['greatproject-manage = djangofloor.scripts:manage',
                                        'greatproject-celery = djangofloor.scripts:celery',
                                        'greatproject-uswgi = djangofloor.scripts:uswgi',
                                        'greatproject-gunicorn = djangofloor.scripts:gunicorn']}
    setup(
        name='greatproject',
        version=version,
        entry_points=entry_points,
        packages=find_packages(),
        include_package_data=True,
        install_requires=['djangofloor'],
    )
    EOF

    cat << EOF > greatproject/defaults.py
    FLOOR_PROJECT_NAME = 'GreatProject'
    FLOOR_INSTALLED_APPS = ['greatproject', ]
    EOF


That's it!

Let's start playing :-) ::

    python manage.py config
    python manage.py collectstatic --noinput
    python manage.py migrate
    python manage.py runserver


Open your favorite browser and explore http://localhost:9000/.