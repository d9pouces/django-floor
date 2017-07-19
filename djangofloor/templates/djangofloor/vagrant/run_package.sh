#!/usr/bin/env bash
sudo rm -rf /opt/updoc/
sudo dpkg -i /tmp/updoc/updoc_1.9.2_amd64.deb
sudo -u updoc updoc-manage migrate
cat << EOF | sudo tee /opt/updoc/etc/updoc/settings.ini
[global]
listen_address = 127.0.0.1:8129
EOF
sudo -u updoc updoc-manage runserver
sudo apt-get install redis-server
