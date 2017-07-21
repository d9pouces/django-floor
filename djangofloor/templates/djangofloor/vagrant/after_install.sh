#!/bin/sh
USER_EXISTS=`getent passwd {{ DF_MODULE_NAME }} || :`
if [ -z "${USER_EXISTS}" ]; then
    useradd "{{ DF_MODULE_NAME }}" -d "/opt/{{ DF_MODULE_NAME }}/var/" -U -r
#    adduser --disabled-password --gecos "" {{ DF_MODULE_NAME }}

fi
chown -R "{{ DF_MODULE_NAME }}": "/opt/{{ DF_MODULE_NAME }}/var/"
# systemctl daemon-reload
