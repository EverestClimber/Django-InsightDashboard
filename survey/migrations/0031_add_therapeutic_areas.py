# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-01-09 07:43
from __future__ import unicode_literals

from django.db import migrations


def forward(apps, schema_editor):
    Survey = apps.get_model('survey', 'Survey')
    TA = apps.get_model('users', 'TherapeuticArea')
    User = apps.get_model('users', 'User')

    for ta_name in ["Bone / Osteoporosis",
                    "Immunology ",
                    "Orthopaedics",
                    "Cardiovascular",
                    "Infectious diseases",
                    "Pulmonology",
                    "CNS",
                    "Inflammation",
                    "Psychiatry",
                    "Dermatology",
                    "Internal diseases",
                    "Respiratory",
                    "Diabetes",
                    "Metabolic diseases",
                    "Rheumatology",
                    "Endocrinology",
                    "Nephrology",
                    "Surgery",
                    "ENT",
                    "Neurology",
                    "Urology",
                    "Gastroenterology",
                    "Oncology",
                    "Vaccines",
                    "Haematology",
                    "Ophthalmology",
                    "Thrombosis",]:
        TA.objects.get_or_create(name=ta_name)

    default_ta = TA.objects.get(name='Psychiatry')
    for u in User.objects.all():
        u.therapeutic_areas.add(default_ta)
    Survey.objects.update(therapeutic_area_id=default_ta.pk)


def dummy(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0030_populate_survey_with_countnry_and_organization'),
        ('users', '__latest__'),
    ]

    operations = [
        migrations.RunPython(forward, dummy),
    ]
