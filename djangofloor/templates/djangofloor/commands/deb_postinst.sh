#!/bin/sh
set -e
{% if python_version == 2 %}if which pycompile >/dev/null 2>&1; then
    pycompile -p python-demo
fi
{% endif %}{% if python_version == 3 %}
if which py3compile >/dev/null 2>&1; then
    py3compile -p python3-demo
fi
{% endif %}

useradd {{ project_name }} -b /var/ -U -r

chown -R {{ project_name }}: /var/{{ project_name }}
mkdir /var/{{ project_name }}/media
mkdir /var/{{ project_name }}/data
mkdir /var/log/{{ project_name }}
chown {{ project_name }}: /var/log/{{ project_name }}

{% if use_sqlite %}{{ project_name }}-manage migrate
{% endif %}
