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
  * local settings, specific to an instance (`[prefix]/etc/myproject/settings.py`) for settings like database infos.

Default DjangoFloor settings are overriden by your project defaults, which are overriden by local settings.
Moreover, each string setting can use reference to other settings through `string.Formatter`.

For example:
DjangoFloor default settings:

    LOCAL_PATH = '/tmp/'
    MEDIA_ROOT = '{DATA_PATH}/media'
    STATIC_ROOT = '{DATA_PATH}/static'

your project default settings:

    MEDIA_ROOT = '{DATA_PATH}/data'

your local settings:

    LOCAL_PATH = '/var/www/data'
    STATIC_ROOT = '/var/www/static'

in the Django shell, you can check that settings are gracefully merged together:

    >>> from django.conf import settings
    >>> print(settings.LOCAL_PATH)
    /var/www/data
    >>> print(settings.MEDIA_ROOT)
    /var/www/data/data
    >>> print(settings.STATIC_ROOT)
    /var/www/static

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


Use `myproject-manage config` to check all used settings files.

And Pycharm (or other IDEs)?
----------------------------

PyCharm (and, I guess, many other IDEs) has built-in support for the Django framework and is able to use the settings module for a better auto-completion.
However, it is not able to use such a complex system.

DjangoFloor can generate a merged settings file for you::

  myproject-manage config --merge > pycharm_settings.py

Then you can use this file as Django settings in PyCharm.

Notes
-----

  - Only settings in capitals are taken into account.
  - interpolation of settings is also recursively processed for dicts, lists, tuples and sets.
  - You can use `djangofloor.utils.[DirectoryPath|FilePath]('{LOCAL_PATH}/static')`: directory will be automatically created.
  - Use `manage.py config` to show actual values and where are expected your local settings.
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

    - `LOCAL_PATH`: the base directory for all data,
    - `BIND_ADDRESS`: the default bind address for the runserver command, or for gunicorn,
    - `REDIS_HOST` and `REDIS_PORT`: this is self-explained,

    - `THREADS`, `WORKERS`, `GUNICORN_PID_FILE`, `GUNICORN_ERROR_LOG_FILE`, `GUNICORN_ACCESS_LOG_FILE`, `GUNICORN_LOG_LEVEL`, `MAX_REQUESTS`: all these settings are related to gunicorn
    - `REVERSE_PROXY_IPS`: the IPs of your reverse proxy, allowing authenticating users by the `REMOTE_USER` header
    - `DEFAULT_GROUP_NAME`: name of the default group for newly created users (when authenticated by the reverse proxy)
