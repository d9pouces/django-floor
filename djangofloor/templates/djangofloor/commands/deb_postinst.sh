#!/bin/sh
set -e
{% if python_version == 2 %}if which pycompile >/dev/null 2>&1; then
    pycompile -p python-{{ project_name }}
fi
{% endif %}{% if python_version == 3 %}
if which py3compile >/dev/null 2>&1; then
    py3compile -p python3-{{ project_name }}
fi
{% endif %}

USER_EXISTS=`getent passwd {{ project_name }} || :`
if [ -z "${USER_EXISTS}" ]; then
    useradd {{ project_name }} -b /var/ -U -r
fi

mkdir -p /var/{{ project_name }}/media
mkdir -p /var/{{ project_name }}/data
mkdir -p /var/log/{{ project_name }}
chown -R {{ project_name }}: /var/{{ project_name }}
chown -R {{ project_name }}: /etc/{{ debian_project_name }}
chown -R {{ project_name }}: /var/log/{{ project_name }}
{% if frontend == 'apache2.2' or frontend == 'apache2.4' %}a2enmod proxy proxy_http
{% endif %}

{{ extra_postinst|safe }}