#!/usr/bin/env bash
IS_INSTALLED=`dpkg -l | grep "{{ DF_MODULE_NAME }}"`
if [ -z "${IS_INSTALLED}" ]; then
    sudo rm -rf "{{ install_dir.1 }}"
fi
{% if dependencies %}
sudo apt-get install -y {{ dependencies|join:" " }}
{% endif %}
sudo dpkg -i "{{ tmp_dir.1 }}/{{ package_filename }}"
sudo -H -u "{{ DF_MODULE_NAME }}" "{{ processes.django.command_line }}" migrate
cat << EOF | sudo tee "{{ install_dir.1 }}/etc/{{ DF_MODULE_NAME }}/settings.ini"
[global]
listen_address = 0.0.0.0:{{ SERVER_PORT }}
server_url = http://localhost:10080/
EOF
sudo apt-get install -y redis-server
cat << EOF | sudo -H -u "{{ DF_MODULE_NAME }}" "{{ processes.django.command_line }}" shell
from django.contrib.auth.models import User
if User.objects.filter(username='admin').count() == 0:
    u = User(username='admin')
    u.is_superuser = True
    u.is_staff = True
    u.set_password('admin')
    u.save()
if User.objects.filter(username='user').count() == 0:
    u = User(username='user')
    u.set_password('user')
    u.save()
EOF
{% if processes.celery %}{% for queue in expected_celery_queues %}sudo -H -u "{{ DF_MODULE_NAME }}" "{{ processes.celery.command_line }}" worker -Q "{{ queue }}"  -n '%h-{{ queue }}' &
{% endfor %}
{% endif %}
echo "a standard user named “user” has been created (with password “user”)"
echo "an admin user named “admin” has been created (with password “admin”)"
echo "You can stop the web process with <Ctrl>-<C>"
{% if processes.aiohttp %}sudo -H -u "{{ DF_MODULE_NAME }}" "{{ processes.aiohttp.command_line }}"
{% elif processes.gunicorn %}sudo -H -u "{{ DF_MODULE_NAME }}" "{{ processes.gunicorn.command_line }}"
{% endif %}
{% if expected_celery_queues %}echo "To stop all Celery workers, you can use the following command"
echo 'sudo kill `ps aux   | grep "^{{ DF_MODULE_NAME }}"  | awk "{print \$2}"`'
{% endif %}
