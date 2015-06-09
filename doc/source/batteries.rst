Included dependencies
=====================

Django
------

Ok, you should already know Django ;)

Gunicorn
--------

`Gunicorn <http://gunicorn.org>`_ 'Green Unicorn' is a Python WSGI HTTP Server for UNIX.
It's a pre-fork worker model ported from Ruby's Unicorn project.
The Gunicorn server is broadly compatible with various web frameworks, simply implemented, light on server resources, and fairly speedy.


Gunicorn is in pure Python, very simple to use and allow an easy production deployment.


Bootstrap3
----------

DjangoFloor comes with Bootstrap3 and JQuery. `Bootstrap3 <http://getbootstrap.com>`_ is the most popular HTML, CSS, and JS framework for developing responsive, mobile first projects on the web
You obtain nice pages out-of-box. The drawback is of course that many websites have the same look.

Required dependencies:

    * django-bootstrap3,
    * django-admin-bootstrapped.


Django-Debug-Toolbar
--------------------

`Django-Debug-Toolbar <http://django-debug-toolbar.readthedocs.org/>`_ is a configurable set of panels that display various debug information about the current request/response.

Required dependencies:

    * django-debug-toolbar.

CSS and JS files
----------------

`Pipeline <https://django-pipeline.readthedocs.org/en>`_ is an asset packaging library for Django, providing both CSS and JavaScript concatenation and compression, built-in JavaScript template support, and optional data-URI image and font embedding.

Required dependencies:
    * django-pipeline,
    * jsmin,
    * rcssmin.

Redis
-----

Traditionnal SQL databases (PostgreSQL or MySQL, for example) are very good at storing your persistent data.
However, there are several usages for which such databases are not recommended:

    * caching web pages,
    * broker for Celery,
    * websockets (currently only with Python 2.6/2.7),
    * session storage.

All these usages can be fullfilled by some other technology (for example, AMQP as Celery brocker, memcached for… cache and your default SQL engine for sessions).
Redis is performant and very easy to use, and it limits the number of different systems in your architecture.

Several dependencies allow to properly use Redis:

    * django-redis,
    * django-redis-cache.

If you can use  C extensions, you should also install (and use) django-redis-sessions-fork.


Websockets
----------

Currently, only Python 2.6/2.7 allow to use websockets.

These dependencies are required:

    * django-websocket-redis,
    * gevent,
    * uwsgi.


Celery
------

`Celery <http://www.celeryproject.org>`_  is an asynchronous task queue/job queue based on distributed message passing.
It is focused on real-time operation, but supports scheduling as well.
The execution units, called tasks, are executed concurrently on a single or more worker servers using multiprocessing, Eventlet, or gevent.
Tasks can execute asynchronously (in the background) or synchronously (wait until ready).

This dependency is required:

    * celery.


You should launch a Celery worker::

    djangofloor-celery --dfproject myproject worker
    myproject-celery worker

Authentication
--------------

`django-allauth <http://www.intenct.nl/projects/django-allauth/>`_ is an integrated set of Django applications addressing authentication, registration, account management as well as 3rd party (social) account authentication.

This dependency is required:

    * django-allauth.
