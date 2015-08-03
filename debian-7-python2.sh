#!/bin/bash
IP=`/sbin/ifconfig | grep -Eo 'inet (addr:|adr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'`
sudo apt-get update
sudo apt-get upgrade --yes
sudo apt-get install --yes vim python-all-dev dh-make ntp rsync virtualenvwrapper liblzma-dev python-tz python-setuptools tree apache2 apache2-mpm-worker apache2-utils apache2.2-bin apache2.2-common libapr1 libaprutil1 libaprutil1-dbd-sqlite3 libaprutil1-ldap python-medusa python-meld3 ssl-cert supervisor
source /etc/bash_completion.d/virtualenvwrapper
mkvirtualenv -p `which python2.7` djangofloor2
workon djangofloor2
pip install setuptools --upgrade
pip install pip --upgrade
pip install debtools --upgrade
# generate packages for all dependencies
python setup.py install
python setup.py install
echo "" > ~/.virtualenvs/djangofloor2/lib/python2.7/site-packages/setuptools.pth
pip install gunicorn==18.0
cd demo
multideb -r -v -x stdeb-debian-7.cfg
cd ..
python setup.py install

# creating package for demo
cd demo
rm -rf `find * | grep pyc$`
python setup.py bdist_deb_django -x stdeb-debian-7.cfg
deb-dep-tree deb_dist/*deb
mv deb_dist/*deb deb

# install all packages
sudo dpkg -i deb/python3-*.deb

# package configuration
sudo sed -i "s/localhost/$IP/g" /etc/apache2/sites-available/demo.conf
sudo sed -i "s/localhost/$IP/g" /etc/demo/settings.ini
sudo a2ensite demo.conf
sudo a2dissite 000-default
sudo -u demo demo-manage migrate
sudo service supervisor restart
sudo service apache2 restart
