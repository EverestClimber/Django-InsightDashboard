# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, ReadOnlyPasswordHashField
from django.utils.translation import gettext as _
from .models import User, Country, Language, TherapeuticArea


class MyUserChangeForm(UserChangeForm):
    password = ReadOnlyPasswordHashField(label="Password",
                                         help_text='<a href="../password/">Change password</a>')
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


class MyUserCreationForm(UserCreationForm):

    error_message = UserCreationForm.error_messages.update({
        'duplicate_username': 'This username has already been taken.'
    })

    class Meta(UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])


@admin.register(User)
class MyUserAdmin(AuthUserAdmin):
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    # fieldsets = (
    #         ('User Profile', {'fields': ('name', 'country')}),
    # ) + AuthUserAdmin.fieldsets
    fieldsets = (
        ('User Profile', {'fields': ('name', 'country', 'secondary_language', 'therapeutic_areas')}),
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'name', 'email', 'country',
                    'get_groups', 'is_staff', 'is_superuser')
    search_fields = ['name', 'email']

    def get_groups(self, user):
        return ", ".join(g.name for g in user.groups.all())
    get_groups.short_description = _('Groups')


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'use_in_reports', 'ordering', 'created_at')
    prepopulated_fields = {'slug': ('name',), }

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(TherapeuticArea)
class TherapeuticAreaAdmin(admin.ModelAdmin):
    list_display = ('name',)
