django-floor
============

A common base for modern and complete Django websites, with several common tools integrated, a simple signal-based communication system and an easy-to-use settings system.

Together the third-party tools shipped with djangofloor, there is two major advantages: settings and signals (with websockets!).
You must use Python 2.7 to play with websockets. Otherwise, DjangoFloor is fully compatible with Python 3.2+.

You can find a complete documentation here: http://django-floor.readthedocs.org/en/latest/ .
The source code is available on Github: https://github.com/d9pouces/django-floor .


Installing
----------

    pip install djangofloor
    
    

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

  -  use provided commands `djangofloor-celery`, `djangofloor-manage`, `djangofloor-gunicorn` or `djangofloor-uwsgi` with the option `--dfproject myproject`
  -  `export DJANGOFLOOR_PROJECT_NAME=myproject` before using `djangofloor-celery`, `djangofloor-manage`, `djangofloor-gunicorn` or `djangofloor-uwsgi`
  -  renaming `djangofloor-celery`, `djangofloor-manage`, `djangofloor-gunicorn` or `djangofloor-uwsgi` to `myproject-[celery|manage|gunicorn|uwsgi`

You can change `myproject.defaults` to another value with the environment variable `DJANGOFLOOR_PROJECT_SETTINGS`
You can specify another local setting files with the option `--dfconf [path/to/settings.py]`
  
If you run `[prefix]/bin/myproject-manage`, then local settings are expected in `[prefix]/etc/myproject/settings.py`.
If you run without installation, local settings are expected in `working_dir/my_project_configuration.py`.


Notes:

  - Only settings in capitals are taken into account.
  - interpolation of settings is also recursively processed for dicts, lists, tuples and sets.
  - You can use `djangofloor.utils.[DirectoryPath|FilePath]('{LOCAL_PATH}/static')`: directory will be automatically created.
  - Use `manage.py config` to show actual values and where are expected your local settings.
  - If you have a settings MY_SETTING and another called MY_SETTING_HELP, the latter will be used as help for `manage.py config`.


Signals
-------

Communications between Python world and Javascript one is often awful, with a lot of boilerplate.
The main goal of my implementation of signals is to really limit this code and to easily integrate Celery and websockets.
 
In DjangoFloor, you have four kind of codes:

  * JavaScript (can call Django views or communicate with websockets)
  * Python code in Django views (receives a HttpRequest as argument and returns a HttpResponse, can call Celery tasks)
  * Python code in Celery tasks (receives some arguments and often return None, can only call other tasks, cannot communicate with Django, websocket or JS)
  * Python code in the websocket world (can call some Celery tasks but cannot perform any blocking call or call Django views)
  

In DjangoFloor, a signal is a simple name (a unicode string). You connect some code (JS or Python) to this name. Then you can call a signal (with some arguments).

Python example:

    from djangofloor.decorators import connect
    @connect(path='demo.my_signal')
    def my_signal(request, arg):
        [ some interesting code ]
        print('blablabla', arg)
        
A lot of computation, and this code must be used through Celery?

    from djangofloor.decorators import connect
    @connect(path='demo.my_signal', delayed=True)
    def my_signal(request, arg):
        [ some interesting code ]
        print('blablabla', arg)
        
You can allow non-connected users to trigger the signal:

    from djangofloor.decorators import connect
    @connect(path='demo.my_signal', auth_required=False)
    def my_signal(request, arg):
        [ some interesting code ]
        print('blablabla', arg)
        
JavaScript example:

    df.connect('demo.my_signal', function (options) { alert(options.arg); });


Ok, that is enough to connect any code to a signal. Now, if you want to call this code in Python: 
 
    from djangofloor.tasks import call, SESSION
    call('demo.my_signal', request, SESSION, arg='argument')

And in JavaScript?

    df.call('demo.my_signal', {arg: 'argument'})
    

*Any Python or Javascript can call any Python or JavaScript signal, with (almost) the same syntax.*

Notes:

  - You can prevent Python code from being called by JS: @connect(path='demo.my_signal', allow_from_client=False)
  - You can prevent Python code from calling the javascript side of calls call('demo.my_signal', request, None, \*\*kwargs)
  - You can propagate Python signals to all sessions of the logged user (use USER instead of SESSION), any logged user (use BROADCAST), or a limited set of users with {USER: ['username']}
  - Several functions (either JS or Python) can be connected to the same signal
  - Python calls require a `request`, which can be either a standard `django.http.HttpRequest` or a `djangofloor.decorators.SignalRequest`.
    `SignalRequest` propagates the username and the session key from call to call and is provided from a JS key.   
  - Required JS files (jquery, ws4redis and djangofloor) are defined in `settings.PIPELINE_JS`
  
  
**Degraded mode:** Maybe you cannot use websockets (Python 3…). You can still use signals through HTTP requests.
Set `FLOOR_USE_WS4REDIS` to False. Each Python signal return a list of dict `{'signal': 'signal.name', 'options': kwargs}`.
These dictionnaries will act as regular signals. Of course, you can only propagate JS signals at the end of a signal called by the client.
 
 
Batteries included
------------------

  * uwsgi
  * bootstrap3 (django-bootstrap3)
  * font-awesome
  * SCSS, CSS and JS minimizing (django-pipeline with pyscss, jsmin and rcssmin)
  * templates for authentication (django-allauth)
  * distributed tasks (celery via Redis)
  * new cache, websockets and sessions engines (django-websocket-redis, django-redis-sessions-fork, django-redis-cache)
  * django-debug-toolbar
  * gunicorn (of course, you can also use uwsgi)
  * celery
  

Creating a new site
-------------------

  * Just create a standard Python module with the same structure than `demo` (provided with DjangoFloor).
  Compared to a classical Django app, it only require a `defaults` module.
  Signals are automatically discovered by importing `APP.signals` files (for all APP in INSTALLED_APPS).
  
  
  mkvirtualenv demo -p `which python2.7`
  python setup.py develop
  djangofloor-manage --dfproject demo migrate
  djangofloor-manage --dfproject demo runserver
  djangofloor-celery --dfproject demo worker
  
Of course, you can also use:

  demo-manage migrate
  demo-manage collectstatic
  demo-manage runserver
  demo-celery worker
  
  
Extra stuff
-----------


  * Avoid to modify INSTALLED_APPS if you only want to add extra apps: you can use FLOOR_INSTALLED_APPS instead.


Authentication:

  * All settings required by a proper HTTP authentication (Kerberos, SSO, …) are valid.
  * FLOOR_AUTHENTICATION_HEADER = 'HTTP_REMOTE_USER', SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https'), USE_X_FORWARDED_HOST = True
  * you just have to correctly set REVERSE_PROXY_IPS
  * DEFAULT_GROUP_NAME can be set to automatically add a default group to new users
  * You can emulate this authentication for dev:
     * FLOOR_FAKE_AUTHENTICATION_USERNAME : set it to the username you want to emulate (or to `None` to disable it)
     * FLOOR_FAKE_AUTHENTICATION_GROUPS : set it to the list of groups of the test user

File management:

  * DjangoFloor comes with Django-Pipeline and pure-Python compressors: just set PIPELINE_ENABLED to True
  * Sending large files:
      * If you use Apache and mod_x_sendfile, set USE_X_SEND_FILE to True
      * If you use NGinx, set X_ACCEL_REDIRECT
      * Then use `djangofloor.views.send_file` to send a file in an optimized way
       
       
Extra setup options
-------------------

    pip install djangofloor[websocket,scss]

websocket only works with Python 2.7 and requires uwsgi. scss is required to install pyscss, allowing 
to compile SCSS files (superset of the CSS language) with the collectstatic command (check the django-pipeline documentation).
