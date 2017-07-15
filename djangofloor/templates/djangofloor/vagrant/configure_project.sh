{% include 'djangofloor/vagrant/post_install.sh' %}
mkdir -p {{ package_dir.1 }}{{ install_dir.1 }}
rsync -a {{ install_dir.1 }}/ {{ package_dir.1 }}{{ install_dir.1 }}/