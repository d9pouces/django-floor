"""Forms used in default views
===========================

Currently, only a SearchForm is provided.
"""
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from djangofloor.decorators import validate_form, everyone, is_superuser

__author__ = "mgallet"


@validate_form(path="djangofloor.validate.search", is_allowed_to=everyone)
class SearchForm(forms.Form):
    """Only one query field is provided."""

    q = forms.CharField(
        max_length=255,
        min_length=1,
        label=_("Search"),
        help_text=_("Please enter your search pattern."),
    )


@validate_form(path="djangofloor.validate.logname", is_allowed_to=is_superuser)
class LogNameForm(forms.Form):
    log_name = forms.ChoiceField(
        required=False,
        initial=None,
        label=_("configured logger"),
        choices=[(x, x) for x in sorted(settings.LOGGING["loggers"])],
    )
    other_log_name = forms.CharField(
        max_length=255,
        min_length=1,
        label=_("other logger name"),
        required=False,
        help_text=_("Please enter the name of another logger to check."),
    )
    message = forms.CharField(
        max_length=255, min_length=1, label=_("message"), initial=_("log test")
    )
    level = forms.ChoiceField(
        label=_("level"),
        initial=40,
        choices=(
            (50, "critical"),
            (40, "error"),
            (30, "warning"),
            (20, "info"),
            (10, "debug"),
            (0, "notset"),
        ),
    )
