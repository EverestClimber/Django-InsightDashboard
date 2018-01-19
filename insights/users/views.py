# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, ListView, RedirectView, UpdateView, CreateView, FormView
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from django.contrib.auth import password_validation
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin

from .models import User


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = 'username'
    slug_url_kwarg = 'username'


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse('users:detail',
                       kwargs={'username': self.request.user.username})


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):

    fields = ['name', 'email', 'therapeutic_areas', 'country',
              'secondary_language', 'groups']

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'

    permission_required = 'users.change_user'
    raise_exception = True

    def get_success_url(self):
        return reverse('users:list')


class CreateUserForm(forms.ModelForm):
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


class UserSetPasswordView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, FormView):
    template_name = 'account/password_change.html'
    permission_required = 'users.change_user'
    raise_exception = True

    def get_form(self, form_class=None):
        self.user = get_object_or_404(User, username=self.kwargs['username'])
        return SetPasswordForm(self.user, **self.get_form_kwargs())

    def get_success_url(self):
        return reverse('users:update_user', kwargs={'username': self.kwargs['username']})

    def get_success_message(self, cleaned_data):
        return _('Password for %(username)s is changed successfully.' % {'username': self.user.name})


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = CreateUserForm
    slug_field = 'username'
    slug_url_kwarg = 'username'

    permission_required = 'users.change_user'
    raise_exception = True

    def get_success_url(self):
        return reverse('users:list')


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User

    slug_field = 'username'
    slug_url_kwarg = 'username'

    permission_required = 'users.change_user'
    raise_exception = True

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        return qs
