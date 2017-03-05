Provided settings
=================

DjangoFloor sets several settings used by Django (or third-party packages) and defines some new settings, specifically
used by DjangoFloor.

DjangoFloor also allows references between settings: for example, you only defines `SERVER_BASE_URL`
(like 'https://www.example.com/site/' ) and `SERVER_NAME` ('www.example.com'), `SERVER_PORT` ('443'),
`USE_SSL` ('True'), `SERVER_PROTOCOL` ('https') and `URL_PREFIX` ('/site/') are deduced.

These settings are defined in :mod:`djangofloor.conf.defaults`.
Settings that should be customized on each installation (like the server name or the database password) can be
written in .ini files. The mapping between the Python setting and the [section/option] system is defined in
:mod:`djangofloor.conf.mapping`.

.. literalinclude:: ../../djangofloor/conf/defaults.py
   :language: python
   :lines: 24-433
