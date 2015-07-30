#!/bin/bash
sudo apt-get install --yes python3-all-dev dh-make virtualenvwrapper liblzma-dev python3-tz python3-setuptools
source /etc/bash_completion.d/virtualenvwrapper
mkvirtualenv -p `which python3.2` djangofloor3
workon djangofloor3
pip install setuptools --upgrade
pip install pip --upgrade
pip install debtools --upgrade
python setup.py install
python setup.py install
pip install gunicorn==18.0
pip uninstall futures -y
multideb -r
echo "" > ~/.virtualenvs/djangofloor3/lib/python3.2/site-packages/setuptools.pth
rm -rf `find * | grep pyc$`
python setup.py --command-packages=stdeb.command bdist_deb
mv deb_dist/*deb deb
python setup.py install
cd demo
python setup.py bdist_deb2
deb-dep-tree deb_dist/*deb