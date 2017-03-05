Main features… and how to disable them
======================================

Settings system
---------------

DjangoFloor allows to merge several files to define your settings:

  * `DjangoFloor.conf.defaults` that aims at providing good default values,
  * `yourproject.defaults` for your project-specific settings,
  * `/etc/yourproject/settings.ini` and `/etc/yourproject/settings.py` for installation-dependent settings,
  * `./local_settings.py` and `./local_settings.ini` setting files in the working directory.


You should define your project-wide settings in `yourproject.defaults` and the list of installation-specific settings in `yourproject.iniconf`.
Development-specific settings (`DEBUG = True`!) can be written into `local_settings.py` and added to your source.

If you do not want to use this setting system: just set the `DJANGO_SETTINGS_MODULE` environment variable before running the scripts.

Deactivate redis
----------------

To disable background tasks, websockets and Redis cache, you must change these settings:

  * `CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-snowflake'}}`
  * `WEBSOCKET_URL = None`
  * `USE_CELERY = False`


Default URLs
------------

By default, DjangoFloor provides a complete URL configuration:

  * authentication pages,
  * signal definitions,
  * websockets,
  * monitoring view,
  * a global search view,
  * Django admin site,
  * javascript translation (i18n),
  * static and media files,
  * Django debug toolbar.

If you prefer to use your own URL configuration, just set the `ROOT_URLCONF` setting.

Middleware and context processors
---------------------------------

DjangoFloor offers custom middleware (:class:`djangofloor.middleware.DjangoFloorMiddleware`) and context processors (:class:`djangofloor.context_processors.context_base`). You can disable them by overriding the settings `TEMPLATE_CONTEXT_PROCESSORS` and `MIDDLEWARE_CLASSES`.

DjangoFloor also provides a backend for authenticating users (:class:`djangofloor.backends.DefaultGroupsRemoteUserBackend`). Override the `AUTHENTICATION_BACKENDS` setting to disable it.

Django-Pipeline
---------------

DjangoFloor provides a valid configuration for Django-Pipeline with Bootstrap3, Font-Awesome and a few specific scripts or style sheets.
Just override the `PIPELINE` setting to disable them.

Scripts
-------

DjangoFloor provides an easy way to run Django, Celery or aiohttp commands.
There are several main functions in :mod:`djangofloor.scripts` that automatically detect the name of your project from the script name and loads settings from the corresponding Python module (`your_projects.defaults`).
A classical `setup.py` script should create the following console_scripts as `entry_points`:

  * '{your_project}-celery = djangofloor.scripts:celery',
  * '{your_project}-django = djangofloor.scripts:django',
  * '{your_project}-aiohttp = djangofloor.scripts:aiohttp'.

If you want to use custom scripts, you just have to remove these lines from your `setup.py`.

Using Gunicorn
--------------

By default, DjangoFloor uses `aiohttp <http://aiohttp.readthedocs.io>`_ as application server. If you do not use websockets (or if you want different application servers for WS and HTTP requests), you can use `Gunicorn <https://gunicorn-docs.readthedocs.io>`_.
Just add to your `setup.py` file, in the `console_scripts` section of the `entry_points`, '{your_project}-gunicorn = djangofloor.scripts:gunicorn'


Logs
----

DjangoFloor provides a log configuration based on:

  * the `DEBUG` mode (if `True`, everything is logged to the console),
  * the `LOG_DIRECTORY` value for storing infos and errors in rotated files,
  * the `LOG_REMOTE_URL` value for send errors to a syslog (or logd) server.

This log configuration is provided by :meth:`djangofloor.log.log_configuration`.