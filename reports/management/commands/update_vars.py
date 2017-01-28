from django.core.management.base import BaseCommand

from reports.evaluators import LastEvaluator

class Command(BaseCommand):
    help = 'Update stat vars from stat data'

    def handle(self, *args, **options):
        LastEvaluator.process_answers()
        # for q in QuestionStat.objects.all():
        #     q.update_vars()
        #     q.save()
