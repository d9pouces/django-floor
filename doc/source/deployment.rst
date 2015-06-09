Deployment
==========

Deploying Django is merely complex if we follow the `official guide <https://docs.djangoproject.com/en/1.8/howto/deployment/>`_ .
In this small guide, we only support the wsgi.
WSGI can be used with two application servers: gunicorn and uwsgi, behind a pure webserver: nginx or apache.

Do not forget to read the `official doc <https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/>`_ !

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

settings for HTTP authentication (Kerberos/Shibboleth/SSO/…)

  * FLOOR_AUTHENTICATION_HEADER = 'HTTP_REMOTE_USER'

settings for Redis:

  * REDIS_HOST = 'localhost'
  * REDIS_PORT = 6379


your application
----------------




gunicorn
--------

Gunicorn is an easy-to-use application server::

    myproject-gunicorn

Or, if you wan to daemonize::

    myproject-gunicorn -D

uwsgi
-----

Since uwsgi requires compilation, it is not installed as DjangoFloor dependency, but it can be installed with pip::

    pip install uwsgi

And then run::

    myproject-uwsgi

Apache
------

Here is a simple configuration file for your project behind Apache, assuming that LOCAL_PATH is set to "/var/www/myproject" in your settings::

    <VirtualHost *:80>
        ServerName my.project.com
        Alias /static/ /var/www/myproject/static/
        Alias /media/ /var/www/myproject/media/
        ProxyPass /static/ !
        ProxyPass /media/ !
        ProxyPass / http://localhost:9000/
        ProxyPassReverse / http://localhost:9000/
        DocumentRoot /var/www/myproject/static/
    </VirtualHost>

Nginx
-----

Here is a simple configuration file for your project behind Nginx, assuming that LOCAL_PATH is set to "/var/www/myproject" in your settings::

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
            proxy_set_header Host       $host:$proxy_port;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-Host $host:$proxy_port;
            proxy_set_header X-Forwarded-Server $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }


supervisor
----------

systemd
-------

