Settings system
===============

By default, Django uses a single Python file for all settings.
However, these settings could be organized into three categories:

  * settings that are very common and that can be kept as-is for any project (`USE_TZ = True` or `MEDIA_URL = '/media/'`),
  * settings that are specific to your project but common to all instances of your project (like `INSTALLED_APPS`),
  * settings that are installation-dependent (`DATABASE_PASSWORD`, …)

You usually have to maintain at least two versions of the same file (dev and prod, or one that is versionned and the other one for prod), with the risk of desynchronized files.

On the contrary, DjangoFloor allows to dynamically merge several files to define your settings:

  * :mod:`djangoFloor.conf.defaults` that aims at providing good default values,
  * `yourproject.defaults` for your project-specific settings,
  * `/etc/yourproject/settings.py` for installation-dependent settings.

You can define a list of settings that are read from a traditionnal text configuration file (`.ini format <https://docs.python.org/3/library/configparser.html>`_).
DjangoFloor also searches for `local_settings.py` and `local_settings.ini` setting files in the working directory.

Defining settings
-----------------

  * many settings are *de facto* defined in :mod:`djangofloor.conf.defaults`,
  * default mapping between Python settings and the `.ini` config file is defined in :mod:`djangofloor.conf.mapping`,
  * you should define your project-wide settings in `<project_root>/yourproject/defaults.py` (only define overriden settings),
  * you should define the option that can be defined in a configuration file in `<project_root>/yourproject/iniconf.py`, in a list named `INI_MAPPING`,
  * define development settings (like `DEBUG = True`) should be defined in  `<project_root>/local_settings.py`,

Before defining your own settings, you should take a look to the first two files and the existing variables.

Your `defaults.py` has the same structure than a traditionnal Django `settings.py` file (but with less variables ^^ )
`INI_MAPPING` is a list of :class:`djangofloor.conf.config_values.ConfigValue` (or of its subclasses, some of them defined in the same module).
Several lists are already defined in :mod:`djangofloor.conf.mapping`.


Displaying settings
-------------------

The complete list of used config files can be displayed using the following command:

.. code-block:: bash

  yourproject-django config python -v 2 | less (or python yourproject-django.py config python -v 2)
  # --------------------------------------------------------------------------------
  # Djangofloor version 1.0.0
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

  yourproject-django config ini -v 2 | less
  #  - .ini file "/Users/flanker/.virtualenvs/easydjango35/etc/easydemo/settings.ini"
  #  - .ini file "/Users/flanker/.virtualenvs/easydjango35/etc/easydemo/django.ini"
  #  - .ini file "/Users/flanker/Developer/Github/EasyDjango/EasyDemo/local_settings.ini"
  [global]
  admin_email = admin@localhost
  data = django_data
  language_code = fr-fr
  listen_address = localhost:9000
  secret_key = secret_key
  server_url = http://localhost:9000/
  time_zone = Europe/Paris
  log_remote_url =