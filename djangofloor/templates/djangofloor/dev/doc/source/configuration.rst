Complete configuration
======================

You can look current settings with the following command:

.. code-block:: bash

    {{ PROJECT_NAME }}-manage config

Here is the complete list of settings:

.. code-block:: ini

{% block ini_configuration %}{% for section in settings_merger.all_ini_options.items %}  [{{ section.0 }}]
{% for option_parser in section.1 %}  {{ option_parser.key }} = {{ option_parser.str_value }}
{% if option_parser.help_str %}  # {{ option_parser.help_str|safe }}
{% endif %}{% endfor %}{% endfor %}
{% endblock %}

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