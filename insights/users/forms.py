# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

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
        subject = "[MLS Insights] Finish your account setup!"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = user.email

        email_context = Context(
            {
                'user': user,
                'set_password_url': user.get_set_password_url(request)
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
