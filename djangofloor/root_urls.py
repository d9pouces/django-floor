"""Root URLs provided by DjangoFloor
=================================

By default, register URLs for the admin site, `jsi18n`, static and media files, favicon and robots.txt.
If DjangoDebugToolbar is present, then its URL is also registered.

"""
from django.conf import settings
from django.conf.urls import include
from django.urls import re_path
from django.utils.module_loading import import_string, autodiscover_modules
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve

from djangofloor import urls
from djangofloor.scripts import load_celery
from djangofloor.utils import get_view_from_string
from djangofloor.views import favicon, robots

__author__ = "Matthieu Gallet"

load_celery()

catalog_view = JavaScriptCatalog.as_view(packages=settings.DF_JS_CATALOG_VIEWS)
urlpatterns = [
    re_path(r"jsi18n/$", catalog_view, name="jsi18n"),
    re_path(
        r"%s(?P<path>.*)$" % settings.MEDIA_URL[1:],
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
    re_path(
        r"%s(?P<path>.*)$" % settings.STATIC_URL[1:],
        serve,
        {"document_root": settings.STATIC_ROOT},
    ),
    re_path(r"df/", include(urls, namespace="df")),
    re_path(r"robots\.txt$", robots),
    re_path(
        r"apple-touch-icon\.png$",
        serve,
        {"document_root": settings.STATIC_ROOT, "path": "favicon/apple-touch-icon.png"},
    ),
    re_path(
        r"apple-touch-icon-precomposed\.png$",
        serve,
        {
            "document_root": settings.STATIC_ROOT,
            "path": "favicon/apple-touch-icon-precomposed.png",
        },
    ),
    re_path(r"favicon\.ico$", favicon, name="favicon"),
]


if settings.DF_URL_CONF:
    extra_urls = import_string(settings.DF_URL_CONF)
    urlpatterns += list(extra_urls)

if settings.USE_ALL_AUTH:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    from allauth.account.views import login as allauth_login

    urlpatterns += [
        re_path(r"admin/login/$", allauth_login),
        re_path(r"accounts/", include("allauth.urls")),
    ]
else:
    urlpatterns += [re_path(r"auth/", include("django.contrib.auth.urls"))]

if settings.DF_ADMIN_SITE:
    admin_site = import_string(settings.DF_ADMIN_SITE)
    autodiscover_modules("admin", register_to=admin_site)
    urlpatterns += [re_path(r"admin/", include(admin_site.urls[:2]))]

if settings.USE_REST_FRAMEWORK:
    # noinspection PyUnresolvedReferences
    urlpatterns += [
        re_path(r"api-auth/", include("rest_framework.urls", namespace="rest_framework"))
    ]
if settings.DEBUG and settings.USE_DEBUG_TOOLBAR:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import debug_toolbar

    urlpatterns += [re_path(r"__debug__/", include(debug_toolbar.urls))]
if settings.DF_INDEX_VIEW:
    urlpatterns += [
        re_path(r"^$", get_view_from_string(settings.DF_INDEX_VIEW), name="index")
    ]


url_prefix = settings.URL_PREFIX[1:]

if url_prefix:
    urlpatterns = [re_path("^" + url_prefix, include(urlpatterns))]
