# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from allauth.account.forms import LoginForm
from allauth.utils import get_current_site
from django import forms
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template
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
        user = super(UpdateUserForm, self).save()
        user.username = self.cleaned_data['email']

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
    email = forms.EmailField(label=_('Email address'), required=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'therapeutic_areas', 'country',
                  'secondary_language', 'groups']


    def save(self, commit=True):
        user = super().save()
        user.username = self.cleaned_data['email']
        # User becomes active once he sets up his password
        user.is_active = False
        if commit:
            user.save()
        return user

    def send_set_password_email(self, user, request):
        plaintext_mail = get_template('users/emails/set_password_initial.txt')
        html_mail = get_template('users/emails/set_password_initial.html')
        subject = "[MSL Insights] Finish your account setup!"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = user.email
        current_site = get_current_site(request)

        email_context = Context(
            {
                'user': user,
                'set_password_url': user.get_set_password_url(request),
                'site_name': current_site.name,
                'site_domain': current_site.domain
            }
        )
        text_content = plaintext_mail.render(email_context)
        html_content = html_mail.render(email_context)
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [to]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()


class CustomLoginForm(LoginForm):
    def clean(self):
        required_field_error_msg = 'This field is required.'
        if not self.cleaned_data:
            if required_field_error_msg in self.errors.get('login') and \
                    required_field_error_msg in self.errors.get('password'):
                self.errors.pop('login')
                self.errors.pop('password')
                raise forms.ValidationError(
                    _('Both email and password are required')
                )
        if 'login' in self.errors.keys():
            self.errors.pop('password', '')
        elif 'password' in self.errors.keys():
            self.errors.pop('login', '')
        return super().clean()
