#!/usr/bin/env bash
{{ processes.control.command_line }} collectstatic --noinput
{% include 'djangofloor/vagrant/after_install.sh' %}
mkdir -p "{{ package_dir.1 }}{{ install_dir.1 }}"
rm -rf "{{ package_dir.1 }}/usr/local/bin"
mkdir -p "{{ package_dir.1 }}/usr/local/bin"
mkdir -p "{{ package_dir.1 }}/var/log"
mkdir -p "{{ package_dir.1 }}/etc"
rsync -a "{{ install_dir.1 }}/" "{{ package_dir.1 }}{{ install_dir.1 }}/"
for k in "{{ install_dir.1 }}/bin/{{ DF_MODULE_NAME }}-*"; do
    ln -s ${k} "{{ package_dir.1 }}/usr/local/bin/"
done
rm -f "{{ package_dir.1 }}/etc/{{ DF_MODULE_NAME }}" "{{ package_dir.1 }}/var/{{ DF_MODULE_NAME }}" "{{ package_dir.1 }}/var/log/{{ DF_MODULE_NAME }}"
ln -s "{{ install_dir.1 }}/etc/{{ DF_MODULE_NAME }}" "{{ package_dir.1 }}/etc/{{ DF_MODULE_NAME }}"
ln -s "{{ install_dir.1 }}/var/{{ DF_MODULE_NAME }}" "{{ package_dir.1 }}/var/{{ DF_MODULE_NAME }}"
ln -s "{{ install_dir.1 }}/var/{{ DF_MODULE_NAME }}/log" "{{ package_dir.1 }}/var/log/{{ DF_MODULE_NAME }}"
