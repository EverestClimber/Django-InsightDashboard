# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-01-05 04:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0021_survey_organizations'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ['ordering', 'created_at']},
        ),
        migrations.AddField(
            model_name='question',
            name='ordering',
            field=models.PositiveIntegerField(default=0, verbose_name='Order'),
        ),
        migrations.AddField(
            model_name='question',
            name='survey',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='survey.Survey'),
        ),
    ]
