Installation
============

As every Python package, you may use several ways to install {{ FLOOR_PROJECT_NAME }}.
The following packages are required:
{% block dependencies %}{% block pre_dependencies %}{% endblock %}
  * setuptools >= 3.0
  * djangofloor >= 0.17.0{% block post_dependencies %}{% endblock %}
{% endblock %}
Installing or Upgrading
-----------------------

Here is a simple tutorial to install {{ FLOOR_PROJECT_NAME }} on a basic Debian/Linux installation.
You should easily adapt it on a different Linux or Unix flavor.

{% block pre_install_step %}{% endblock %}

{% block database %}Database
--------

PostgreSQL is often a good choice for Django sites:

.. code-block:: bash

{% block pre_database %}{% endblock %}   sudo apt-get install postgresql
   echo "CREATE USER {{ PROJECT_NAME }}" | sudo -u postgres psql -d postgres
   echo "ALTER USER {{ PROJECT_NAME }} WITH ENCRYPTED PASSWORD '5trongp4ssw0rd'" | sudo -u postgres psql -d postgres
   echo "ALTER ROLE {{ PROJECT_NAME }} CREATEDB" | sudo -u postgres psql -d postgres
   echo "CREATE DATABASE {{ PROJECT_NAME }} OWNER {{ PROJECT_NAME }}" | sudo -u postgres psql -d postgres
{% block post_database %}{% endblock %}
{% endblock %}

{% block webserver %}
Apache
------

I only present the installation with Apache, but an installation behind nginx should be similar.
You cannot use different server names for browsing your mirror. If you use `{{ PROJECT_NAME }}.example.org`
in the configuration, you cannot use its IP address to access the website.

.. code-block:: bash

    sudo apt-get install apache2 libapache2-mod-xsendfile
    sudo a2enmod headers proxy proxy_http
    sudo a2dissite 000-default.conf
    # sudo a2dissite 000-default on Debian7
    SERVICE_NAME={{ PROJECT_NAME }}.example.org
    cat << EOF | sudo tee /etc/apache2/sites-available/{{ PROJECT_NAME }}.conf
    <VirtualHost *:80>
        ServerName $SERVICE_NAME
        Alias /static/ /var/{{ PROJECT_NAME }}/static/
        ProxyPass /static/ !
        Alias /media/ /var/{{ PROJECT_NAME }}/media/
        ProxyPass /media/ !
        ProxyPass / http://{{ BIND_ADDRESS }}/
        ProxyPassReverse / http://{{ BIND_ADDRESS }}/
        DocumentRoot /var/{{ PROJECT_NAME }}/
        ServerSignature off
        XSendFile on
        XSendFilePath /var/{{ PROJECT_NAME }}/storage/
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
{% block extra_apache_conf %}
{% endblock %}
    </VirtualHost>
    EOF
    sudo mkdir /var/{{ PROJECT_NAME }}/
    sudo chown -R www-data:www-data /var/{{ PROJECT_NAME }}/
    sudo a2ensite {{ PROJECT_NAME }}.conf
    sudo apachectl -t
    sudo apachectl restart

{% block ssl_kerberos %}
If you want to use SSL:

.. code-block:: bash

    sudo apt-get install apache2 libapache2-mod-xsendfile
    PEM=/etc/apache2/`hostname -f`.pem
    # ok, I assume that you already have your certificate
    sudo a2enmod headers proxy proxy_http ssl
    openssl x509 -text -noout < $PEM
    sudo chown www-data $PEM
    sudo chmod 0400 $PEM
{% block keytab %}
    sudo apt-get install libapache2-mod-auth-kerb
    KEYTAB=/etc/apache2/http.`hostname -f`.keytab
    # ok, I assume that you already have your keytab
    sudo a2enmod auth_kerb
    cat << EOF | sudo ktutil
    rkt $KEYTAB
    list
    quit
    EOF
    sudo chown www-data $KEYTAB
    sudo chmod 0400 $KEYTAB
{% endblock %}
    SERVICE_NAME={{ PROJECT_NAME }}.example.org
    cat << EOF | sudo tee /etc/apache2/sites-available/{{ PROJECT_NAME }}.conf
    <VirtualHost *:80>
        ServerName $SERVICE_NAME
        RedirectPermanent / https://$SERVICE_NAME/
    </VirtualHost>
    <VirtualHost *:443>
        ServerName $SERVICE_NAME
        SSLCertificateFile $PEM
        SSLEngine on
        Alias /static/ /var/{{ PROJECT_NAME }}/static/
        ProxyPass /static/ !
        Alias /media/ /var/{{ PROJECT_NAME }}/media/
        ProxyPass /media/ !
        ProxyPass / http://{{ BIND_ADDRESS }}/
        ProxyPassReverse / http://{{ BIND_ADDRESS }}/
        DocumentRoot /var/{{ PROJECT_NAME }}/
        ServerSignature off
        RequestHeader set X_FORWARDED_PROTO https
        <Location />
            Options +FollowSymLinks +Indexes
{% block kerberos_auth %}            AuthType Kerberos
            AuthName "{{ FLOOR_PROJECT_NAME }}"
            KrbAuthRealms EXAMPLE.ORG example.org
            Krb5Keytab $KEYTAB
            KrbLocalUserMapping On
            KrbServiceName HTTP
            KrbMethodK5Passwd Off
            KrbMethodNegotiate On
            KrbSaveCredentials On
            Require valid-user
            RequestHeader set REMOTE_USER %{REMOTE_USER}s
{% endblock %}
        </Location>
        <Location /static/>
            Order deny,allow
            Allow from all
            Satisfy any
        </Location>
{% block extra_ssl_apache_conf %}{% endblock %}
        XSendFile on
        XSendFilePath /var/{{ PROJECT_NAME }}/storage/
        # in older versions of XSendFile (<= 0.9), use XSendFileAllowAbove On
    </VirtualHost>
    EOF
    sudo mkdir /var/{{ PROJECT_NAME }}/
    sudo chown -R www-data:www-data /var/{{ PROJECT_NAME }}/
    sudo a2ensite {{ PROJECT_NAME }}.conf
    sudo apachectl -t
    sudo apachectl restart
{% endblock %}
{% endblock %}

{% block application %}Application
-----------

Now, it's time to install {{ FLOOR_PROJECT_NAME }}:

.. code-block:: bash

{% block pre_application %}{% endblock %}    SERVICE_NAME={{ PROJECT_NAME }}.example.org
    sudo mkdir -p /var/{{ PROJECT_NAME }}
    sudo adduser --disabled-password {{ PROJECT_NAME }}
    sudo chown {{ PROJECT_NAME }}:www-data /var/{{ PROJECT_NAME }}
    sudo apt-get install virtualenvwrapper {{ python_version }} {{ python_version }}-dev build-essential postgresql-client libpq-dev
    # application
    sudo -u {{ PROJECT_NAME }} -i
    SERVICE_NAME={{ PROJECT_NAME }}.example.org
    mkvirtualenv {{ PROJECT_NAME }} -p `which {{ python_version }}`
    workon {{ PROJECT_NAME }}
    pip install setuptools --upgrade
    pip install pip --upgrade
    pip install {{ PROJECT_NAME }} psycopg2
    mkdir -p $VIRTUAL_ENV/etc/{{ PROJECT_NAME }}
    cat << EOF > $VIRTUAL_ENV/etc/{{ PROJECT_NAME }}/settings.ini
{% block ini_configuration %}    [global]
    server_name = $SERVICE_NAME
    protocol = http
    ; use https if your Apache uses SSL
    bind_address = {{ BIND_ADDRESS }}
    data_path = /var/{{ PROJECT_NAME }}
    admin_email = admin@$SERVICE_NAME
    time_zone = Europe/Paris
    language_code = fr-fr
    x_send_file =  true
    x_accel_converter = false
    debug = false
{% block ini_configuration_kerberos %}    remote_user_header = HTTP_REMOTE_USER
    ; leave it blank if you do not use kerberos
{% endblock %}{% block extra_ini_configuration %}{% endblock %}    [database]
    engine = django.db.backends.postgresql_psycopg2
    name = {{ PROJECT_NAME }}
    user = {{ PROJECT_NAME }}
    password = 5trongp4ssw0rd
    host = localhost
    port = 5432
{% endblock %}    EOF
    {{ PROJECT_NAME }}-manage migrate
    {{ PROJECT_NAME }}-manage collectstatic --noinput
{% block post_application %}    moneta-manage createsuperuser
{% endblock %}
{% endblock %}

{% block supervisor %}supervisor
----------

Supervisor is required to automatically launch {{ PROJECT_NAME }}:

.. code-block:: bash

    sudo apt-get install supervisor
    cat << EOF | sudo tee /etc/supervisor/conf.d/{{ PROJECT_NAME }}.conf
    [program:{{ PROJECT_NAME }}_gunicorn]
    command = /home/{{ PROJECT_NAME }}/.virtualenvs/{{ PROJECT_NAME }}/bin/{{ PROJECT_NAME }}-gunicorn
    user = {{ PROJECT_NAME }}
{% if USE_CELERY %}    [program:{{ PROJECT_NAME }}_celery]
    command = /home/{{ PROJECT_NAME }}/.virtualenvs/{{ PROJECT_NAME }}/bin/{{ PROJECT_NAME }}-celery worker
    user = {{ PROJECT_NAME }}
{% endif %}    EOF
    sudo /etc/init.d/supervisor restart

Now, Supervisor should start {{ PROJECT_NAME }} after a reboot.
{% endblock %}

{% block systemd %}systemd
-------

You can also use systemd to launch {{ PROJECT_NAME }}:

.. code-block:: bash

    cat << EOF | sudo tee /etc/systemd/system/{{ PROJECT_NAME }}-gunicorn.service
    [Unit]
    Description={{ FLOOR_PROJECT_NAME }} Gunicorn process
    After=network.target
    [Service]
    User={{ PROJECT_NAME }}
    Group={{ PROJECT_NAME }}
    WorkingDirectory=/var/{{ PROJECT_NAME }}/
    ExecStart=/home/{{ PROJECT_NAME }}/.virtualenvs/{{ PROJECT_NAME }}/bin/{{ PROJECT_NAME }}-gunicorn
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s TERM $MAINPID
    [Install]
    WantedBy=multi-user.target
    EOF
    systemctl enable {{ PROJECT_NAME }}-gunicorn.service
{% if USE_CELERY %}    cat << EOF | sudo tee /etc/systemd/system/{{ PROJECT_NAME }}-celery.service
    [Unit]
    Description={{ FLOOR_PROJECT_NAME }} Celery process
    After=network.target
    [Service]
    User={{ PROJECT_NAME }}
    Group={{ PROJECT_NAME }}
    WorkingDirectory=/var/{{ PROJECT_NAME }}/
    ExecStart=/home/{{ PROJECT_NAME }}/.virtualenvs/{{ PROJECT_NAME }}/bin/{{ PROJECT_NAME }}-celery worker
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s TERM $MAINPID
    [Install]
    WantedBy=multi-user.target
    EOF
    systemctl enable {{ PROJECT_NAME }}-celery.service
{% endif %}
{% endblock %}
{% block post_install_step %}{% endblock %}
