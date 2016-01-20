Complete configuration
======================


Configuration options
---------------------

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

{% block debugging %}
Debugging
---------

If something does not work as expected, you can look at logs (in /var/log/supervisor if you use supervisor)
or try to run the server interactively:

.. code-block:: bash

  sudo service supervisor stop
  sudo -u {{ PROJECT_NAME }} -i
  workon {{ PROJECT_NAME }}
  {{ PROJECT_NAME }}-manage config
  {{ PROJECT_NAME }}-manage runserver
  {{ PROJECT_NAME }}-gunicorn
{% if USE_CELERY %}  {{ PROJECT_NAME }}-celery worker
{% endif %}


{% endblock %}

{% block backup %}
Backup
------

A complete {{ FLOOR_PROJECT_NAME }} installation is made a different kinds of files:

    * the code of your application and its dependencies (you should not have to backup them),
    * static files (as they are provided by the code, you can lost them),
    * configuration files (you can easily recreate it, or you must backup it),
    * database content (you must backup it),
    * user-created files (you must also backup them).

Many backup stragegies exist, and you must choose one that fits your needs. We can only propose general-purpose strategies.

{% block backup_db %}We use logrotate to backup the database, with a new file each day.

.. code-block:: bash

  sudo mkdir -p /var/backups/{{ PROJECT_NAME }}
  sudo chown -r {{ PROJECT_NAME }}: /var/backups/{{ PROJECT_NAME }}
  sudo -u {{ PROJECT_NAME }} -i
  cat << EOF > /home/{{ PROJECT_NAME }}/.virtualenvs/{{ PROJECT_NAME }}/etc/{{ PROJECT_NAME }}/backup_db.conf
  /var/backups/{{ PROJECT_NAME }}/backup_db.sql.gz {
    daily
    rotate 20
    nocompress
    missingok
    create 640 {{ PROJECT_NAME }} {{ PROJECT_NAME }}
    postrotate
    myproject-manage dumpdb | gzip > /var/backups/{{ PROJECT_NAME }}/backup_db.sql.gz
    endscript
  }
  EOF
  touch /var/backups/{{ PROJECT_NAME }}/backup_db.sql.gz
  crontab -e
  MAILTO={{ ADMIN_EMAIL }}
  0 1 * * * /home/{{ PROJECT_NAME }}/.virtualenvs/{{ PROJECT_NAME }}/bin/{{ PROJECT_NAME }}-manage clearsessions
  0 2 * * * logrotate -f /home/{{ PROJECT_NAME }}/.virtualenvs/{{ PROJECT_NAME }}/etc/{{ PROJECT_NAME }}/backup_db.conf
{% endblock %}

{% block backup_media %}Backup of the user-created files can be done with rsync, with a full backup each month:
If you have a lot of files to backup, beware of the available disk place!

.. code-block:: bash

  sudo mkdir -p /var/backups/{{ PROJECT_NAME }}/media
  sudo chown -r {{ PROJECT_NAME }}: /var/backups/{{ PROJECT_NAME }}
  cat << EOF > /home/{{ PROJECT_NAME }}/.virtualenvs/{{ PROJECT_NAME }}/etc/{{ PROJECT_NAME }}/backup_media.conf
  /var/backups/{{ PROJECT_NAME }}/backup_media.tar.gz {
    monthly
    rotate 6
    nocompress
    missingok
    create 640 {{ PROJECT_NAME }} {{ PROJECT_NAME }}
    postrotate
    tar -czf /var/backups/{{ PROJECT_NAME }}/backup_media.tar.gz /var/backups/{{ PROJECT_NAME }}/media/
    endscript
  }
  EOF
  touch /var/backups/{{ PROJECT_NAME }}/backup_media.tar.gz
  crontab -e
  MAILTO={{ ADMIN_EMAIL }}
  0 3 * * * rsync -arltDE {{ MEDIA_ROOT }}/ /var/backups/{{ PROJECT_NAME }}/media/
  0 5 0 * * logrotate -f /home/{{ PROJECT_NAME }}/.virtualenvs/{{ PROJECT_NAME }}/etc/{{ PROJECT_NAME }}/backup_media.conf
{% endblock %}
{% endblock %}

Monitoring
----------

You can use Nagios checks to monitor several points:

  * connection to the application server (gunicorn or uwsgi),
  * connection to the database servers (PostgreSQL{% if USE_CELERY %} and Redis{% endif %}),
  * connection to the reverse-proxy server (apache or nginx),
  * time of the last backup (database and files),
  * the validity of the SSL certificate,
  * living processes for gunicorn{% if USE_CELERY %}, celery, redis{% endif %}, postgresql, apache,
  * standard checks for RAM, disk, swap…

LDAP groups
-----------

There are two possibilities to use LDAP groups, with their own pros and cons:

  * on each request, use an extra LDAP connection to retrieve groups instead of looking in the SQL database,
  * regularly synchronize groups between the LDAP server and the SQL servers.

The second approach can be used without any modification in your code and remove a point of failure
in the global architecture (if you allow some delay during the synchronization process).
A tool exists for such synchronization: `MultiSync <https://github.com/d9pouces/Multisync>`_.

LDAP authentication
-------------------

