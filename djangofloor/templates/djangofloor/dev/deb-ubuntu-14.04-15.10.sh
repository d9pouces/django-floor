#!/bin/bash
{% block dependencies %}
# base packages
sudo apt-get update
sudo apt-get upgrade --yes
sudo apt-get install --yes vim dh-make ntp rsync liblzma-dev tree
sudo apt-get install --yes python{% if use_python3 %}3{% endif %}-all-dev virtualenvwrapper python{% if use_python3 %}3{% endif %}-tz python{% if use_python3 %}3{% endif %}-setuptools apache2  libapr1 libaprutil1 libaprutil1-dbd-sqlite3 libaprutil1-ldap python-medusa python-meld3 ssl-cert
{% block extra_dependencies %}{% endblock %}source /etc/bash_completion.d/virtualenvwrapper
{% endblock %}

{% block virtualenv %}
# create the virtual env
mkvirtualenv -p `which python{% if use_python3 %}3{% endif %}` djangofloor{% if use_python3 %}3{% endif %}
workon djangofloor{% if use_python3 %}3{% endif %}
pip install setuptools --upgrade
pip install pip --upgrade
pip install debtools djangofloor
{% block extra_virtualenv %}{% endblock %}python setup.py install
{% endblock %}

{% block packages %}
# generate packages for all dependencies
multideb -r -v -x stdeb-debian-8.cfg

# creating package for {{ PROJECT_NAME }}
rm -rf `find * | grep pyc$`
python setup.py bdist_deb_django -x stdeb-debian-8.cfg
deb-dep-tree deb_dist/*deb
mv deb_dist/*deb deb
{% endblock %}

{% block installation %}
# install all packages
sudo dpkg -i deb/python{% if use_python3 %}3{% endif %}-*.deb

# package configuration
IP=`/sbin/ifconfig | grep -Eo 'inet (addr:|adr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'`
sudo sed -i "s/localhost/$IP/g" /etc/apache2/sites-available/{{ PROJECT_NAME }}.conf
sudo sed -i "s/localhost/$IP/g" /etc/{{ PROJECT_NAME }}/settings.ini
sudo a2ensite {{ PROJECT_NAME }}.conf
sudo a2dissite 000-default.conf
sudo -u {{ PROJECT_NAME }} {{ PROJECT_NAME }}-manage migrate
sudo service supervisor restart
sudo service apache2 restart
{% endblock %}
