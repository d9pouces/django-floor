#!/usr/bin/env bash
gem install fpm
cd "{{ tmp_dir.1 }}"
# load the fpm command line (stored in a json file for avoiding problems with special chars in arguments)
python3 -c 'import subprocess, json; subprocess.check_call(json.load(open("{{ tmp_dir.1 }}/fpm.json")), cwd="{{ tmp_dir.1 }}")'
