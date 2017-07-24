Quick installation
==================

You can quickly test {{ DF_PROJECT_NAME }}, storing all data in $HOME/{{ DF_MODULE_NAME }}:

.. code-block:: bash

{% block install_deps %}    sudo apt-get install {{ python_version }} {{ python_version }}-dev build-essential
{% endblock %}{% block application %}    pip install {{ DF_MODULE_NAME }}
{% endblock %}{% block pre_application %}{% endblock %}    {{ processes.django }} collectstatic --noinput  # prepare static files (CSS, JS, …)
    {{ processes.django }} migrate  # create the database (SQLite by default)
{% block post_application %}    {{ processes.django }} createsuperuser  # create an admin user
{% endblock %}

{% block basic_config %}
You can easily change the root location for all data (SQLite database, uploaded or temp files, static files, …) by
editing the configuration file.

.. code-block:: bash

    CONFIG_FILENAME=`{{ processes.django }}  config ini -v 2 | head -n 1 | grep ".ini" | cut -d '"' -f 2`
    # create required folders
    mkdir -p `dirname $FILENAME` $HOME/{{ DF_MODULE_NAME }}
    # prepare a limited configuration file
    cat << EOF > $FILENAME
    [global]
    data = $HOME/{{ DF_MODULE_NAME }}
    EOF

Of course, you must run again the `migrate` and `collectstatic` commands (or moving data to this new folder).
{% endblock %}

You can launch the server process{% if USE_CELERY %}es (the second process is required for background tasks){% endif %}:

.. code-block:: bash
{% block run_application %}
    {% if processes.aiohttp %}{{ processes.aiohttp }}{% elif processes.gunicorn %}{{ processes.gunicorn }}{% endif %}
{% if USE_CELERY %}    {{ processes.celery }} worker -Q {{ required_celery_queues|join:',' }}
{% endif %}{% endblock %}

Then open http://{{ LISTEN_ADDRESS }} in your favorite browser.

You should use virtualenv or install {{ DF_PROJECT_NAME }} using the `--user` option.