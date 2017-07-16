#!/usr/bin/env bash
apt-get install ruby ruby-dev
gem install fpm
cd "{{ tmp_dir.1 }}"
python3 -c 'import subprocess, json; subprocess.check_call(json.load(open("{{ tmp_dir.1 }}/fpm.json")), cwd="{{ tmp_dir.1 }}")'
