from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView

from survey.models import Survey

from .models import SurveyStat, OrganizationStat, QuestionStat
from .evaluators import LastEvaluator, TotalEvaluator


class ReportsView(LoginRequiredMixin, TemplateView):
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
        kwargs['organization_stat'] = OrganizationStat.objects.filter(survey=survey, country_id=country_id)

        QuestionStat.report_type = kwargs['report_type']

        kwargs['question_stat'] = []
        for qs in QuestionStat.objects.filter(survey=survey, country_id=country_id):
            if (qs.vars):
                kwargs['question_stat'].append(qs)

        return super(self.__class__, self).get_context_data(**kwargs)


@login_required()
def update_stat(request):
    if 'total' in request.GET:
        evaluator = TotalEvaluator
    else:
        evaluator = LastEvaluator
    evaluator.process_answers()
    return HttpResponse('console.log("stat was successfully updated");', "application/javascript")


@staff_member_required
def recalculate(request):
    TotalEvaluator.process_answers()
    return render(request, 'reports/recalculate.html', {'evaluator_messages': TotalEvaluator.messages})

@staff_member_required
def update_vars(request):
    LastEvaluator.process_answers()
    return render(request, 'reports/update_vars.html', {'evaluator_messages': LastEvaluator.messages})
