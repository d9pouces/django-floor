#!/usr/bin/env bash
pip3 install setuptools pip --upgrade
pip3 install "{{ tmp_dir.1 }}/{{ dist_filename }}"
