from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


def admin_context(values=None):
    result = {
        'site_header': settings.DF_PROJECT_NAME,  # <h1>{{ title }} | {{ site_header }}</h1>
        'site_title': settings.DF_PROJECT_NAME,  # <title>{{ title }} | {{ site_title }}</title>
        'site_url': reverse('index') if settings.DF_INDEX_VIEW else '/',
        'is_popup': False,
        'title': _('Page title'),
        'breadcrumbs': [],  # list of ("URL" or None, "title")
    }
    if values:
        result.update(values)
    return result
