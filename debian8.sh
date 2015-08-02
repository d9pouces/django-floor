#!/bin/bash
IP=`/sbin/ifconfig | grep -Eo 'inet (addr:|adr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'`
sudo apt-get update
sudo apt-get upgrade --yes
sudo apt-get install --yes vim python3-all-dev dh-make ntp rsync virtualenvwrapper liblzma-dev python3-tz python3-setuptools tree apache2 apache2-mpm-worker apache2-utils apache2.2-bin apache2.2-common libapr1 libaprutil1 libaprutil1-dbd-sqlite3 libaprutil1-ldap python-medusa python-meld3 ssl-cert supervisor python3-openid
source /etc/bash_completion.d/virtualenvwrapper
mkvirtualenv -p `which python3.4` djangofloor3
workon djangofloor3
pip install setuptools --upgrade
pip install pip --upgrade
pip install debtools --upgrade
# generate packages for all dependencies
python setup.py install
python setup.py install
echo "" > ~/.virtualenvs/djangofloor3/lib/python3.4/site-packages/setuptools.pth
sed -i 's/raise type(self._exception), self._exception, self._traceback/raise type(self._exception)/g' ~/.virtualenvs/djangofloor3/lib/python3.4/site-packages/futures-3.0.3-py3.4.egg/concurrent/futures/_base.py
cd demo
multideb -r -v -x stdeb-debian8.cfg
cd ..
python setup.py install

# creating package for demo
cd demo
rm -rf `find * | grep pyc$`
python setup.py bdist_deb_django -x stdeb-debian8.cfg
deb-dep-tree deb_dist/*deb
mv deb_dist/*deb deb

# install all packages
sudo dpkg -i deb/python3-*.deb

# package configuration
sudo sed -i "s/localhost/$IP/g" /etc/apache2/sites-available/demo.conf
sudo sed -i "s/localhost/$IP/g" /etc/demo/settings.ini
sudo a2ensite demo.conf
sudo a2dissite 000-default.conf
sudo -u demo demo-manage migrate
sudo service supervisor restart
sudo service apache2 restart
