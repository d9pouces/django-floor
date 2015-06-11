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
