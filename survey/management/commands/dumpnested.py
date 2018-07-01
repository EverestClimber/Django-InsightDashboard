# -*- coding: utf-8 -*-
"""
    Dump out objects and all nested associations.
"""
from __future__ import absolute_import, print_function, unicode_literals

import sys

from django.contrib.admin.utils import NestedObjects
from django.core import serializers
from django.core.management import BaseCommand
from django.db import router
from django.db.models import Model
from django.apps import apps


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('args', metavar='[app_label.ModelName.id1,id2,id3...]', nargs='*',
                            help='Specify assessments by their ID.')
        parser.add_argument('--indent', default=None, dest='indent', type=int,
                            help='Specifies the indent level to use when pretty-printing output.')

    def handle(self, *args, **options):
        indent = options.get('indent')

        self.items = []

        for arg in args:
            app_label, model, ids = arg.split('.')
            Model = apps.get_model(app_label, model)
            for id in ids.split(','):
                self.dump_object(Model.objects.filter(pk=id))

        serializers.serialize('json',
                              self.items,
                              indent=indent,
                              stream=sys.stdout,
                              use_natural_foreign_keys=True,
                              use_natural_primary_keys=True)

    def dump_object(self, obj):
        using = router.db_for_write(obj.__class__)

        collector = NestedObjects(using=using)
        collector.collect(obj)

        objs = collector.nested(lambda x: x)

        objs = list(zip(objs[::2], objs[1::2]))

        self.get_objects(objs)

    def get_objects(self, item):
        if isinstance(item, Model):
            self.items.append(item)
        elif isinstance(item[0], Model):
            for _item in item:
                self.get_objects(_item)
        else:
            for obj, children in item:
                self.items.append(obj)
                # items.append(obj)
                self.get_objects(children)
