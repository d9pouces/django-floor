Documentation
-------------

  * packaging
  * vagrant
  * docker
  * error pages


Authentication sources
----------------------

  * LDAP (OK but SASL)
  * SMTP
  * two-factor https://github.com/percipient/django-allauth-2fa
  * radius (OK)
  * PAM (OK)
  * check doc
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
