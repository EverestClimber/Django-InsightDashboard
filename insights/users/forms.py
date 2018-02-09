# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django.contrib.auth import password_validation
from django.utils.translation import ugettext_lazy as _

from crispy_forms.layout import Div, Layout, Fieldset, Field
from crispy_forms.helper import FormHelper

from .models import User


class UpdateUserForm(forms.ModelForm):
    helper = FormHelper()
    helper.layout = Layout(
        Div(
            Div(
                Fieldset(
                    '',
                    'name',
                    'email',
                    Field('country', css_class='selectpicker', data_style='btn selectpicker-btn'),
                    Field('secondary_language', css_class='selectpicker', data_style='btn selectpicker-btn'),
                ),
                css_class="col-sm-6"),
            Div(
                Fieldset(
                    '',
                    'therapeutic_areas',
                    'groups',
                ),
                css_class="col-sm-6"),
            css_class="row",
        ),
    )

    email = forms.EmailField(label=_('Email address'), required=True)

    class Meta:
        model = User
        fields = ['email', 'name',
                  'therapeutic_areas', 'country', 'secondary_language',
                  'groups']

    def save(self, commit=True):
        # commit=False tells Django that "Don't send this to database yet."
        # user = super(UpdateUserForm, self).save(commit=False)
        user = super(UpdateUserForm, self).save()
        user.username = self.cleaned_data['email']
        # never get in, so never update
        if commit:
            user.save()
        return user


class CreateUserForm(forms.ModelForm):
    helper = FormHelper()
    helper.layout = Layout(
        Div(
            Div(
                Fieldset(
                    '',
                    'name',
                    'email',
                    'password1',
                    'password2',
                    Field('country', css_class='selectpicker', data_style='btn selectpicker-btn'),
                    Field('secondary_language', css_class='selectpicker', data_style='btn selectpicker-btn'),
                ),
                css_class="col-sm-6"),
            Div(
                Fieldset(
                    '',
                    'therapeutic_areas',
                    'groups',
                ),
                css_class="col-sm-6"),
            css_class="row",
        ),
    )
    password1 = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_('Password (again)'),
        strip=False,
        help_text=_('Enter the same password as before, for verification.'),
        widget=forms.PasswordInput())
    email = forms.EmailField(label=_('Email address'), required=True)

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'name',
                  'therapeutic_areas', 'country', 'secondary_language',
                  'groups']

    def clean(self):
        cleaned_data = super().clean()
        if 'password1' in cleaned_data:
            if cleaned_data['password1'] != cleaned_data['password2']:
                self.add_error('password1', _('Passwords did not match'))
            else:
                password_validation.validate_password(self.cleaned_data.get('password2'), self.instance)

        return cleaned_data

    def save(self, commit=True):
        user = super().save()
        user.set_password(self.cleaned_data['password1'])
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user
