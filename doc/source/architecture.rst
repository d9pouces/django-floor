Global architecture
===================


A complete production server is based on several components:

    * pure web server: apache or nginx (or any equivalent),
    * main database: mysql or postgresql (or any SQL database supported by Django),
    * secondary database, for session and cache: redis,
    * daemon controler: systemd or supervisor, allowing to automatically start (or restart) services,
    * application server: gunicorn or uwsgi,
    * a celery worker,
    * some regular tasks (cleaning sessions, backup).


The webserver must handle three kinds of paths:

    * static and media files (directly handled),
    * websockets (passed to uwsgi in websocket mode, only if you use websockets),
    * classical Django views (served in reverse-proxy mode).

The complete architecture is incomplete without other classical development tasks:

    * unitary/non-regression testing (with classical tools like tox),
    * documentation (and DjangoFloor generates a customized documentation),
    * packages (pure-Python packages or Debian ones),
    * backup tasks (information on how to backup your data are given in the documentation),
    * a configuration cleanly separated from the code (DjangoFloor provides such a mechanism).