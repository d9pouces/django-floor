# -*- coding=utf-8 -*-
"""Forms used in default views
===========================

Currently, only a SearchForm is provided.
"""
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from djangofloor.decorators import validate_form, everyone

__author__ = 'mgallet'


@validate_form(path='djangofloor.validate.search', is_allowed_to=everyone)
class SearchForm(forms.Form):
    """Only one query field is provided."""
    q = forms.CharField(max_length=255, min_length=1, label=_('Search'),
                        help_text=_('Please enter your search pattern.'))
