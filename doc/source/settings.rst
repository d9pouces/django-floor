Settings system
===============

By default, Django uses a single Python file for all settings.
However, these settings could be organized into three categories:

  * settings that are very common and that can be kept as-is for most projects (`USE_TZ = True` or `MEDIA_URL = '/media/'`),
  * settings that are specific to your project but common to all instances of your project (like `INSTALLED_APPS`),
  * settings that are installation-dependent (`DATABASE_PASSWORD`, …)

You usually have to maintain at least two versions of the same settings file (dev and prod, or one that is versionned and the other one for prod), with the risk of desynchronized files.

On the contrary, DjangoFloor allows to dynamically merge several files to define your settings:

  * :mod:`djangofloor.conf.defaults` that aims at providing good default values,
  * `yourproject.defaults` for your project-specific settings,
  * `/etc/yourproject/settings.py` for installation-dependent settings.

You can define a list of settings that are read from a traditionnal text configuration file (`.ini format <https://docs.python.org/3/library/configparser.html>`_).
DjangoFloor also searches for `local_settings.py` and `local_settings.ini` setting files in the working directory.

Defining settings
-----------------

  * many settings are defined in :mod:`djangofloor.conf.defaults`,
  * define your project-wide settings in `<project_root>/yourproject/defaults.py` (only define overriden settings),
  * translation from `.ini` config files to Python settings is defined by a list named `INI_MAPPING` in `<project_root>/yourproject/iniconf.py`,
  * development settings (like `DEBUG = True`) can be defined in  `<project_root>/local_settings.py`,

Your `defaults.py` has the same structure than a traditionnal Django `settings.py` file (but with less variables ^^ )
`INI_MAPPING` is a list of :class:`djangofloor.conf.config_values.ConfigValue` (or of its subclasses, some of them defined in the same module).
Several lists are already defined in :mod:`djangofloor.conf.mapping`.

Smarter settings
----------------

With DjangoFloor, settings can be built at runtime from some other settings.
For example, imagine that you have the following settings in your Django project:

.. code-block:: python

    LOG_DIRECTORY = '/var/myproject/logs'
    STATIC_ROOT = '/var/myproject/static'
    MEDIA_ROOT = '/var/myproject/media'
    FILE_UPLOAD_TEMP_DIR = '/var/myproject/tmp'


Modifying the base directory `/var/myproject` implies that you have four variables to change (and you will forget to change at least one).
With DjangoFloor, things are simpler:

.. code-block:: python

    LOCAL_PATH = '/var/myproject'
    LOG_DIRECTORY = '{LOCAL_PATH}/logs'
    STATIC_ROOT = '{LOCAL_PATH}/static'
    MEDIA_ROOT = '{LOCAL_PATH}/media'
    FILE_UPLOAD_TEMP_DIR = '{LOCAL_PATH}/tmp'


You only have to redefine `LOCAL_PATH`!
You can even go further:

.. code-block:: python

    from djangofloor.conf.config_values import Directory
    LOCAL_PATH = Directory('/var/myproject')
    LOG_DIRECTORY = Directory('{LOCAL_PATH}/logs')
    STATIC_ROOT = Directory('{LOCAL_PATH}/static')
    MEDIA_ROOT = Directory('{LOCAL_PATH}/media')
    FILE_UPLOAD_TEMP_DIR = Directory('{LOCAL_PATH}/tmp')

If you run the `check` command, you will be warned for missing directories, and the `collectstatic` and `migrate` commands
will attempt to create them.
Of course, you still have `settings.MEDIA_ROOT == '/var/myproject/media'` in your code, when settings are loaded.


You can use more complex things, instead of having:

.. code-block:: python

    SERVER_BASE_URL = 'http://www.example.com'
    SERVER_NAME = 'www.example.com'
    USE_SSL = False
    ALLOWED_HOSTS = ['www.example.com']
    CSRF_COOKIE_DOMAIN = 'www.example.com'
    EMAIL_SUBJECT_PREFIX = '[www.example.com]'

You could just have:

.. code-block:: python

    from djangofloor.conf.config_values import CallableSetting
    SERVER_BASE_URL = 'http://www.example.com'
    SERVER_NAME = CallableSetting(lambda x: urlparse(x['SERVER_BASE_URL']).hostname, 'SERVER_BASE_URL')
    USE_SSL = CallableSetting(lambda x: urlparse(x['SERVER_BASE_URL']).scheme == 'https', 'SERVER_BASE_URL')
    ALLOWED_HOSTS = CallableSetting(lambda x: [urlparse(x['SERVER_BASE_URL']).hostname], 'SERVER_BASE_URL')
    CSRF_COOKIE_DOMAIN = CallableSetting(lambda x: urlparse(x['SERVER_BASE_URL']).hostname, 'SERVER_BASE_URL')
    EMAIL_SUBJECT_PREFIX = CallableSetting(lambda x: '[%s]' % urlparse(x['SERVER_BASE_URL']).hostname, 'SERVER_BASE_URL')


Default settings
----------------

Please take a look at :mod:`djangofloor.conf.defaults` for all default settings.

Displaying settings
-------------------

The complete list of used config files can be displayed using the following command:

.. code-block:: bash

  yourproject-ctl config python | less (or python yourproject-django.py config python -v 2)
  # --------------------------------------------------------------------------------
  # Djangofloor version 1.0.22
  # Configuration providers:
  # --------------------------------------------------------------------------------
  ...
  DF_TEMPLATE_CONTEXT_PROCESSORS = ['updoc.context_processors.most_checked']

You can use the `-v 2` flag for a more verbose output:

.. code-block:: bash

  yourproject-ctl config python -v 2 | less (or python yourproject-django.py config python -v 2)
  # --------------------------------------------------------------------------------
  # Djangofloor version 1.0.4
  # Configuration providers:
  #  - Python module "djangofloor.conf.defaults"
  #  - Python module "yourproject.defaults"
  #  - .ini file "/home/user/.virtualenvs/yourproject/etc/yourproject/settings.ini"
  #  - Python file "/home/user/.virtualenvs/yourproject/etc/yourproject/settings.py"
  #  - .ini file "/home/user/.virtualenvs/yourproject/etc/yourproject/django.ini"
  #  - Python file "/home/user/.virtualenvs/yourproject/etc/yourproject/django.py"
  #  - .ini file "./local_settings.ini"
  #  - Python file "./local_settings.py"
  # --------------------------------------------------------------------------------
  ...
  DF_TEMPLATE_CONTEXT_PROCESSORS = ['updoc.context_processors.most_checked']
  #   djangofloor.conf.defaults -> []
  #   updoc.defaults -> ['updoc.context_processors.most_checked']


You can also display the corresponding .ini files:

.. code-block:: bash

  yourproject-ctl config ini -v 2 | less
  #  - .ini file "/home/usr/.virtualenvs/easydjango35/etc/easydemo/settings.ini"
  #  - .ini file "/home/usr/.virtualenvs/easydjango35/etc/easydemo/django.ini"
  #  - .ini file "/home/usr/Developer/Github/EasyDjango/EasyDemo/local_settings.ini"
  [global]
  admin_email = admin@localhost
	# e-mail address for receiving logged errors
  data = django_data
	# where all data will be stored (static/uploaded/temporary files, …) If you change it, you must run the collectstatic and migrate commands again.
  language_code = fr_FR
	# default to fr_FR
  listen_address = localhost:9000
	# address used by your web server.
  secret_key = *secret_key*
  server_url = http://localhost:9000/
	# Public URL of your website.
	# Default to "http://listen_address" but should be ifferent if you use a reverse proxy like Apache or Nginx. Example: http://www.example.org.
  time_zone = Europe/Paris
	# default to Europe/Paris
  log_remote_url =
	# Send logs to a syslog or systemd log daemon.
	# Examples: syslog+tcp://localhost:514/user, syslog:///local7, syslog:///dev/log/daemon, logd:///project_name
  ...

