#!/bin/sh
{% block header %}{% endblock %}
set -e
{% block create_user %}
USER_EXISTS=`getent passwd {{ DF_MODULE_NAME }} || :`
if [ -z "${USER_EXISTS}" ]; then
    useradd {{ DF_MODULE_NAME }} -b /var/ -U -r
fi
{% endblock %}
{% block create_directories %}
mkdir -p /opt/{{ DF_MODULE_NAME }}/var/media
mkdir -p /opt/{{ DF_MODULE_NAME }}/var/data
mkdir -p /opt/{{ DF_MODULE_NAME }}/var/log
chown -R {{ project_name }}: /opt/{{ DF_MODULE_NAME }}
{% endblock %}
{% if frontend == 'apache2.2' or frontend == 'apache2.4' %}
a2enmod proxy proxy_http mod_headers {% if WEBSOCKET_URL %}mod_proxy_wstunnel {% endif %}{% if USE_SSL %}mod_ssl {% endif %}{% if USE_X_SEND_FILE %}mod_xsendfile {% endif %}
{% endif %}
set +e
{% block footer %}{% endblock %}
