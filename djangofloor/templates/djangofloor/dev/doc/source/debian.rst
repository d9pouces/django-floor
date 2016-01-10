Debian Installation
===================

By default, {{ FLOOR_PROJECT_NAME }} is only packaged as a standard Python project, downloadable from `Pypi <https://pypi.python.org>`_.
However, you can create pure Debian packages with `DjangoFloor <http://django-floor.readthedocs.org/en/latest/packaging.html#debian-ubuntu>`_.

The source code provides several Bash scripts:

    * `debian-7-python3.sh`,
    * `debian-8-python3.sh`,
    * `ubuntu-14.04-15.10.sh`.

These scripts are designed to run on basic installation and are split in five steps:

    * update system and install missing packages,
    * create a virtualenv and install all dependencies,
    * package all dependencies,
    * package {{ PROJECT_NAME }},
    * install all packages and {{ PROJECT_NAME }}, prepare a simple configuration to test.

If everything is ok, you can copy all the .deb packages to your private mirror or to the destination server.
The configuration is set in `/etc/{{ PROJECT_NAME }}/settings.ini`.
By default, {{ PROJECT_NAME }} is installed with Apache 2.2 (or 2.4) and Supervisor.
You can switch to Nginx or Systemd by tweaking the right `stdeb-XXX.cfg` file.
