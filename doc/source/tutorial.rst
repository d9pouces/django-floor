Tutorial
========

This tutorial shows you how to create a new DjangoFloor-based website.

Basically, there are two ways for creating a new project: from scratch, or with `StarterPyth <https://github.com/d9pouces/StarterPyth>`_.

Creating a new project from scratch
-----------------------------------

Let assume that our great idea is called `myproject`.

As always, we start by creating a new virtualenv:

.. code-block:: bash

    mkvirtualenv myproject -p `which python2.7`
    pip install djangofloor

We can create required files and directories:

.. code-block:: bash

    mkdir -p myproject/myproject/tests myproject/myproject/static myproject/myproject/templates
    cd myproject
    touch myproject/models.py
    echo "__version__ = '1.0.0'" > myproject/__init__.py

    cat << EOF > myproject-manage.py
    from djangofloor.scripts import manage
    manage()
    EOF
    cat << EOF > myproject-gunicorn.py
    from djangofloor.scripts import gunicorn
    gunicorn()
    EOF
    cat << EOF > myproject-celery.py
    from djangofloor.scripts import celery
    celery()
    EOF
    cat << EOF > myproject-uwsgi.py
    from djangofloor.scripts import uwsgi
    uwsgi()
    EOF

    cat << EOF > setup.py
    # -*- coding: utf-8 -*-
    from setuptools import setup, find_packages
    from myproject import __version__ as version
    entry_points = {'console_scripts': ['myproject-manage = djangofloor.scripts:manage',
                                        'myproject-celery = djangofloor.scripts:celery',
                                        'myproject-uswgi = djangofloor.scripts:uswgi',
                                        'myproject-gunicorn = djangofloor.scripts:gunicorn']}
    setup(
        name='myproject',
        version=version,
        entry_points=entry_points,
        packages=find_packages(),
        include_package_data=True,
        install_requires=['djangofloor'],
    )
    EOF

    cat << EOF > myproject/defaults.py
    FLOOR_PROJECT_NAME = 'myproject'
    FLOOR_INSTALLED_APPS = ['myproject', ]
    EOF


That's it!

Let's start playing :-):

.. code-block:: bash

    python myproject-manage.py config
    python myproject-manage.py collectstatic --noinput
    python myproject-manage.py migrate
    python myproject-manage.py runserver


Open your favorite browser and explore http://localhost:9000/.


Creating a new project with Starterpyth
---------------------------------------

It's a bit simpler:

.. code-block:: bash

    mkvirtualenv myproject -p `which python2.7`
    pip install starterpyth
    starterpyth-bin
    [some questions…]
    cd myproject
    python myproject-manage.py config
    python myproject-manage.py collectstatic --noinput
    python myproject-manage.py migrate
    python myproject-manage.py runserver

