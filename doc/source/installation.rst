Installing
==========

There are several ways to install DjangoFloor.

Installing from pip
-------------------

.. code-block:: bash

  pip install djangofloor

Installing from source
----------------------

If you prefer install directly from the source:

.. code-block:: bash

  git clone https://github.com/d9pouces/django-floor.git DjangoFloor
  cd DjangoFloor
  python setup.py install

Dependencies
------------

Of course, DjangoFloor is not a standalone library and requires several packages:

  * aiohttp-wsgi,
  * django >= 1.11,
  * celery,
  * django-bootstrap3,
  * redis,
  * gunicorn,
  * pip,
  * aiohttp,
  * asyncio_redis.

Several other dependencies are not mandatory but are really useful:

  * django-pipeline,
  * django-debug-toolbar,
  * django-redis-sessions,
  * django-redis,
  * psutil.

You can install these optional dependencies:

.. code-block:: bash

  pip install djangofloor[extra]


Virtualenvs
-----------

You really should consider using `virtualenvs <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_, allowing
to create several isolated Python environments (each virtualenv having its own set of libraries).
`virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_ may help you to create and manage your virtualenvs.
