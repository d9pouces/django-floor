# -*- coding: utf-8 -*-
DEBUG = True
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache', 'LOCATION': 'unique-snowflake'}}
PIPELINE_ENABLED = not DEBUG
DF_REMOTE_USER_HEADER = 'HTTP-REMOTE-USER'  # HTTP-REMOTE-USER
