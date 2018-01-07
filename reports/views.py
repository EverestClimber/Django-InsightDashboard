from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

from insights.users.models import Country
from survey.models import Survey

from .models import SurveyStat, OrganizationStat, QuestionStat
from .evaluators import LastEvaluator, TotalEvaluator


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/main.html'
    country_dict = {}

    def get_context_data(self, **kwargs):

        try:
            survey = Survey.objects.get(slug=kwargs['survey_id'])
        except Survey.DoesNotExist:
            try:
                survey = get_object_or_404(Survey, pk=kwargs['survey_id'])
            except ValueError:
                raise Http404

        if kwargs['country'] in ('europe', 'all'):
            country_id = None
            country = None
        else:
            try:
                country = Country.objects.get(slug=kwargs['country'])
            except Country.DoesNotExist:
                try:
                    country = get_object_or_404(Country, pk=kwargs['country'])
                except ValueError:
                    raise Http404
            country_id = country.pk

        ctx = super(self.__class__, self).get_context_data(**kwargs)

        ctx['survey'] = survey
        ctx['country'] = country
        ctx['survey_stat'] = SurveyStat.objects.filter(survey=survey, country_id=country_id).last()
        ctx['organization_stat'] = OrganizationStat.objects.filter(survey=survey, country_id=country_id)

        ctx['question_stat'] = []
        for qs in QuestionStat.objects.filter(survey=survey, country_id=country_id):
            ctx['question_stat'].append(qs)

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
