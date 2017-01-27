# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-24 15:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields
import reports.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_anonymoususer'),
        ('survey', '0010_remove_question_report_order'),
        ('reports', '0003_organizationstat_report_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionStat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', jsonfield.fields.JSONField(default=dict)),
                ('ordering', models.PositiveIntegerField(blank=True, db_index=True, default=1, verbose_name='Ordering in reports')),
                ('country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.Country')),
            ],
            bases=(reports.models.RepresentationTypeMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Representation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordering', models.PositiveIntegerField(blank=True, db_index=True, default=1, verbose_name='Ordering in reports')),
                ('label1', models.CharField(blank=True, default='', max_length=400, verbose_name='Label 1')),
                ('label2', models.CharField(blank=True, default='', max_length=400, verbose_name='Label 2')),
                ('label3', models.CharField(blank=True, default='', max_length=400, verbose_name='Label 3')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='survey.Question')),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='survey.Survey')),
            ],
            bases=(reports.models.RepresentationTypeMixin, models.Model),
        ),
        migrations.RemoveField(
            model_name='organizationstat',
            name='report_order',
        ),
        migrations.AddField(
            model_name='organizationstat',
            name='ordering',
            field=models.PositiveIntegerField(blank=True, db_index=True, default=1, verbose_name='Ordering in reports'),
        ),
        migrations.AddField(
            model_name='questionstat',
            name='representation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reports.Representation'),
        ),
        migrations.AddField(
            model_name='questionstat',
            name='survey',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='survey.Survey'),
        ),
    ]
