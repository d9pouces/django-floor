Complete configuration
======================

You can look current settings with the following command::

    {{ PROJECT_NAME }}-manage config

Here is the complete list of settings::

{% block ini_configuration %}    [global]
    server_name = {{ PROJECT_NAME }}.example.org
    protocol = https
    bind_address = {{ BIND_ADDRESS }}
    data_path = /var/{{ PROJECT_NAME }}
    admin_email = admin@example.org
    time_zone = Europe/Paris
    language_code = fr-fr
    x_send_file =  true
    x_accel_converter = false
    debug = false
{% block authentication %}    remote_user_header = HTTP_REMOTE_USER
{% endblock %}{% block extra_ini_configuration %}{% endblock %}    [database]
    engine =
    name =
    user =
    password =
    host =
    port =
{% block ini_redis %}{% if USE_CELERY or FLOOR_USE_WS4REDIS %}    [redis]
    host = {{ REDIS_HOST }}
    port = {{ REDIS_PORT }}
    broker_db = {{ BROKER_DB }}
{% endif %}{% endblock %}{% endblock %}

If you need more complex settings, you can override default values (given in `djangofloor.defaults` and
`{{ PROJECT_NAME }}.defaults`) by creating a file named `[prefix]/etc/{{ PROJECT_NAME }}/settings.py`.

Valid engines for your database are:

  - `django.db.backends.sqlite3` (use the `name` option for its filepath)
  - `django.db.backends.postgresql_psycopg2`
  - `django.db.backends.mysql`
  - `django.db.backends.oracle`

Use `x_send_file` with Apache, and `x_accel_converter` with nginx.

Debugging
---------

If something does not work as expected, you can look at logs (in /var/log/supervisor if you use supervisor)
or try to run the server interactively:

.. code-block:: bash

  sudo service supervisor stop
  sudo -u {{ PROJECT_NAME }} -i
  workon {{ PROJECT_NAME }}
  {{ PROJECT_NAME }}-manage runserver
  {{ PROJECT_NAME }}-gunicorn
{% if USE_CELERY %}  {{ PROJECT_NAME }}-celery worker
{% endif %}