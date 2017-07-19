#!/usr/bin/env bash
IS_INSTALLED=`dpkg -l | grep "{{ DF_MODULE_NAME }}"`
if [ -z "${IS_INSTALLED}" ]; then
    sudo rm -rf "{{ install_dir.1 }}"
fi
sudo dpkg -i "{{ tmp_dir.1 }}/{{ DF_MODULE_NAME }}"*.deb
sudo -u "{{ DF_MODULE_NAME }}" "{{ processes.django.command_line }}" migrate
cat << EOF | sudo tee "{{ install_dir.1 }}/etc/{{ DF_MODULE_NAME }}/settings.ini"
[global]
listen_address = 0.0.0.0:{{ SERVER_PORT }}
EOF
sudo apt-get install -y redis-server
{% if processes.aiohttp %}sudo -u "{{ DF_MODULE_NAME }}" "{{ processes.aiohttp.command_line }}" &
{% elif processes.gunicorn %}sudo -u "{{ DF_MODULE_NAME }}" "{{ processes.gunicorn.command_line }}" &
{% endif %}
{% if processes.celery %}{% for queue in expected_celery_queues %}sudo -u "{{ DF_MODULE_NAME }}" "{{ processes.celery.command_line }}" worker -Q "{{ queue }}" &
{% endfor %}
{% endif %}

echo "To stop all commands, you can use the following command"
echo "sudo kill `ps aux  | grep '^{{ DF_MODULE_NAME }} ' | awk '{print $2}'`"
