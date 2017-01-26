from django.core.management.base import BaseCommand

from reports.evaluators import TotalEvaluator

class Command(BaseCommand):
    help = 'Recalculate all data from answers'

    def handle(self, *args, **options):
        TotalEvaluator.process_answers()
