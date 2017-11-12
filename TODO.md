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
  * documentation for developpers
  * documentation for new projects
  * remove Bootstrap 3?
  * check cache system
  * modal without bootstrap
  * PID files in a directory
  * display all logs in a directory

Authentication sources
----------------------

  * LDAP (OK but SASL)
  * SMTP
  * two-factor https://github.com/percipient/django-allauth-2fa
  * radius (OK)
  * PAM (OK)
  * reCAPTCHA

EasyDemo
--------

  * Javascript upload a file
  * dynamic form validation
  * check i18n
