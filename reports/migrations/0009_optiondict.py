# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-25 22:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_auto_20170125_2029'),
    ]

    operations = [
        migrations.CreateModel(
            name='OptionDict',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lower', models.CharField(max_length=200, unique=True)),
                ('original', models.CharField(max_length=200)),
            ],
        ),
    ]
