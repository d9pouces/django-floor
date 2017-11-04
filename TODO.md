Documentation
-------------

  * packaging
  * vagrant
  * docker
  * error pages


Authentication sources
----------------------

  * LDAP (OK but SASL)
  * REMOTE_USER (OK) => check the session duration
  * HTTP basic auth (always / maybe / never)
  * SMTP
  * two-factor
  * allauth (OAuth2, OpenId, Persona) (OK — excepting templates)
  * PAM (OK - templates to check)
  * Disable user auto create ? => ALLOW_USER_CREATION
    => works for allauth?
  * LDAP groups (OK for REMOTE_USER but SASL)
  * check doc
  * check all templates (with and without allauth)
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


Authentication URLs
-------------------

    DJANGOFLOOR
    ^signup/$

    DJANGO
    ^login/$
    ^logout/$
    ^password_change/$
    ^password_change/done/$
    ^password_reset/$
    ^password_reset/done/$
    ^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$
    ^reset/done/$

    DJANGO-ALLAUTH
    ^signup/$
    ^login/$
    ^logout/$
    ^password/change/$
    ^password/set/$
    ^inactive/$
    ^email/$
    ^confirm-email/$
    ^confirm-email/(?P<key>[-:\w]+)/$
    ^password/reset/$
    ^password/reset/done/$
    ^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$
    ^password/reset/key/done/$
