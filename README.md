Djangofloor
===========

Djangofloor helps you to quickly create Django applications that are also easy to deploy. To reach these goals, Djangofloor provides:

  * an extension to the base Django's setting, allowing to split your configuration into several files (default values provided by Djangofloor, constants values for your project, deployement parameters, local values for development),
  * an unified signal dispatcher, using bi-directionnal websockets through Celery and Redis. You can call Python and Javascript signals from the Python or the Javascript side,
  * auto-configuration for a few widespread Django apps (Django-Debug-Toolbar, Django-Redis-Sessions, Django-Pipeline) if they are present,
  * a base template using the well-known Bootstrap3 (but of course you can use any other templates),
  * valid default Django settings (like logs),
  * create new Django projects that are working and deployable out-of-the-box (even if you finally replace all default templates and views).

Creating a new project
----------------------

Creating a working new project only requires a couple lines:

    pip install djangofloor
    djangofloor-createproject
      Your new project name [MyProject] NewProject
      Python package name [newproject]
      Initial version [0.1]
      Root project path [.] /tmp/newproject
    cd /tmp/newproject
    python setup.py install
    newproject-ctl migrate
    newproject-ctl runserver

Online documentation
--------------------

[Read The doc](http://django-floor.readthedocs.io/en/latest/)
