"""Root URLs provided by DjangoFloor
=================================

By default, register URLs for the admin site, `jsi18n`, static and media files, favicon and robots.txt.
If DjangoDebugToolbar is present, then its URL is also registered.

"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.utils.module_loading import import_string
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve

from djangofloor import urls
from djangofloor.scripts import load_celery
from djangofloor.utils import get_view_from_string
from djangofloor.views import favicon, robots

__author__ = 'Matthieu Gallet'

load_celery()
admin.autodiscover()
admin_urls = admin.site.urls

if settings.DF_URL_CONF:
    extra_urls = import_string(settings.DF_URL_CONF)
else:
    extra_urls = []
prefix = '^' + settings.URL_PREFIX[1:]
catalog_view = JavaScriptCatalog.as_view(packages=['djangofloor', 'django.contrib.admin'])
urlpatterns = [url(prefix + r'jsi18n/$', catalog_view, name='jsi18n'),
               url(prefix + r'%s(?P<path>.*)$' % settings.MEDIA_URL[1:], serve, {'document_root': settings.MEDIA_ROOT}),
               url(prefix + r'%s(?P<path>.*)$' % settings.STATIC_URL[1:], serve,
                   {'document_root': settings.STATIC_ROOT}),
               url(prefix + r'df/', include(urls, namespace='df')),
               url(prefix + r'robots\.txt$', robots),
               url(prefix + r'apple-touch-icon\.png$', serve,
                   {'document_root': settings.STATIC_ROOT, 'path': 'favicon/apple-touch-icon.png'}),
               url(prefix + r'apple-touch-icon-precomposed\.png$', serve,
                   {'document_root': settings.STATIC_ROOT, 'path': 'favicon/apple-touch-icon-precomposed.png'}),
               url(prefix + r'favicon\.ico$', favicon, name='favicon'),
               ] + list(extra_urls)
if settings.USE_ALL_AUTH:
    # noinspection PyPackageRequirements
    from allauth.account.views import login as allauth_login
    urlpatterns += [
        url(prefix + r'admin/login/$', allauth_login),
        url(prefix + r'accounts/', include('allauth.urls'))
    ]
else:
    urlpatterns += [url(prefix + r'auth/', include('django.contrib.auth.urls'))]

urlpatterns += [url(prefix + r'admin/', include(admin_urls[:2]))]
if settings.USE_REST_FRAMEWORK:
    urlpatterns += [url(prefix + r'api-auth/', include('rest_framework.urls', namespace='rest_framework'))]
if settings.DF_INDEX_VIEW:
    urlpatterns += [url(prefix + r'$', get_view_from_string(settings.DF_INDEX_VIEW), name='index')]
if settings.DEBUG and settings.USE_DEBUG_TOOLBAR:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import debug_toolbar
    urlpatterns += [url(prefix + r'__debug__/', include(debug_toolbar.urls)), ]
