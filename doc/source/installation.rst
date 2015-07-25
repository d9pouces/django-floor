Installing / Upgrading
======================

Environment
-----------

DjangoFloor is compatible with Python 2.7, 3.2, 3.3, 3.4 and 3.5.
We strongly recommend to create a virtualenvironment and the use of `virtualenvwrapper`.
Go to the `doc <https://virtualenvwrapper.readthedocs.org/>`_ to discover how to use it.

.. code-block:: bash

    mkvirtualenv djangofloor


Simple installation
-------------------

The simplest way is to use pip:

.. code-block:: bash

    pip install djangofloor


You can also install with optional dependencies:

.. code-block:: bash

    pip install djangofloor[websocket,scss]

Installing from source
----------------------

If you prefer install directly from the source:

.. code-block:: bash

    git clone https://github.com/d9pouces/django-floor.git
    cd django-floor
    python setup.py install

Upgrading
---------

Again, the easiest way is to use pip:

.. code-block:: bash

    pip install djangofloor --upgrade

