# noinspection PyUnresolvedReferences
from easydemo.views import (
    cache_60,
    cache_nevercache,
    cache_private,
    cache_vary_on_headers,
    chat,
    download_file,
    upload_file,
)
from django.conf.urls import url

urlpatterns = [
    url(r"^chat/", chat, name="chat"),
    url(r"^download/", download_file, name="download_file"),
    url(r"^demo/cache_60/", cache_60, name="cache_60"),
    url(
        r"^demo/cache_vary_on_headers/",
        cache_vary_on_headers,
        name="cache_vary_on_headers",
    ),
    url(r"^demo/cache_private/", cache_private, name="cache_private"),
    url(r"^demo/cache_nevercache/", cache_nevercache, name="cache_nevercache"),
    url(r"^upload/", upload_file, name="upload_file"),
]
