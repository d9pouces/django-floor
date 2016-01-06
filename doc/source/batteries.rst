Included dependencies
=====================

Here is a list of the dependencies, with a short description. All these dependencies are plain Python, they can be installed without compiling C extensions.

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

    * django-bootstrap3.


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
    * slimit,
    * rcssmin (directly included in djangofloor.df_pipeline to ease installation - the official package require the compilation of a C extension).

By default, `PIPELINE_ENABLED` is set to `False`, as some bugs can appear in JS.

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

Some settings are related to Redis:

    * all values:
        .. code-block:: python

            REDIS_HOST = 'localhost'  # valid by default
            REDIS_PORT = 6379  # valid by default

    * Celery:
        .. code-block:: python

            USE_CELERY = True
            CELERY_TIMEZONE = '{TIME_ZONE}'  # valid by default
            BROKER_DB = 13
            BROKER_URL = 'redis://{REDIS_HOST}:{REDIS_PORT}/{BROKER_DB}'  # valid by default
            CELERY_APP = 'djangofloor'  # valid by default
            CELERY_CREATE_DIRS = True  # valid by default

    * cache:
        .. code-block:: python

            CACHES = {
                'default': {
                    'BACKEND': 'redis_cache.RedisCache',
                    'LOCATION': '{REDIS_HOST}:{REDIS_PORT}',
                },
            }

    * sessions:
        .. code-block:: python

            SESSION_ENGINE = 'redis_sessions.session'
            SESSION_REDIS_PREFIX = 'session'  # valid by default
            SESSION_REDIS_HOST = '{REDIS_HOST}'  # valid by default
            SESSION_REDIS_PORT = '{REDIS_PORT}'  # valid by default
            SESSION_REDIS_DB = 10  # valid by default

    * websockets emulation (if you cannot use native websockets):
        .. code-block:: python

            WS4REDIS_EMULATION_INTERVAL = 1000  # (in ms, you should not set it below 500 or 1,000)
            WEBSOCKET_URL = '/ws/'  # valid by default

    * websockets:
        .. code-block:: python

            FLOOR_USE_WS4REDIS  # should automatically set to `True`
            WEBSOCKET_URL = '/ws/'  # valid by default
            WS4REDIS_DB = 15
            WS4REDIS_CONNECTION = {'host': '{REDIS_HOST}', 'port': '{REDIS_PORT}', 'db': WS4REDIS_DB, }
            WS4REDIS_EXPIRE = 0  # valid by default
            WS4REDIS_PREFIX = 'ws'  # valid by default
            WS4REDIS_HEARTBEAT = '--HEARTBEAT--'  # valid by default
            WSGI_APPLICATION = 'ws4redis.django_runserver.application'  # valid by default
            WS4REDIS_SUBSCRIBER = 'djangofloor.df_ws4redis.Subscriber'  # valid by default
            FLOOR_WS_FACILITY = 'djangofloor'  # valid by default


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


You must launch a Celery worker::

    djangofloor-celery --dfproject myproject worker
    myproject-celery worker

Authentication
--------------

`django-allauth <http://www.intenct.nl/projects/django-allauth/>`_ is an integrated set of Django applications addressing authentication, registration, account management as well as 3rd party (social) account authentication.

This dependency is required:

    * django-allauth.
