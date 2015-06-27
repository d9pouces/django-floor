Settings
========

IMHO, dealing with Django settings is a nightmare for at least two reasons.
Even if you are building a custom website, some settings are common to both your developper instance and your production instance, and others settings are different.
So, *you must maintain two differents files with lots of common parts.*

Moreover, setting file (with secret data like database passwords) is expected to be in your project.
*You mix versionned files (the code) and non-versionned files (the settings), and any reinstallation can overwrite your settings.*

With DjangoFloor, you can forget these drawbacks. You always use `djangofloor.settings` as Django settings, but this module does not contain any settings.
This module can smartly merge settings from three different sources:

    * default DjangoFloor settings (`djangofloor.defaults`),
    * default settings for your wonderful website (`myproject.defaults`, for settings like INSTALLED_APPS, MIDDLEWARES, and so on),
    * local settings, specific to an instance (`[prefix]/etc/myproject/settings.py`) for settings like database infos,
    * you can even define settings in a more traditionnal way, with .ini files.

Default DjangoFloor settings are overriden by your project defaults, which are overriden by local settings.
Run `myproject-manage config` to display all configuration files, in order of precedence:

    * Python local configuration: [...]/etc/archeolog_server/settings.py (defined in environment by DJANGOFLOOR_PYTHON_SETTINGS)
    * INI local configuration: [...]/etc/archeolog_server/settings.ini (defined in environment by DJANGOFLOOR_INI_SETTINGS)
    * Default project settings: [...]/[...]/defaults.py (defined in environment by DJANGOFLOOR_PROJECT_DEFAULTS)
    * Other default settings: [...]/[...]/djangofloor/defaults.py

Existing files are displayed in blue, missing files are displayed in red.
All Python settings files have the same syntax as the traditionnal Django settings file.


However, any string setting can use reference other settings through `string.Formatter`. An example should be clearer:

DjangoFloor default settings::

    LOCAL_PATH = '/tmp/'
    MEDIA_ROOT = '{DATA_PATH}/media'
    STATIC_ROOT = '{DATA_PATH}/static'
    LOG_ROOT = '{DATA_PATH}/logs'

your project default settings (which override DjangoFloor settings)::

    MEDIA_ROOT = '{DATA_PATH}/data'

your local settings (which have the top priority)::

    LOCAL_PATH = '/var/www/data'
    STATIC_ROOT = '/var/www/static'

in the Django shell, you can check that settings are gracefully merged together::

    >>> from django.conf import settings
    >>> print(settings.LOCAL_PATH)  # overriden in local settings
    /var/www/data
    >>> print(settings.MEDIA_ROOT)  # overriden in project defaults but not in local settings
    /var/www/data/data
    >>> print(settings.STATIC_ROOT)  # overriden in local settings
    /var/www/static
    >>> print(settings.LOG_ROOT)  # reference LOCAL_PATH in DjangoFloor, which is overriden
    /var/www/data/logs

How to use it?
--------------

Since your settings are expected to be in  `myproject.defaults` and in `[prefix]/etc/myproject/settings.py`, DjangoFloor must to guess your project name `myproject`.
There are three ways to let it know `myproject`:

  -  use one of the provided commands `djangofloor-celery`, `djangofloor-manage`, `djangofloor-gunicorn` or `djangofloor-uwsgi` with the option `--dfproject myproject`
  -  `export DJANGOFLOOR_PROJECT_NAME=myproject` before using `djangofloor-celery`, `djangofloor-manage`, `djangofloor-gunicorn` or `djangofloor-uwsgi`
  -  copy `djangofloor-celery`, `djangofloor-manage`, `djangofloor-gunicorn` or `djangofloor-uwsgi` as `myproject-[celery|manage|gunicorn|uwsgi`.

You can change `myproject.defaults` to another value with the environment variable `DJANGOFLOOR_PROJECT_SETTINGS`
You can specify another local setting files with the option `--dfconf [path/to/settings.py]`

If you run `[prefix]/bin/myproject-manage`, then local settings are expected in `[prefix]/etc/myproject/settings.py`.
If you run directly from the source (without installing), local settings are expected in `working_dir/my_project_configuration.py`.


And Pycharm (or other IDEs)?
----------------------------

PyCharm (and, I guess, many other IDEs) has built-in support for the Django framework and is able to use the settings module for a better auto-completion.
However, it is not able to use such a complex system.

DjangoFloor can generate a merged settings file for you:

.. code-block:: bash

  myproject-manage config --merge > pycharm_settings.py

Then you can use this file as Django settings in PyCharm.

Notes
-----

  - Only settings in capitals are taken into account.
  - interpolation of settings is also recursively processed for dicts, lists, tuples and sets.
  - You can use `djangofloor.utils.[DirectoryPath|FilePath]('{LOCAL_PATH}/static')`: required directories will be automatically created.
  - If you have a settings MY_SETTING and another called MY_SETTING_HELP, the latter will be used as help for `manage.py config`.


Full list of settings
---------------------

DjangoFloor define a few new settings.

    - `FLOOR_INDEX`: django view your the website index,
    - `FLOOR_INSTALLED_APPS`: list of extra Django apps (including yours),
    - `FLOOR_PROJECT_NAME`: your project name,
    - `FLOOR_URL_CONF`: your extra URL configuration,
    - `FLOOR_FAKE_AUTHENTICATION_USERNAME`: set it to any username you want (allow to fake a HTTP authentication, like Kerberos). Only for debugging purposes,
    - `FLOOR_FAKE_AUTHENTICATION_GROUPS`: set it to the names of the groups you want for the fake user. Only for debugging purposes,
    - `FLOOR_WS_FACILITY`: websocket facility for the signal implementation,
    - `FLOOR_USE_WS4REDIS`: is automatically set if you installed ws4redis (do not change it in your settings).

    - `LOCAL_PATH`: the base directory for all data,
    - `BIND_ADDRESS`: the default bind address for the runserver command, or for gunicorn,
    - `REDIS_HOST` and `REDIS_PORT`: this is self-explained,

    - `THREADS`, `WORKERS`, `MAX_REQUESTS`: all these settings are related to gunicorn
    - `REVERSE_PROXY_IPS`: the IPs of your reverse proxy, allowing authenticating users by the `REMOTE_USER` header
    - `FLOOR_DEFAULT_GROUP_NAME`: name of the default group for newly created users (when authenticated by the reverse proxy). Leave it to `None` to avoid this behavior.

Using flat config files
-----------------------

If your application has a few settings available to the end-user (typically the coordinates of the database), you can also put them into a .ini file.
However, this require a mapping between the option in the .ini file and the settings.

This dictionnary is expected in the file `myproject/iniconf.py`, with a single variable named `INI_MAPPING` which is a list of :class:`djangofloor.iniconf.OptionParser`.
For example:

.. code-block:: python

    INI_MAPPING = [
        OptionParser('DATABASE_ENGINE', 'database.engine'),
        OptionParser('DATABASE_NAME', 'database.name'),
        OptionParser('DATABASE_USER', 'database.user'),
        OptionParser('DATABASE_PASSWORD', 'database.password'),
        OptionParser('DATABASE_HOST', 'database.host'),
        OptionParser('DATABASE_PORT', 'database.port'),
    ]

In this case, DjangoFloor will look for a file `[prefix]/etc/myproject/settings.ini` with a section `database`, with the options `engine`, `name`, `user`, `password`, `host` and `port`:

.. code-block:: ini

    [database]
    host = localhost
    user = my_user
    password = my_secret_password
    engine = django.db.backends.postgresql_psycopg2

The exact expected filename is always given by the command `myproject-manage config`.