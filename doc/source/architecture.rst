Global architecture
===================


A complete production server is based on several components:

    * pure web server: apache or nginx (or any equivalent),
    * application server: gunicorn or uwsgi,
    * main database: mysql or postgresql (or any SQL database supported by Django),
    * secondary database, for session and cache: redis,
    * daemon controler: systemd or supervisor, allowing to automatically start (or restart) services,
    * your application, of course.


The webserver must handle three kinds of paths:

    * static and media files (directly handled),
    * websockets (passed to uwsgi in websocket mode),
    * classical Django views (served in reverse-proxy mode).