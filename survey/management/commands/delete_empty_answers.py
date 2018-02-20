from django.core.management.base import BaseCommand, CommandError

from survey.models import Answer


class Command(BaseCommand):
    help = 'Deletes Answers with empty body'

    def handle(self, *args, **options):
        deleted =  Answer.objects.filter(body='').delete()
        return "Deleted {0} answers".format(deleted[0])
