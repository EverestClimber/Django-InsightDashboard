from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.views.generic import TemplateView

from insights.users.models import Country
from survey.models import Survey

from .models import SurveyStat, OrganizationStat, QuestionStat
from .evaluators import LastEvaluator, TotalEvaluator


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/main.html'
    country_dict = {}

    def get_context_data(self, **kwargs):

        survey = Survey.objects.filter(pk=kwargs['survey_id']).first()

        if not survey:
            raise ValueError('There is no active surveys')

        if kwargs['country'] in ('europe', 'all'):
            country_id = None
            country = None
        else:
            try:
                country_id = int(kwargs['country'])
                country = Country.objects.get(pk=country_id)
            except ValueError:
                if kwargs['country'] in ReportsView.country_dict:
                    country = ReportsView.country_dict[kwargs['country']]
                else:
                    country = Country.objects.get(slug=kwargs['country'])
            if country:
                country_id = country.pk
                ReportsView.country_dict[country.slug] = country
            else:
                raise Http404("There is no country %s" % kwargs['country'])

        kwargs['country'] = country
        kwargs['survey_stat'] = SurveyStat.objects.filter(survey=survey, country_id=country_id).last()
        kwargs['organization_stat'] = OrganizationStat.objects.filter(survey=survey, country_id=country_id)

        QuestionStat.report_type = kwargs['report_type']

        kwargs['question_stat'] = []
        for qs in QuestionStat.objects.filter(survey=survey, country_id=country_id):
            kwargs['question_stat'].append(qs)

        ctx = super(self.__class__, self).get_context_data(**kwargs)
        ctx['survey'] = survey
        return ctx


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
