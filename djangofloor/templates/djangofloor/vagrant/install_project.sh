#!/usr/bin/env bash
"{{ install_dir.1 }}/bin/pip3" install setuptools pip --upgrade
"{{ install_dir.1 }}/bin/pip3" install "{{ tmp_dir.1 }}/{{ dist_filename }}"
"{{ install_dir.1 }}/bin/pip3" install django-redis-sessions django-redis psutil psycopg2 mysqlclient
