What's next?
============

Here is a short list of external tools you could use.

Versionning
-----------

I like `Github <https://github.com>`_ but of course you can use any other repository like `Gitlab <https://gitlab.com>`_.

.. code-block:: bash

  cd myproject
  git remote add git@github.com:myself/myproject.git
  git add .
  git commit -m 'initial commit'
  git push origin


Python packages
---------------

If your project is free or open-source, you really should consider to upload it on `Pypi <https://pypi.python.org>`_.
You first have to create a config file for Pypi and register your project:

.. code-block:: bash

  cat << EOF > ~/.pypirc
  [pypi]
  username=myself
  password=mypassword
  EOF
  cd myproject
  python setup.py register

When you are ready to upload your project:

.. code-block:: bash

  cd myproject
  python setup.py sdist upload


deb/rpm packages
----------------

There are several ways to distribute your application, like:

  * source Python files,
  * Docker files,
  * standard packages for your distribution (e.g. .deb files for Ubuntu and Debian).
    To avoid the packaging of all your dependencies (and conflicts with packages proposed by the distribution), only
    the Python 3 of your distribution is used: a virtualenv is created in /opt and packaged as-is.
    All dependencies are installed inside this virtualenv.

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

You can use sites like `PackageCloud <https://packagecloud.io>`_ to host your public packages.


documentation
--------------

A complete documentation can be generated and customized to perfectly fit your needs.
You should consider using `ReadTheDocs <https://readthedocs.org>`_, like most of modern Python packages, for hosting your doc.
