from django import forms
from djangofloor.decorators import validate_form, everyone
from django.utils.translation import ugettext_lazy as _

__author__ = "Matthieu Gallet"


@validate_form(path="validate_test", is_allowed_to=everyone)
class TestForm(forms.Form):
    email = forms.EmailField(label="Email", help_text="Please enter your e-mail")
    name = forms.CharField(label="Name", help_text="Please enter your name")
    age = forms.IntegerField(label="Age")


@validate_form(path="validate_loginform", is_allowed_to=everyone)
class ChatLoginForm(forms.Form):
    name = forms.CharField(label="Name", help_text="Please enter your name")


@validate_form(path="djangofloor.validate.search", is_allowed_to=everyone)
class SearchForm(forms.Form):
    q = forms.CharField(
        max_length=255,
        min_length=1,
        label=_("Search"),
        help_text=_("Please enter your search pattern."),
    )


@validate_form(path="validate_upload_file", is_allowed_to=everyone)
class UploadFileForm(forms.Form):
    name = forms.CharField(
        label="Name", help_text="Please enter your name", required=False
    )
    content = forms.FileField(label="File", help_text="Please select a file")


class SimpleUploadFileForm(forms.Form):
    content = forms.FileField(label="File", help_text="Please select a file")
