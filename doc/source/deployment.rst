Deployment
==========

Deploying Django is merely complex if we follow the `official guide <https://docs.djangoproject.com/en/1.8/howto/deployment/>`_ .
In this small guide, we only support the wsgi.
WSGI can be used with two application servers: gunicorn and uwsgi, behind a pure webserver: nginx or apache.

Do not forget to read the `official doc <https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/>`_!

I will only cover the deployment with wsgi through gunicorn (installed as a dependency) or uwsgi (optional).
Gunicorn is a pure-Python application, but on the other hand uwsgi is maybe more efficient and allows websockets.

settings due to the reverse proxy:

  * ALLOWED_HOSTS = ('IP of the reverse proxy', 'its DNS name', )
  * REVERSE_PROXY_IPS = ('IP of the reverse proxy', )
  * USE_X_SEND_FILE = True if you use Apache, X_ACCEL_REDIRECT if you use nginx
  * USE_X_FORWARDED_HOST = True
  * SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

settings for SSL/HTTPS:

  * SECURE_SSL_REDIRECT = True
  * SESSION_COOKIE_SECURE = True
  * CSRF_COOKIE_SECURE = True
  * CSRF_COOKIE_HTTPONLY = True

You can also check `cipherli <https://cipherli.st>`_ for good configurations.

settings for HTTP authentication (Kerberos/Shibboleth/SSO/…)

  * FLOOR_AUTHENTICATION_HEADER = 'HTTP_REMOTE_USER'

settings for Redis:

  * REDIS_HOST = 'localhost'
  * REDIS_PORT = '6379'

application
-----------

The first thing to do is to create a virtualenv and install your project inside.
If your project is uploaded to pypi or to an internal mirror:

.. code-block:: bash

    mkvirtualenv myproject_prod
    pip install myproject_prod

Otherwise, you should copy the source (or git clone the project):

.. code-block:: bash

    mkvirtualenv myproject_prod
    cd myproject/
    python setup.py install

Then you can configure it:

.. code-block:: bash

    myproject-manage config
    # look on the first lines to check the location of the Python local config file
    # create this file and set the right settings (database, LOCAL_PATH, …)
    myproject-manage migrate
    # create the database and the tables
    myproject-manage collectstatic --noinput
    # generate all static files
    myproject-manage createsuperuser
    # create a first user with admin rights

backup
------

A basic DjangoFloor application a different kinds of files:

    * the code of your application and its dependencies (you should not have to backup them),
    * static files (as they are provided by the code, you can lost them),
    * configuration files (you can easily recreate it, or you must backup it),
    * database content (you must backup it),
    * media files (you also must backup them).

database backup
###############

DjangoFloor comes with a command to dump the database. You can combine it with the `logrotate` utility.

.. code-block:: bash

    cat << EOF > [prefix]/etc/myproject/dbrotate.conf
    /backupdirectory/dbbackup.sql.gz {
        rotate 5
        nocompress
        dateext
        dateformat _%Y-%m-%d
        extension .sql.gz
        missingok
    }
    EOF
    mkdir -p [prefix]/var/myproject/

    myproject-manage dumpdb | gzip > /backupdirectory/dbbackup.sql.gz && logrotate -s [prefix]/var/myproject/dbrotate.state [prefix]/etc/myproject/dbrotate.conf

The last command should be in crontab to be regularly launched.

media files backup
##################

Media files can be backuped with two distinct strategies:

    * generate a single tar.gz archive (takes a lot of disk space),
    * synchronize the folder with another one (say, on a NFS) with `rsync`.

A good strategy is to run the rsync command daily with a monthly tar.gz archive:

.. code-block:: bash

    cat << EOF > [prefix]/etc/myproject/mediarotate.conf
    /backupdirectory/mediabackup.tar.gz {
        rotate 5
        nocompress
        dateext
        dateformat _%Y-%m-%d
        extension .tar.gz
        missingok
    }
    EOF
    mkdir -p [prefix]/var/myproject/
    SRC=`python manage.py config -m | grep MEDIA_ROOT | cut -f 3 -d ' '`

    tar -C $SRC -czf /backupdirectory/mediabackup.tar.gz . && logrotate -s [prefix]/var/myproject/mediarotate.state [prefix]/etc/myproject/mediarotate.conf

    rsync -arltDE $SRC /backupdirectory/media


gunicorn
--------

Gunicorn is an easy-to-use application server:

.. code-block:: bash

    myproject-gunicorn

Or, if you wan to daemonize (but you really should prefer to use systemd/supervisor or launchd):

.. code-block:: bash

    myproject-gunicorn -D

uwsgi
-----

Since uwsgi requires compilation, it is not installed as DjangoFloor dependency, but it can be installed with pip:

.. code-block:: bash

    pip install uwsgi

And then run:

.. code-block:: bash

    myproject-uwsgi

Apache
------

Here is a simple configuration file for your project behind Apache, assuming that LOCAL_PATH is set to "/var/www/myproject" in your settings:

.. code-block:: bash

    <VirtualHost *:80>
        ServerName my.project.com
        Alias               /static/    /var/www/myproject/static/
        Alias               /media/     /var/www/myproject/media/
        ProxyPass           /static/    !
        ProxyPass           /media/     !
        ProxyPass           /           http://localhost:9000/
        ProxyPassReverse    /           http://localhost:9000/
        DocumentRoot        /var/www/myproject/static/
        ServerSignature     off
    </VirtualHost>

Nginx
-----

Here is a simple configuration file for your project behind Nginx, assuming that LOCAL_PATH is set to "/var/www/myproject" in your settings:

.. code-block:: bash

    server {
        listen       80;
        server_name  my.project.name;
        location /static/ {
            autoindex        on;
            alias            /var/www/myproject/static/;
        }
        location /media/ {
            autoindex        on;
            alias            /var/www/myproject/media/;
        }
        location / {
            proxy_pass       http://localhost:9091;
            proxy_set_header Host               $host:$proxy_port;
            proxy_set_header X-Real-IP          $remote_addr;
            proxy_set_header X-Forwarded-Host   $host:$proxy_port;
            proxy_set_header X-Forwarded-Server $host;
            proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
        }
    }


supervisor
----------

A single config file for Supervisor can handle all processes to launch:

.. code-block:: bash

    PROJECT_NAME=myproject
    VIRTUAL_ENV=$VIRTUAL_ENV
    USER=www-data
    cat << EOF | sudo tee /etc/supervisor.d/$PROJECT_NAME.conf
    [program:${PROJECT_NAME}_gunicorn]
    command = $VIRTUAL_ENV/bin/$PROJECT_NAME-gunicorn
    user = $USER
    [program:${PROJECT_NAME}_celery]
    command = $VIRTUAL_ENV/bin/$PROJECT_NAME-celery worker
    user = $USER
    EOF

systemd (Linux only)
--------------------

Most distribution are now using systemd for starting services:

.. code-block:: bash

    PROJECT_NAME=myproject
    VIRTUAL_ENV=$VIRTUAL_ENV
    USER=www-data

    cat << EOF | sudo tee /etc/systemd/system/$PROJECT_NAME-gunicorn.service
    [Unit]
    Description=$PROJECT_NAME Gunicorn process
    After=network.target
    [Service]
    User=$USER
    Group=$USER
    WorkingDirectory=$VIRTUAL_ENV
    ExecStart=$VIRTUAL_ENV/bin/$PROJECT_NAME-gunicorn
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s TERM $MAINPID
    [Install]
    WantedBy=multi-user.target
    EOF

    cat << EOF | sudo tee /etc/systemd/system/$PROJECT_NAME-celery.service
    [Unit]
    Description=$PROJECT_NAME Celery worker process
    After=network.target
    [Service]
    User=$USER
    Group=$USER
    WorkingDirectory=$VIRTUAL_ENV
    ExecStart=$VIRTUAL_ENV/bin/$PROJECT_NAME-celery worker
    [Install]
    WantedBy=multi-user.target
    EOF

    sudo systemctl restart $PROJECT_NAME-gunicorn
    sudo systemctl enable $PROJECT_NAME-gunicorn
    sudo systemctl restart $PROJECT_NAME-celery
    sudo systemctl enable $PROJECT_NAME-celery

launchd (Mac OS X only)
-----------------------

We need to create a config file for each process to launch:

.. code-block:: bash

    PROJECT_NAME=myproject
    VIRTUAL_ENV=$VIRTUAL_ENV
    cat << EOF > ~/Library/LaunchAgents/$PROJECT_NAME.gunicorn.plist
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
      <dict>
        <key>KeepAlive</key>
        <true/>
        <key>Label</key>
        <string>$PROJECT_NAME-gunicorn</string>
        <key>ProgramArguments</key>
        <array>
          <string>$VIRTUAL_ENV/bin/$PROJECT_NAME-gunicorn</string>
        </array>
        <key>EnvironmentVariables</key>
        <dict>
        </dict>
        <key>RunAtLoad</key>
        <true/>
        <key>WorkingDirectory</key>
        <string>/usr/local/var</string>
        <key>StandardErrorPath</key>
        <string>/dev/null</string>
        <key>StandardOutPath</key>
        <string>/dev/null</string>
      </dict>
    </plist>
    EOF
    cat << EOF > ~/Library/LaunchAgents/$PROJECT_NAME.celery.plist
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
      <dict>
        <key>KeepAlive</key>
        <true/>
        <key>Label</key>
        <string>$PROJECT_NAME-celery</string>
        <key>ProgramArguments</key>
        <array>
          <string>$VIRTUAL_ENV/bin/$PROJECT_NAME-celery</string>
          <string>worker</string>
        </array>
        <key>EnvironmentVariables</key>
        <dict>
        </dict>
        <key>RunAtLoad</key>
        <true/>
        <key>WorkingDirectory</key>
        <string>/usr/local/var</string>
        <key>StandardErrorPath</key>
        <string>/dev/null</string>
        <key>StandardOutPath</key>
        <string>/dev/null</string>
      </dict>
    </plist>
    EOF


In this case, your project run as the current logged user. Maybe you should use a dedicated user.