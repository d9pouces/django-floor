Generate .deb packages
======================

A way to distribute a website is to package as Debian packages.

  * generate basic informations with `python setup.py sdist_dsc`
  * collect static files to move to
  * gather all commands to run (gunicorn|uwsgi, celery)
  * prepare control files for supervisor (Debian 7-, Ubuntu 14.10-) or systemd (Ubuntu 15.04+, Debian 8+)
  * create user
  * prepare config files for apache or nginx
  * prepare crontab
  * regenerate DEBIAN/md5sums
  * fix dependencies (fix python version, add supervisor/apache/nginx)

.
├── changelog
├── compat
├── control
├── files
├── python-djangofloor
│   ├── DEBIAN
│   │   ├── control
│   │   ├── md5sums
│   │   ├── postinst
│   │   └── prerm
│   └── usr
│       ├── bin
│       │   ├── djangofloor-celery
│       │   ├── djangofloor-gunicorn
│       │   ├── djangofloor-manage
│       │   └── djangofloor-uswgi
│       ├── lib
│       │   └── python2.7
│       │       └── dist-packages
│       │           ├── djangofloor
│       │           │   ├── __init__.py
│       │           │   ├── admin.py
│       │           │   ├── backends.py
│       │           │   ├── celery.py
│       │           │   ├── iniconf.py
│       │           │   ├── locale
│       │           │   │   ├── README
│       │           │   │   └── xx_XX
│       │           │   │       └── LC_MESSAGES
│       │           │   │           └── xproject.po
│       │           │   ├── log.py
│       │           │   ├── management
│       │           │   │   ├── __init__.py
│       │           │   │   └── commands
│       │           │   │       ├── __init__.py
│       │           │   │       ├── config.py
│       │           │   │       ├── config_example.py
│       │           │   │       └── dumpdb.py
│       │           │   ├── middleware.py
│       │           │   ├── migrations
│       │           │   │   ├── 0001_initial.py
│       │           │   │   └── __init__.py
│       │           │   ├── root_urls.py
│       │           │   ├── scripts.py
│       │           │   ├── sessions_list.py
│       │           │   ├── settings.py
│       │           │   ├── static
│       │           │   │   └── js
│       │           │   │       ├── djangofloor.js
│       │           │   │       ├── html5shiv.js
│       │           │   │       ├── jquery-1.10.2.js
│       │           │   │       ├── jquery-1.10.2.min.map
│       │           │   │       ├── jquery.min.js
│       │           │   │       └── respond.min.js
│       │           │   ├── tasks.py
│       │           │   ├── templates
│       │           │   │   └── djangofloor
│       │           │   │       ├── base.html
│       │           │   │       ├── index.html
│       │           │   │       ├── robots.txt
│       │           │   │       └── signals.html
│       │           │   ├── templatetags
│       │           │   │   ├── __init__.py
│       │           │   │   └── djangofloor.py
│       │           │   ├── tests
│       │           │   │   ├── __init__.py
│       │           │   │   └── test_decorators.py
│       │           │   ├── utils.py
│       │           │   ├── views.py
│       │           │   ├── wsgi.py
│       │           │   ├── wsgi_http.py
│       │           │   └── wsgi_websockets.py
│       │           └── djangofloor-0.14.0.egg-info
│       │               ├── PKG-INFO
│       │               ├── SOURCES.txt
│       │               ├── dependency_links.txt
│       │               ├── entry_points.txt
│       │               ├── not-zip-safe
│       │               ├── requires.txt
│       │               └── top_level.txt
│       └── share
│           ├── doc
│           │   └── python-djangofloor
│           │       └── changelog.Debian.gz
│           └── pyshared
│               ├── djangofloor
│               │   ├── __init__.py
│               │   ├── admin.py
│               │   ├── backends.py
│               │   ├── celery.py
│               │   ├── context_processors.py
│               │   ├── decorators.py
│               │   ├── defaults.py
│               │   ├── df_pipeline.py
│               │   ├── df_redis.py
│               │   ├── df_ws4redis.py
│               │   ├── empty.py
│               │   ├── exceptions.py
│               │   ├── iniconf.py
│               │   ├── locale
│               │   │   ├── README
│               │   │   └── xx_XX
│               │   │       └── LC_MESSAGES
│               │   │           └── xproject.po
│               │   ├── log.py
│               │   ├── management
│               │   │   ├── __init__.py
│               │   │   └── commands
│               │   │       ├── __init__.py
│               │   │       ├── config.py
│               │   │       ├── config_example.py
│               │   │       └── dumpdb.py
│               │   ├── middleware.py
│               │   ├── migrations
│               │   │   ├── 0001_initial.py
│               │   │   └── __init__.py
│               │   ├── root_urls.py
│               │   ├── scripts.py
│               │   ├── sessions_list.py
│               │   ├── settings.py
│               │   │   ├── fonts
│               │   │   │   ├── glyphicons-halflings-regular.woff
│               │   │   │   └── glyphicons-halflings-regular.woff2
│               │   │   ├── images
│               │   │   │   ├── favicon.ico
│               │   │   │   └── favicon.png
│               │   │   └── js
│               │   │       ├── jquery.min.js
│               │   │       └── respond.min.js
│               │   ├── tasks.py
│               │   ├── templates
│               │   │   ├── account
│               │   │   │   ├── verification_sent.html
│               │   │   │   └── verified_email_required.html
│               │   │   ├── base.html
│               │   │   └── djangofloor
│               │   │       ├── base.html
│               │   │       ├── index.html
│               │   │       ├── robots.txt
│               │   │       └── signals.html
│               │   ├── templatetags
│               │   │   ├── __init__.py
│               │   │   └── djangofloor.py
│               │   ├── tests
│               │   │   ├── __init__.py
│               │   │   └── test_decorators.py
│               │   ├── utils.py
│               │   ├── views.py
│               │   ├── wsgi.py
│               │   ├── wsgi_http.py
│               │   └── wsgi_websockets.py
│               └── djangofloor-0.14.0.egg-info
│                   ├── PKG-INFO
│                   ├── SOURCES.txt
│                   ├── dependency_links.txt
│                   ├── entry_points.txt
│                   ├── not-zip-safe
│                   ├── requires.txt
│                   └── top_level.txt
├── python-djangofloor.debhelper.log
├── python-djangofloor.postinst.debhelper
├── python-djangofloor.prerm.debhelper
├── python-djangofloor.substvars
├── rules
└── source
    ├── format
    └── options
