# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-21 11:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0005_auto_20170118_1213'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='is_updated',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
