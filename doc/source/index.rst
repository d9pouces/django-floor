DjangoFloor
===========

Introduction
------------

DjangoFloor is an thin overlay of the Django Python web framework for quickly building websites that are ready to deploy.
Its main features are:

  * easy to develop: a single command line generates a fully-working base project (with complete templates), that you can modify step-by-step, with dedicated development settings,
  * easy to deploy: ready to be packaged with separated simple config (.ini) files, without requiring to maintain duplicated config files (prod and dev),
  * allowing offline computation (computation in separated processes or dedicated machines) and two-way communication between the server and the JavaScript world via websockets.
  * with a complete deployment documentation.

Of course, any thing provided by DjangoFloor can be overriden (like the default templates that are based on the well-known Bootstrap 3).

Requirements
------------

DjangoFloor has a bit more requirements than Django:

  * Python 3.4+ (however Django 2.0 also requires Python 3.4+),
  * Django 1.11+,
  * Gunicorn as application server,
  * Redis for caching, sessions, websocket management and celery broker,
  * a reverse proxy like nginx or apache.

DjangoFloor in a nutshell
-------------------------

I assume that you already have a new virtual environment.

.. code-block:: bash

  pip install djangofloor
  djangofloor-createproject
  | Your new project name [MyProject]
  | Python package name [myproject]
  | Initial version [0.1]
  | Root project path [.] test
  | Use background tasks or websockets [n]
  cd test
  python setup.py develop
  myproject-ctl collectstatic --noinput
  myproject-ctl migrate
  myproject-ctl check
  myproject-ctl runserver

And open your browser on http://localhost:9000/ :)

You can easily create an admin user (password: "admin") and a standard user (password: "user"):

.. code-block:: bash

  cat << EOF | myproject-ctl shell
  from django.contrib.auth.models import User
  if User.objects.filter(username='admin').count() == 0:
      u = User(username='admin')
      u.is_superuser = True
      u.is_staff = True
      u.set_password('admin')
      u.save()
  if User.objects.filter(username='user').count() == 0:
      u = User(username='user')
      u.set_password('user')
      u.save()
  EOF

Overview
========

.. toctree::
   :maxdepth: 3

   installation
   newproject
   settings
   provided-settings
   signals
   remote-functions
   monitoring
   notification
   authentication
   features
   common_errors
   javascript
   whatsnext
   api/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
