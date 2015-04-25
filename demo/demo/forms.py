# coding=utf-8
from __future__ import unicode_literals
from django import forms

__author__ = 'flanker'


class SimpleForm(forms.Form):
    first_name = forms.CharField(label='first name', required=False)
    last_name = forms.CharField(label='last name', required=False)
    test_boolean = forms.BooleanField(label='BooleanField')
    test_nboolean = forms.NullBooleanField(label='NullBooleanField')
    test_choice = forms.ChoiceField(label='ChoiceField', choices=(('choice1', 'C1'), ('choice2', 'C2')), required=False)
    test_choice2 = forms.ChoiceField(label='ChoiceField', choices=(('choice1', 'C1'), ('choice2', 'C2')), required=True)
    test_mchoice = forms.MultipleChoiceField(label='MultipleChoiceField', choices=(('choice1', 'C1'), ('choice2', 'C2')), required=False)
