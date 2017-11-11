Documentation
-------------

  * packaging
  * vagrant
  * docker

TODO
----

  * monitoring:
    * logs => display all files
    * Celery : add the number of waiting tasks by queue
  * in the Django check, add some info checks (=> new methods in monitoring.py)
    * celery queue running
    * number of waiting tasks
    * http process running
    * is the DB valid?
    * is all Redis valid?
    * is DEBUG mode deactivated?
    * activated authentication methods

  * documentation generated for new projects
    (generate project and generate doc)
  * documentation for
  * remove Bootstrap 3?
  * modal and notifications without bootstrap

Authentication sources
----------------------

  * LDAP (OK but SASL)
  * SMTP
  * two-factor https://github.com/percipient/django-allauth-2fa
  * radius (OK)
  * PAM (OK)
