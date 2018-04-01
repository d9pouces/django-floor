#!/usr/bin/env bash
"{{ install_dir.1 }}/bin/pip3" install django-redis-sessions django-redis psutil psycopg2-binary mysqlclient {% if processes.gunicorn %}gunicorn {% endif %}
