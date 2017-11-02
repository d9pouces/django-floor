Documentation
-------------

  * packaging
  * vagrant
  * docker
  * error pages


Authentication sources
----------------------

  * LDAP (OK; require LDAP username/password/SASL)
  * REMOTE_USER (OK)
  * HTTP basic auth (always / maybe / never)
  * SMTP
  * allauth (OAuth2, OpenId, Persona) (OK — excepting templates)
  * PAM (OK - templates to check)

  * Disable user auto create ?
  * LDAP groups (require LDAP username/password/SASL)
