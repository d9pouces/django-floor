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

DjangoFloor offers a simple utility based on `stdeb` to package your complete application. First of all, you should look at the original `documentation <https://pypi.python.org/pypi/stdeb>`_. However, this utility requires to be run on a Debian-based system, with `dh-make`.

.. code-block:: bash

    cd myproject
    workon myproject
    pip install djangofloor[deb]
    # download and package dependencies to .deb files
    mkdir -p dependencies/deb
    cd dependencies
    for line in `pip freeze|grep '=='`; do
        name=`echo $line | cut -d '=' -f 1`
        version=`echo $line | cut -d '=' -f 3`
        pypi-download --release=$version $name
    done
    for archive in *tar.gz; do
        rm -rf deb_dist
        py2dsc-deb $archive
        mv deb_dist/*.deb deb
    done
    # ok, we can go on to build our package
    python setup.py bdist_deb2

This command requires a configuration file, called `stdeb.cfg`. In addition to the options used by the original `bdist_stdeb` command, you can add this

.. code-block:: ini

    [djangofloor]
    processes = demo-gunicorn:/usr/bin/demo-gunicorn
        demo-celery:/usr/bin/demo-celery worker
    frontend = nginx
    process_manager = supervisor
    username = demo

There are basically four available options:

    * `processes`: a list of process to run (like the gunicorn process),
    * `frontend`: the frontend server (currently `apache` or `nginx`),
    * `process_manager`: the process manager (currently `supervisor` or `systemd`),
    * `username`: the username used for the process.

RedHat / CentOS / Scientific Linux
----------------------------------

TODO