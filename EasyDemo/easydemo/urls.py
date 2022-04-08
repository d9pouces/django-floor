from django.urls import re_path
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

urlpatterns = [
    re_path(r"^chat/", chat, name="chat"),
    re_path(r"^download/", download_file, name="download_file"),
    re_path(r"^demo/cache_60/", cache_60, name="cache_60"),
    re_path(
        r"^demo/cache_vary_on_headers/",
        cache_vary_on_headers,
        name="cache_vary_on_headers",
    ),
    re_path(r"^demo/cache_private/", cache_private, name="cache_private"),
    re_path(r"^demo/cache_nevercache/", cache_nevercache, name="cache_nevercache"),
    re_path(r"^upload/", upload_file, name="upload_file"),
]
