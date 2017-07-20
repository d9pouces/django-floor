gen_doc_api:
	pip install sphinx_rtd_theme sphinxcontrib-autoanysrc starterpyth
	python setup.py gen_doc_api --api-dir doc/source/api  --modules-to-exclude='djangofloor.tests*,djangofloor.df_*,djangofloor.migrations*,djangofloor.management*,djangofloor,djangofloor.templatetags.metro_ui,djangofloor.conf,djangofloor.templatetags,djangofloor.wsgi,djangofloor.deb_fixes,djangofloor.views.legacy,djangofloor.wsgi.utf8validator,djangofloor.empty,djangofloor.iniconf,djangofloor.exceptions,djangofloor.wsgi.websocket' --pre-rm
	python setup.py gen_doc --html
