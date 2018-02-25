import django
django.setup()

from django.contrib.admin.utils import NestedObjects
from django.db import DEFAULT_DB_ALIAS
from django.core import serializers
from factory.django import get_model


Survey = get_model('survey', 'Survey')

restore_me = Survey.objects.filter(id=1)
collector = NestedObjects(using=DEFAULT_DB_ALIAS)
collector.collect(restore_me)


# This generates a hierarchical list of all of the objects related to the
# object that was deleted.  The same output that Django creates when it prompts
# you for confirmation to delete something.
result = collector.nested()
output = '['


def json_dump(obj):
    global output
    for model in obj:
        if not isinstance(model, list):
            # Ignore many to many tables as they are included in the primary
            # object serialization
            if "_" not in model.__class__.__name__:
                # Use Django's built in serializer, and strip off the array
                # brackets
                output += serializers.serialize("json", [model])[1:-1]
                # append a comma
                output += ","
        else:
            json_dump(model)


json_dump(result)
# remove the last comma and add the ending array bracket.
output = output[:-1] + "]"
with open("dump-survey-{}.json".format('1'), "w+") as dump:
    # dump it to a file
    dump.write(output)
