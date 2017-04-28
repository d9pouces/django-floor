# -*- coding: utf-8 -*-
from functools import lru_cache

from django import forms

from djangofloor.conf.fields import ConfigField
from djangofloor.conf.merger import SettingMerger
from djangofloor.conf.settings import merger

__author__ = 'Matthieu Gallet'


@lru_cache()
def config_form_factory():
    """
    Generate the form class

    """
    assert isinstance(merger, SettingMerger)
    fields = []
    for config_field in merger.fields_provider:
        assert isinstance(config_field, ConfigField)
        form_field = config_field.get_form_field()
        fields.append(form_field)
    kls = type(forms.Form, fields, {})
    return kls


def set_config(request):
    kls = config_form_factory()
    if request.method == 'POST':
        form = kls(request.POST)
    else:
        form = kls()
