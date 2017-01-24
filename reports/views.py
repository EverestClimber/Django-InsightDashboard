from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.generic import TemplateView

from survey.models import Survey

from .models import SurveyStat, OrganizationStat, LastEvaluator, TotalEvaluator


class ReportsView(TemplateView):
    template_name = 'reports/main.html'

    def get_context_data(self, **kwargs):

        survey = Survey.objects.filter(active=True).first()

        if not survey:
            raise ValueError('There is no active surveys')

        if 'country' in kwargs:
            country_id = int(kwargs['country'])
        else:
            country_id = None

        kwargs['survey_stat'] = SurveyStat.objects.filter(survey=survey, country_id=country_id).last()
        kwargs['organization_stat'] = OrganizationStat.objects.filter(survey=survey, country_id=country_id)\
            .order_by('report_order')

        return super(self.__class__, self).get_context_data(**kwargs)


@login_required()
def update_stat(request):
    if 'total' in request.GET:
        evaluator = TotalEvaluator
    else:
        evaluator = LastEvaluator
    evaluator.process_answers()
    return HttpResponse('console.log("stat was successfully updated");', "application/javascript")

