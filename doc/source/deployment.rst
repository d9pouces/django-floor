Deployment
==========

Deploying Django is merely complex if we follow the official guide: https://docs.djangoproject.com/en/1.8/howto/deployment/ .
In this small guide, we only support the wsgi.
WSGI can be used with two application servers: gunicorn and uwsgi, behind a pure webserver: nginx or apache.



gunicorn
--------

Gunicorn is an easy-to-use application server::

    myproject-gunicorn

Or, if you wan to daemonize::

    myproject-gunicorn -D

uwsgi
-----

apache
------

nginx
-----
