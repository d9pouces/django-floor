"""Callables settings
==================

Dynamically build smart settings related to django-pipeline, taking into account other settings or installed packages.
"""


def static_storage(settings_dict):
    if settings_dict["PIPELINE_ENABLED"]:
        return "djangofloor.backends.DjangofloorPipelineCachedStorage"
    return "django.contrib.staticfiles.storage.StaticFilesStorage"


static_storage.required_settings = ["PIPELINE_ENABLED"]


def pipeline_enabled(settings_dict):
    return settings_dict["USE_PIPELINE"] and not settings_dict["DEBUG"]


pipeline_enabled.required_settings = ["DEBUG", "USE_PIPELINE"]
