#!/usr/bin/env bash
"{{ install_dir.1 }}/bin/pip3" install setuptools pip --upgrade
"{{ install_dir.1 }}/bin/pip3" install "{{ tmp_dir.1 }}/{{ dist_filename }}"
