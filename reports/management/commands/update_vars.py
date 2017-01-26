from django.core.management.base import BaseCommand

from reports.models import QuestionStat

class Command(BaseCommand):
    help = 'Update stat vars from stat data'

    def handle(self, *args, **options):
        for q in QuestionStat.objects.all():
            q.update_vars()
            q.save()
