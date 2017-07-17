import random

from django import forms

from djangofloor.decorators import function, validate_form, everyone


@validate_form(path='validate', is_allowed_to=everyone)
class TestForm(forms.Form):
    email = forms.EmailField(label='Email', help_text='Please enter your e-mail')
    name = forms.CharField(label='Name', help_text='Please enter your name')
    age = forms.IntegerField(label='Age')


# noinspection PyUnusedLocal
@function(path='test_function', is_allowed_to=everyone)
def test_function(window_info):
    # TODO to remove before release
    return 'Coucou : %d' % random.randint(0, 100)
