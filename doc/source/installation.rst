Installing / Upgrading
======================

Environment
-----------

We strongly recommend to create a virtualenvironment and the use of `virtualenvwrapper`.
Go to the `doc <https://virtualenvwrapper.readthedocs.org/>`_ to discover how to use it.::

    mkvirtualenv djangofloor


You can use DjangoFloor with Python 2.7 or 3.3, 3.4 and 3.5.

Simple installation
-------------------

The simplest way is to use pip::

    pip install djangofloor


You can also install with optional dependencies::

    pip install djangofloor[websocket,scss]



Installing from source
----------------------

If you prefer install directly from the source::

    git clone https://github.com/d9pouces/django-floor.git
    cd django-floor
    python setup.py install

Upgrading
---------

Again, the easiest way is to use pip::

    pip install djangofloor --upgrade

