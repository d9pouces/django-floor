Authentication
==============

There are many, many ways to authenticate users, and many, many Django packages that define authentication methods.

Django authentication
---------------------

As you know, Django offers a model for users (:class:`django.contrib.auth.models.User`).
Of course, you can use it, but you must define views for creating new accounts, logging in and logging out.
The package `django-allauth <http://django-allauth.readthedocs.io/en/latest/>`_ can help you for this.


HTTP authentication
-------------------

You reverse proxy (Apache or Nginx) can authenticate users for you and put then user name in a HTTP header (often `REMOTE_USER`).
Since the header is set by the reverse proxy and not by the Python server itself, this HTTP header is renamed to `HTTP_REMOTE_USER`. These reverse proxies can handle any authentication methods, like Kerberos, GSSAPI, LDAP, Shibbolet, and so on.
The :class:`djangofloor.middleware.DjangoFloorMiddleware` middleware uses this HTTP header to authenticate users.
The user is automatically created on its first connection (you can even automatically add him to several groups).

If HTTP authentication should be the default method for every installation of your project:

.. code-block:: python
  :caption: yourproject.defaults.py

  DF_REMOTE_USER_HEADER = 'HTTP-REMOTE-USER'
  DF_DEFAULT_GROUPS = ['Users', 'New Users']

Or you can use when you deploy it:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  remote_user_header = HTTP-REMOTE-USER
  remote_user_groups = Users,New Users

HTTP basic authentication
-------------------------

DjangoFloor can itself handle HTTP authentication, checking username and password against the Django user database.
Of course, user must already exist.


If HTTP authentication should be the default method for every installation of your project:

.. code-block:: python
  :caption: yourproject.defaults.py

  USE_HTTP_BASIC_AUTH = True

Or you can use when you deploy it:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  allow_basic_auth = true

OAuth2 authentication
---------------------

The package `django-allauth <http://django-allauth.readthedocs.io/en/latest/>`_ perfectly handles OAuth2 authentication from many providers.
Please check its own documentation.
Of course, it must be installed separately (it is not a dependency of Djangofloor) and at least one provider must be given in `ALLAUTH_PROVIDERS`.


  * `INSTALLED_APPS` will contain the list of all required Django apps ,
  * :mod:`allauth.urls` is inserted in root urls,
  * :class:`allauth.account.auth_backends.AuthenticationBackend` is added to authentication backends.

Of course, templates must be written.
You can define OAuth2 providers in a .ini config file:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  oauth2_providers = github,asana,bitbucket,tumblr

LDAP authentication
-------------------

Again, `django-auth-ldap <https://pythonhosted.org/django-auth-ldap/>`_ knows how to handle LDAP authentication. Of course, it must be installed separately (it is not a dependency of Djangofloor).
And again, DjangoFloor can help you to use it.
If `AUTH_LDAP_SERVER_URI` is set, then:

  * :class:`django_auth_ldap.backend.LDAPBackend` is added to authentication backends,
  * the setting `AUTH_LDAP_USER_SEARCH` is built from `AUTH_LDAP_USER_SEARCH_BASE` and `AUTH_LDAP_FILTER`.

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  ldap_server_url = ldap://ldap.example.com
  ldap_bind_dn = cn=admin,cn=example,cn=com
  ldap_bind_password=s3cr3t
  ldap_search_base=ou=users,dc=example,dc=com
  ldap_filter=(uid=%(user)s)
  ldap_direct_bind=uid=%(user)s,ou=users,dc=example,dc=com  # not required!
  ldap_start_tls=false
