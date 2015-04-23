django-floor
============

DjangoFloor aims

A common base for modern and complete Django websites, with several common tools integrated, a simple signal-based communication system and an easy-to-use settings system.

Together the third-party tools shipped with djangofloor, there is two major advantages: settings and signals (with websockets!).

Installing
----------

    mkvirtualenv djangofloor -p `which python2.7`
    pip install djangofloor
    djangofloor-manage  --dfproject djangofloor.demo migrate
    djangofloor-manage  --dfproject djangofloor.demo runserver
  
Open your brower on `http://localhost:9000/test.html` 
Full demo: assume that you have a Redis server on its standard port (6379). In `djangofloor.demo.defaults`, uncomment the following lines:

    # WSGI_APPLICATION = 'ws4redis.django_runserver.application'
    # USE_WS4REDIS = True
    # USE_CELERY = True

Run   

    djangofloor-manage  --dfproject djangofloor.demo runserver
    djangofloor-celery  --dfproject djangofloor.demo worker

Go back to `http://localhost:9000/test.html` and try websockets and Celery.
  

Settings
--------

IMHO, dealing with Django settings is a nightmare for at least two reasons. 
Even if you are building a custom website, some settings are common to both your developper instance and your production instance, and others are different.
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

*How to use it?* Since your settings are expected to be in  `myproject.defaults` and in `[prefix]/etc/myproject/settings.py`, DjangoFloor must determine `myproject`.
There are three ways to let it know `myproject`:

1) use provided commands `djangofloor-celery`, `djangofloor-manage`, `djangofloor-gunicorn` or `djangofloor-uwsgi` with the option `--dfproject myproject`
2) `export DJANGOFLOOR_PROJECT_NAME=myproject` before using `djangofloor-celery`, `djangofloor-manage`, `djangofloor-gunicorn` or `djangofloor-uwsgi`
3) renaming `djangofloor-celery`, `djangofloor-manage`, `djangofloor-gunicorn` or `djangofloor-uwsgi` to `myproject-[celery|manage|gunicorn|uwsgi`

You can change `myproject.defaults` to another value with the environment variable `DJANGOFLOOR_PROJECT_SETTINGS`
You can specify another local setting files with the option `--dfconf [path/to/settings.py]`
  
If you run `[prefix]/bin/myproject-manage`, then local settings are expected in `[prefix]/etc/myproject/settings.py`.
If you run without installation, local settings are expected in `working_dir/my_project_configuration.py`.


Notes:

    1) Only settings in capitals are taken into account.
    2) interpolation of settings is also recursively processed for dicts, lists, tuples and sets.
    3) You can use `djangofloor.utils.[DirectoryPath|FilePath]('{LOCAL_PATH}/static')`: directory will be automatically created.
    4) Use `manage.py config` to show actual values and where are expected your local settings.
    5) If you have a settings MY_SETTING and another called MY_SETTING_HELP, the latter will be used as help for `manage.py config`.

Signals
-------




Batteries included
------------------

  * uwsgi
  * bootstrap3 (django-bootstrap3 and django-admin-bootstrapped)
  * font-awesome
  * CSS and JS minimizing (django-pipeline, jsmin and rcssmin)
  * templates for authentication (django-allauth)
  * distributed tasks (celery via Redis)
  * new cache, websockets and sessions engines (django-websocket-redis, django-redis-sessions-fork, django-redis-cache)
  * django-debug-toolbar
  * gunicorn (of course, you can also use uwsgi)

