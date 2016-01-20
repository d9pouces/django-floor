Packaging your application
==========================

Python
------

The simplest way for packaging is to use built-in Python tools.

.. code-block:: bash

    cd myproject
    workon myproject
    python setup.py sdist

Debian / Ubuntu
---------------

Creating a Debian package for a Djangofloor project, like any other Django project, requires to also package all dependencies.

packaging dependencies
~~~~~~~~~~~~~~~~~~~~~~

You should use `DebTools <https://debtools.readthedocs.org/en/latest/>`_ to create packages for all dependencies in a single command.
Creating all packages is quite simple:

    #. create a virtualenv and install your application (so all your dependencies are also installed),
    #. create a generic `stdeb.cfg` file for all Debian-based distributions,
    #. create a `stdeb-distribution.cfg` specific to each distribution,
    #. in these files, create a section for each Python package requiring specific treatment,
    #. call `multideb -r -v -x stdeb-distribution.cfg`,
    #. wait (it takes almost one hour on a slow computer) while all Python modules are packaged.

In the `demo` application, a generic `stdeb.cfg` file and specific files for Debian 7/8 and Ubuntu 14.04+ are provided.
The following packages require specific treatment to be packaged as .deb files:

    * `djangofloor` (dependencies for Python 3),
    * `anyjson` (needs to delete the `tests` directory before packaging),
    * `requests-oauthlib` (needs to delete the `tests` directory before packaging),
    * `celery`  (needs to delete the `docs` directory before packaging),
    * `pathlib` (needs to change the `MANIFEST.in` file),
    * `msgpack-python` (needs to change the package name and to change the `MANIFEST.in` file),
    * `gunicorn` must be installed in version `18.0` on Debian 7.

If you do not have more dependencies, you can juste reuse the files bundled with the `demo` app. Their names should be explicit enough.


packaging your project
~~~~~~~~~~~~~~~~~~~~~~

Packaging your project cannot be done with the standard `bdist_deb` command, provided by the `stdeb` package:

   * static files must be collected,
   * configuration file must be prepared in `/etc/my_project/settings.ini`,
   * configuration file is required for Apache or Nginx,
   * configuration file is required for Supervisor or Systemd.

Djangofloor provides a new command `bdist_deb_django` that do all these things for you.
It only requires a new section `my_project` in your `stdeb.cfg` file. This section can also be in the files specific to each distribution.
In addition to the options used by the original `bdist_stdeb` command, you can add this

.. code-block:: ini

    [my_project]
    ; a list of processes to run (like the gunicorn process, or the celery worker)
    processes = myproject-gunicorn:/usr/bin/myproject-gunicorn
        myproject-celery:/usr/bin/myproject-celery worker
    ; the frontend server (valid values are currently apache2.2, apache2.4 or nginx)
    frontend = nginx
    ; the process manager (valid values are currently supervisor or systemd)
    process_manager = supervisor
    ; the username used for the process (should be my_project).
    username = myproject
    ; extra post-inst. script, appended to the default one (Python 2 only)
    extra_postinst = path_of_postinstallation_script_for_python2.sh
    ; extra post-inst. script, appended to the default one (Python 3 only)
    extra_postinst3 = path_of_postinstallation_script_for_python.sh
    ; uncommon option
    preinst = path_of_preinstallation_script_for_python2.sh
    ; uncommon option
    preinst3 = path_of_preinstallation_script_for_python3.sh
    ; uncommon option
    postinst = path_of_postinstallation_script_for_python2.sh
    ; uncommon option
    postinst3 = path_of_postinstallation_script_for_python3.sh
    ; uncommon option
    prerm = path_of_preremove_script_for_python2.sh
    ; uncommon option
    prerm3 = path_of_preremove_script_for_python3.sh
    ; uncommon option; override the default postinst script
    postrm = path_of_postremove_script_for_python2.sh
    ; uncommon option; override the default postinst script
    postrm3 = path_of_postremove_script_for_python3.sh


Then you can create your .deb:

.. code-block:: bash

    rm -rf `find * | grep pyc$`
    python setup.py bdist_deb_django -x stdeb-distribution.cfg

Again, you should take a look the files provided with the `demo` application (the same files are used to create .deb packages for the dependencies and for the application).

installing your project
~~~~~~~~~~~~~~~~~~~~~~~

If you cannot use a private mirror, just put all .deb files on your server and run:

.. code-block:: bash

    sudo dpkg -i deb/python3-*.deb  # for a Python3 project
    sudo dpkg -i deb/python-*.deb   # for a Python2 project

You should configurate your project by tweaking `/etc/apache2/sites-available/my_project.conf` and `/etc/my_project/settings.ini`.

.. code-block:: bash

    sudo a2ensite my_project.conf
    sudo a2dissite 000-default
    sudo -u my_project my_project-manage migrate
    sudo service supervisor restart
    sudo service apache2 restart


RedHat / CentOS / Scientific Linux
----------------------------------

TODO