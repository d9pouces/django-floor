Using the demo
==============

First, you must download and unzip the source on `Github <https://github.com/d9pouces/django-floor/archive/master.zip>`_.

.. code-block:: bash

  curl -o django-floor.zip https://github.com/d9pouces/django-floor/archive/master.zip
  unzip django-floor.zip
  cd DjangoFloor/demo
  mkvirtualenv -p `which python2.7` demo
  python setup.py develop
  demo-manage migrate
  demo-manage collectstatic --noinput
  demo-manage runserver

And open http://localhost:9000/test.html in your favorite browser.

If you want to test with Celery, please install a Redis server (it should listen on 127.0.0.1:6379) and set `USE_CELERY` to `True` in `demo/defaults.py`.
In another shell:

.. code-block:: bash

  workon demo
  demo-celery worker

If you want to test websockets:

.. code-block:: bash

  workon demo
  pip install djangofloor[websocket]
  demo-manage runserver
