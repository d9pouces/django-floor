#!/bin/bash
sudo apt-get update
sudo apt-get upgrade --yes
sudo apt-get install --yes python3-all-dev dh-make virtualenvwrapper liblzma-dev python3-tz python3-setuptools tree apache2 apache2-mpm-worker apache2-utils apache2.2-bin apache2.2-common libapr1 libaprutil1 libaprutil1-dbd-sqlite3 libaprutil1-ldap python-medusa python-meld3 ssl-cert supervisor
source /etc/bash_completion.d/virtualenvwrapper
mkvirtualenv -p `which python3.2` djangofloor3
workon djangofloor3
pip install setuptools --upgrade
pip install pip --upgrade
pip install debtools --upgrade
python setup.py install
python setup.py install
pip install gunicorn==18.0
pip uninstall futures
# sed -i 's/raise type(self._exception), self._exception, self._traceback/raise type(self._exception)/g' ~/.virtualenvs/djangofloor3/lib/python3.2/site-packages/futures-3.0.3-py3.2.egg/concurrent/futures/_base.py
multideb -r
echo "" > ~/.virtualenvs/djangofloor3/lib/python3.2/site-packages/setuptools.pth
rm -rf `find * | grep pyc$`
python setup.py --command-packages=stdeb.command bdist_deb
mv deb_dist/*deb deb
python setup.py install
cd demo
rm -rf `find * | grep pyc$`
python setup.py bdist_deb2
deb-dep-tree deb_dist/*deb
cd ..
sudo dpkg -i deb/*.deb
sudo dpkg -i demo/deb_dist/python3-*.deb