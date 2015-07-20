useradd {{ project_name }} -b /var/ -U -m -r
chown -R {{ project_name }}: /var/{{ project_name }}
# python-foo.postinst
# python3-foo.postinst
