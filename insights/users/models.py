# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import base64

from django.contrib.auth.models import AbstractUser, AnonymousUser as DjangoAnonymousUser
from django.core.signing import TimestampSigner
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Country(models.Model):
    name = models.CharField('Country name', unique=True, max_length=100)
    slug = models.SlugField('Country slug', unique=True)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True, null=True)
    ordering = models.PositiveIntegerField('Order in reports', default=1, blank=True, db_index=True)
    use_in_reports = models.BooleanField('Use in reports', default=True, blank=True, db_index=True)

    class Meta:
        verbose_name_plural = 'countries'
        ordering = ['ordering', 'id']

    def __str__(self):
        return self.name


class Language(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    code = models.CharField(_('Code'), max_length=2)

    def __str__(self):
        return self.name


class TherapeuticArea(models.Model):
    name = models.CharField(_('Name'), max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_('Name of User'), blank=True, max_length=255)
    country = models.ForeignKey(Country, null=True)
    secondary_language = models.ForeignKey(Language, null=True, blank=True)
    therapeutic_areas = models.ManyToManyField(
        TherapeuticArea, related_name="users", blank=True,
        help_text=_('Hold down "Control", or "Command" on a Mac, to select more than one.'))

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})

    def get_flags(self):
        if self.is_superuser:
            return ['Superuser']
        return list(g.name for g in self.groups.all())

    def get_set_password_url(self, request):
        signer = TimestampSigner()
        user_hash = signer.sign(self.email)
        encoded_hash = base64.urlsafe_b64encode(user_hash.encode('utf-8'))
        return request.build_absolute_uri(reverse('users:complete', kwargs={'hash': encoded_hash}))


class AnonymousUser(User, DjangoAnonymousUser):
    class Meta:
        proxy = True
