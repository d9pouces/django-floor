Creating a new project
======================

Expected archicture
-------------------

By default, DjangoFloor assumes several architectural choices:

  * your gunicorn server is behind a reverse proxy (nginx or apache),
  * offline computation and websockets messages (if present) are processed by Celery queues,
  * Redis is used as Celery broker, session store and cache database.

Preparing the environment
-------------------------

* install redis (optional if you do not use offline computations nor websockets)

* create a virtualenv dedicated to your project

.. code-block:: bash

  pip install virtualenv
  cd myproject
  virtualenv venv -p `which python3.5`  # also works with any Python 3.4+
  source venv/bin/activate

* install DjangoFloor:

.. code-block:: bash

  pip install djangofloor

* create the base of your project

.. code-block:: bash

  djangofloor-createproject
  | Your new project name [MyProject]
  | Python package name [myproject]
  | Initial version [0.1]
  | Root project path [.] .

* install scripts in your path. The default `setup.py` installs a single script (`myproject-ctl`) that allows you to
access to all Django or Celery commands or launch the aiohttp server.


.. code-block:: bash

  python setup.py develop

* prepare the database and collect static files

.. code-block:: bash

  myproject-ctl collectstatic --noinput
  myproject-ctl migrate

* Now, you just have to run the following two processes (so you need two terminal windows):

.. code-block:: bash

  myproject-ctl runserver  # the dev. server provided by Django, you should use only `server` in production
  myproject-ctl worker


Project structure
-----------------

The structure of this project closely follows the Django standard one.
DjangoFloor only provides default code or values for some parts, so you do not have to write them (but you can override them if you want):

  * instead of writing a complete `myproject.settings` module, you only have to override some values in a `myproject.defaults` module,
  * a valid `ROOT_URLCONF` is provided (with admin views as well as static and media files), you can only add some views in a list in `myproject.url.urlpatterns`,
  * a default template and a default index view, based on Bootstrap 3,
  * a minimal mapping for some settings in a configuration file,
  * multiple WSGI apps (for Gunicorn and aiohttp) are also provided.

Deploying your project
----------------------

If your project is uploaded to Pypi:


.. code-block:: bash

  pip install myproject --upgrade

Of course, you can deploy it in a virtualenv.
The configuration of your deployment should be in .ini-like files. The list of configuration files, as well as default values, are shown with the following command line:

.. code-block:: bash

  myproject-ctl config ini -v 2

After the configuration, you can migrate the database and deploy the static files (CSS or JS):

.. code-block:: bash

  myproject-ctl collectstatic --noinput
  myproject-ctl migrate

Running the servers (in two different processes):

.. code-block:: bash

  myproject-ctl runserver  # for dev
  myproject-ctl server  # for prod
  myproject-ctl worker  # for the Celery worker that process offline computation and websocket messages

Development commands
--------------------

Django already uses a `DEBUG` variable; DjangoFloor adds a boolean `DEVELOPMENT` variable that allows to hide commands
from the command line. The goal is to hide from the final user commands that are not required in production.

Development files
-----------------

DjangoFloor can create a Sphinx documentation for your project:

  * configuration file for generating the doc source,

.. code-block:: bash

  myproject-ctl gen_dev_files . -v 2  --dry

(remove the `--dry` argument for actually writing files)
You can now install sphinx and generate the doc:

.. code-block:: bash

  pip install sphinx  # some extra packages may be required
  cd doc
  make html
  cd ..

How files are generated?
~~~~~~~~~~~~~~~~~~~~~~~~

The `gen_dev_files` command looks for files in some directories.
It use
By default, it searches in `"djangofloor:djangofloor/dev"` and `"myproject:myproject/dev"`.
It means that it looks for files in:

  * `[installation_path_of_djangofloor]/djangofloor/static/djangofloor/dev`,
  * `[installation_path_of_djangofloor]/djangofloor/templates/djangofloor/dev`,
  * `[installation_path_of_myproject]/myproject/static/myproject/dev`,
  * `[installation_path_of_myproject]/myproject/templates/myproject/dev`.

When files have the same relative path, the last one override the previous ones.

If an original filename ends with `"_inc"`, then this file will be ignored.
If an original filename ends with `"_tpl"`, then this suffix is silently stripped for building the destination filename.
This allows to avoid template files with the `".py"` suffix (that can lead to some problems with scripts that import all Python files in a folder).

For example, if we have:

.. code-block:: bash

  $ ls -lR [installation_path_of_djangofloor]/djangofloor/static/djangofloor/dev
  subfolder/test1.txt
  subfolder/test2.txt
  subfolder/test4.txt_inc
  demo.txt
  $ ls -lR [installation_path_of_djangofloor]/djangofloor/templates/djangofloor/dev
  subfolder/test1.txt
  demo.txt
  $ ls -lR [installation_path_of_myproject]/myproject/static/myproject/dev
  subfolder/test1.txt
  demo.txt
  $ ls -lR [installation_path_of_myproject]/myproject/templates/myproject/dev
  subfolder/test1.txt_tpl
  subfolder/test3.txt
  demo.txt


Then the `gen_dev_files destination/folder` command will write the following files:

.. code-block:: bash

  $ls -lR destination/folder
  destination/folder/subfolder/test1.txt
  destination/folder/subfolder/test2.txt
  destination/folder/subfolder/test3.txt
  destination/folder/demo.txt


If the original file is found in a `static` folder, then it is copied as-is.
If it is found in a `templates` folder, then it is templated before being written.

Template values are:

  * all Django settings,
  * "year": the current year,
  * "python_version": current Python version,
  * "use_python3": `True` or `False`,
  * "settings_merger": the current :class:`djangofloor.conf.merger.SettingMerger`,
  * "settings_ini" : a .ini representation of the settings.

If the final file is empty, then it is not written.

Due to the search pattern, you can create your own templates that extends DjangoFloor ones.

Using PyCharm
-------------

PyCharm Pro can handle Django projects. However, it requires a complete settings file to work.
DjangoFloor can luckily generate the required file:

.. code-block:: bash

  myproject-ctl config python > pycharm_settings.py

Since this file is easily created, you do not have to commit this file to your version control system.
