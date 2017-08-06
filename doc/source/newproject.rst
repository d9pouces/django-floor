Creating a new project
======================

Expected archicture
-------------------

By default, DjangoFloor assumes several architectural choices:

  * your application server (aiohttp or gunicorn) is behind a reverse proxy (nginx or apache),
  * offline computation are processed by Celery queues,
  * Redis is used as Celery broker, session store and cache database.

Preparing the environment
-------------------------

* install redis

* create a virtualenv dedicated to your project

.. code-block:: bash

  pip install virtualenv
  cd myproject
  virtualenv venv -p `which python3.5`
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

* install scripts in your path. Several scripts will be installed:

  * myproject-django: access to all Django admin commands,
  * myproject-celery: run any Celery command,
  * myproject-aiohttp: run a webserver with aiohttp.

.. code-block:: bash

  python setup.py develop
  echo "DEBUG = True" > local_settings.py

* prepare the database and collect static files

.. code-block:: bash

  myproject-django collectstatic --noinput
  myproject-django migrate

* Now, you just have to run the following two processes (so you need two terminal windows):

.. code-block:: bash

  myproject-django runserver
  myproject-celery worker




Project structure
-----------------

The structure of this project closely follows the Django standard one.
DjangoFloor only provides default code or values for some parts, so you do not have to write them (but you can override them if you want):

  * instead of writing a complete `myproject.settings` module, you only have to override some values in a `myproject.defaults` module,
  * a valid `ROOT_URLCONF` is provided (with admin views as well as static and media files), you can only add some views in a list in `myproject.url.urlpatterns`,
  * a default template and a default index view, based on Bootstrap 3,
  * a minimal mapping for some settings in a configuration file,
  * multiple WSGI apps (for Gunicorn and aiohttp) are also provided.

Translating strings
-------------------

If you install `starterpyth` in your dev environment, you can prepare `.po` translation files and compile them in two commands:

.. code-block:: bash

  python setup.py makemessages -l fr_FR -D django
  python setup.py compilemessages -l fr_FR -D django


Of course, you must use the right value instead of `fr_FR`.

Testing signals
---------------

The signal framework requires a working Redis and a worker process. However, if you only want to check if a signal
has been called in unitary tests, you can use :class:`djangofloor.tests.SignalQueue`.
Both server-side and client-side signals are kept into memory:

  * :attr:`djangofloor.tests.SignalQueue.ws_signals`,

    * keys are the serialized topics
    * values are lists of tuples `(signal name, arguments as dict)`

  * :attr:`djangofloor.tests.SignalQueue.python_signals`

    * keys are the name of the queue
    * values are lists of `(signal_name, window_info_dict, kwargs=None, from_client=False, serialized_client_topics=None, to_server=False, queue=None)`

      * `signal_name` is … the name of the signal
      * `window_info_dict` is a WindowInfo serialized as a dict,
      * `kwargs` is a dict representing the signal arguments,
      * `from_client` is `True` if this signal has been emitted by a web browser,
      * `serialized_client_topics` is not `None` if this signal must be re-emitted to some client topics,
      * `to_server` is `True` if this signal must be processed server-side,
      * `queue` is the name of the selected Celery queue.

.. code-block:: python

  from djangofloor.tasks import scall, SERVER
  from djangofloor.wsgi.window_info import WindowInfo
  from djangofloor.wsgi.topics import serialize_topic
  from djangofloor.decorators import signal
  # noinspection PyUnusedLocal
  @signal(path='test.signal', queue='demo-queue')
  def test_signal(window_info, value=None):
      print(value)

  wi = WindowInfo()
  with SignalQueue() as fd:
      scall(wi, 'test.signal1', to=[SERVER, 1], value="value1")
      scall(wi, 'test.signal2', to=[SERVER, 1], value="value2")

  # fd.python_signals looks like {'demo-queue': [ ['test.signal1', {…}, {'value': 'value1'}, False, None, True, None], ['test.signal2', {…}, {'value': 'value2'}, False, None, True, None]]}
  # fd.ws_signals looks like {'-int.1': [('test.signal1', {'value': 'value1'}), ('test.signal2', {'value': 'value2'})]}


If you do not want to use :class:`djangofloor.tests.SignalQueue` as a context manager, you can just call `activate` and `deactivate` methods.

Deploying your project
----------------------

If your project is uploaded to Pypi:


.. code-block:: bash

  pip install myproject --upgrade

Of course, you can deploy it in a virtualenv.
The configuration of your deployment should be in .ini-like files. The list of configuration files, as well as default values, are shown with the following command line:

.. code-block:: bash

  myproject-django config ini -v 2

After the configuration, you can migrate the database and deploy the static files (CSS or JS):

.. code-block:: bash

  myproject-django collectstatic --noinput
  myproject-django migrate

Running the servers (in two different processes):

.. code-block:: bash

  myproject-django runserver  # for dev
  myproject-aiohttp  # for prod
  myproject-celery worker

Development files
-----------------

DjangoFloor can create a documentation for your project as well as some extra files:

  * configuration file for generating the doc source,

.. code-block:: bash

  myproject-django gen_dev_files . -v 2  --dry

(remove the `--dry` argument for actually writing files)
You can now install sphinx and generate the doc:

.. code-block:: bash

  pip install sphinx  # some extra style packages may be required
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

If an original filename ends with `"_tpl"`, then this suffix is silently stripped for building the destination filename. This allows to avoid template files with the `".py"` suffix (that can lead to some problems with scripts that import all Python files in a folder).

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


If the original file is found in a `static` folder, then it is copied as-is. If it is found in a `templates` folder, then it is templated before being written.

Template values are:

  * all Django settings,
  * "year": the current year,
  * "python_version": current Python version,
  * "use_python3": `True` or `False`,
  * "settings_merger": the current :class:`djangofloor.conf.merger.SettingMerger`,
  * "settings_ini" : a .ini representation of the settings.

If the final file is empty, then it is not written.

Due to the search pattern, you can create your own templates that extends DjangoFloor ones.


Creating Debian packages
------------------------

There are several ways to distribute your application, like:

  * source Python files,
  * Docker files,
  * standard packages for your distribution (e.g. .deb files for Ubuntu and Debian)

Again, there are two methods for building a .deb package:

  * a small package that only contains your application, with a package dependency for each Python dependency.
  This is the cleanest way, but that requires to package every Python dependency, and you may have many conflicts
  between versions. Of course, this is the selected method for official packages.
  * a big package that contains everything (your application, its Python dependencies, Python itself, and standard
  database servers like Redis and PostgreSQL).

Packages created by DjangoFloor (and its Django command `"packaging`") are between these two methods, since it is a virtualenv (using the Python 3 provided
by your distribution) created in /opt and simply packaged as-is. All dependencies are installed inside this virtualenv.

Here is the description of the whole process:

  * create a Vagrant box using the selected distribution (like `"ubuntu/xenial64"`),
  * install a virtual env inside /opt/myproject,
  * create an archive of your project (with `python3 setup.py sdist` in the current directory),
  * send this archive to the Vagrant box and install it in the virtual env,
  * create required directories, collect static files and create some files (like service files for systemd),
  * finally create the package using the `fpm` command.

You can optionally keep the Vagrant box (it should be destroyed at the end of the command) with `--no-destroy` and install the
newly created package in this box with `--run-package`.
If you use this latter option, open your favorite browser to `http://localhost:10080/` to try your project.
FPM supports many options. You can tweak its behaviour with a config file provided by the `--config` option.
You can display an example of such config file with the `--show-config` (since this option requires to run almost the whole process,
it can takes some time).