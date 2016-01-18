Generating documentation
========================

Documentation is an important part of a software.
DjangoFloor provides a basic, templated, documentation that can be automatically generated for your project.

.. code-block:: bash

  python manage.py gen_dev_files my_root

You can easily adapt this basic documentation to your own needs.
You just have to create in your app `my_app` a folder named `templates/my_app/dev`.
All files in this folder will be templated and written to the given root (most probably `.`).

Here is the list of the default generated files (you can find them in `djangofloor/templates/djangofloor/dev`.

.. code-block:: bash

  ├── debian-7-python3.sh
  ├── debian-8-python3.sh
  ├── doc
  │   ├── Makefile
  │   ├── make.bat
  │   └── source
  │       ├── conf.py
  │       ├── configuration.rst
  │       ├── debian.rst
  │       ├── index.rst
  │       └── installation.rst
  ├── stdeb-debian-7.cfg
  ├── stdeb-debian-8.cfg
  ├── stdeb.cfg
  └── ubuntu-14.04-15.10-python3.sh

Assume that you have the following tree in `my_app/templates/my_app/dev`:

.. code-block:: bash

  └── doc
      └── source
          ├── extra_file.rst
          └── index.rst

Your folder and DjangoFloor's one will be merged following these rules:

    * any file existing in one of these folder will be written,
    * if a file is defined in both folders, then your file overrides DjangoFloor's one,
    * an empty file will be ignored (so you can skip some default files).

These files are templated using the Django template system. You can override only parts of the default files.

.. code-block:: templates

  {% extends 'djangofloor/dev/doc/source/index.rst' %}
  {% block description %}
  This is a description of a project
  {% endblock %}
