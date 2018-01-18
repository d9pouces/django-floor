"""Templatetags used to generate files
===================================

Various templatetags provided by DjangoFloor in the
`gen_dev_files` command.


"""
import logging

from django import template
from django.utils.safestring import mark_safe

from djangofloor.conf.providers import IniConfigProvider
from djangofloor.conf.settings import merger
from djangofloor.utils import smart_pipfile_url

register = template.Library()
logger = logging.getLogger('django.requests')


register.filter(name='pipfile_url', filter_func=smart_pipfile_url)


@register.simple_tag()
def local_settings(**kwargs):
    provider = IniConfigProvider()
    for config_field in sorted(merger.fields_provider.get_config_fields(), key=lambda x: x.name):
        if config_field.setting_name not in kwargs:
            continue
        old_value = config_field.value
        config_field.value = kwargs[config_field.setting_name]
        provider.set_value(config_field, include_doc=False)
        config_field.value = old_value
    return mark_safe(provider.to_str())


@register.filter
def line_prefix(value, prefix='  '):
    return '\n'.join([prefix + x for x in value.splitlines()])
