# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-01-06 05:49
from __future__ import unicode_literals

from django.db import migrations
from django.template.defaultfilters import slugify


def ensure_slug(apps, schema_editor):
    countries = set()
    slugs = set()

    Country = apps.get_model('users', 'Country')
    for c in Country.objects.all():
        while c.name in countries:
            c.name += '-'
        countries.add(c.name)

        if c.slug is None or c.slug == '':
            c.slug = slugify(c.name)
        while c.slug in slugs:
            c.slug += '-'
        slugs.add(c.slug)

        c.save()


def dummy(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_auto_20171226_2047'),
    ]

    operations = [
        migrations.RunPython(ensure_slug, dummy),
    ]