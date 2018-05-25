Authentication
==============

There are many, many ways to authenticate users, and many, many Django packages that define authentication methods.

Password authentication
-----------------------

As you know, Django offers a model for users (:class:`django.contrib.auth.models.User`).
Of course, you can use it, but you must define views for creating new accounts, logging in and logging out.
DjangoFloor comes with the required views (and templates looking like the admin site) for using it.
DjangoFloor can also handle basic HTTP authentication (useful for API).

You can also add the package `django-allauth <http://django-allauth.readthedocs.io/en/latest/>`_. Again, DjangoFloor
comes with the required templates (using the admin site css).
HTTP basic authentication is disabled by default, but you can easily activate it:

.. code-block:: python
  :caption: yourproject/defaults.py
  USE_HTTP_BASIC_AUTH = True

Or you can only activate it when you deploy your app:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  allow_basic_auth = true

By default, password authentication only uses the Django user database, but you can disable it (for example if you only use a LDAP authentication):

.. code-block:: python
  :caption: yourproject/defaults.py

  DF_ALLOW_LOCAL_USERS = False

Or in the .ini file:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  local_users = false

You can allow anonymous to create their own account:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  create_users = true

.. code-block:: python
  :caption: yourproject/defaults.py

  DF_ALLOW_USER_CREATION = True


Reverse-proxy authentication
----------------------------

You reverse proxy (Apache or Nginx) can authenticate users for you and put then user name in a HTTP header (often `REMOTE_USER`).
Since the header is set by the reverse proxy and not by the Python server itself, this HTTP header is renamed to `HTTP_REMOTE_USER`. These reverse proxies can handle any authentication methods, like Kerberos, GSSAPI, LDAP, Shibbolet, and so on.
The :class:`djangofloor.middleware.DjangoFloorMiddleware` middleware uses this HTTP header to authenticate users.
The user is automatically created on its first connection (you can even automatically add him to several groups) if `create_user` is `true`.
This method allows GSSAPI/Kerberos authentication. You can also configure the LDAP authentication if you want to retrieve user attributes (or its groups) from the LDAP server.

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  remote_user_header = HTTP-REMOTE-USER
  remote_user_groups = Users,New Users
  create_users = true

OAuth2 authentication
---------------------

The package `django-allauth <http://django-allauth.readthedocs.io/en/latest/>`_ perfectly handles OAuth2 authentication from many providers.
Please check its own documentation.
Of course, it must be installed separately (it is not a dependency of Djangofloor) and at least one provider must be given in `ALLAUTH_PROVIDER_APPS`.


  * `INSTALLED_APPS` will contain the list of all required Django apps ,
  * :mod:`allauth.urls` is inserted in root urls,
  * :class:`allauth.account.auth_backends.AuthenticationBackend` is added to authentication backends.

Of course, templates must be written.
You can define OAuth2 providers in a .ini config file:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  oauth2_providers = github,asana,bitbucket,tumblr

After having added a oauth2 provided, you must the matching social app in the admin view.

PAM authentication
------------------

You can authenticate your user against the local PAM database, just set in the config files and install "django-pam":

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  pam = true

Radius authentication
---------------------

You can also authenticate users by testing their password against a Radius server, if you have installed the "django-radius" package:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  radius_server = 8.8.8.1
  radius_port = 1812
  radius_secret = secret


LDAP authentication
-------------------

Everything is ready to transparently use `django-auth-ldap <https://pythonhosted.org/django-auth-ldap/>`_ to enable LDAP authentication.
There are two modes for LDAP authentication:

    * a LDAP search is performed (to search the user and its groups) with a specific account, then a binding is performed to check the password,
    * a direct bind is performed with the user login/password and the user account is used to search its data.

Here is an example of configuration for the first method:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  ldap_server_url = ldap://ldap.example.com
  ldap_start_tls = false
  ldap_user_search_base = ou=users,dc=example,dc=com
  ldap_bind_dn = cn=admin,ou=users,dc=example,dc=com
  ldap_bind_password = secret
  ldap_filter = (uid=%%(user)s)

and for the second method:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  ldap_server_url = ldap://ldap.example.com
  ldap_start_tls = false
  ldap_direct_bind = uid=%%(user)s,ou=users,dc=example,dc=com

You can also use some advanced features, for example for retrieving some user attributes from the LDAP, or for copying its groups:

.. code-block:: ini
  :caption: /etc/yourproject/settings.ini

  [auth]
  ldap_first_name_attribute = givenName
  ldap_email_attribute = email
  ldap_last_name_attribute = sn
  ldap_is_active_group = cn=active,ou=groups,dc=example,dc=com
  ldap_is_staff_group = cn=staff,ou=groups,dc=example,dc=com
  ldap_is_superuser_group = cn=admin,ou=groups,dc=example,dc=com
  ldap_group_search_base = ou=groups,dc=example,dc=com
  ldap_group_type = posix
  ldap_mirror_groups = true
