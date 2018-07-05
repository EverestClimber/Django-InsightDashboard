from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

from insights.users.models import Country
from survey.models import Survey

from .models import SurveyStat, OrganizationStat, QuestionStat
from .evaluators import LastEvaluator, TotalEvaluator


def get_by_slug_or_pk(cls, obj_id):
    try:
        return cls.objects.get(slug=obj_id)
    except cls.DoesNotExist:
        try:
            return get_object_or_404(cls, pk=obj_id)
        except ValueError:
            raise Http404


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/main.html'
    country_dict = {}

    def get(self, *args, **kwargs):
        if kwargs['country'] in ('europe', 'all'):
            country_id = None
            country = None
        else:
            country = get_by_slug_or_pk(Country, kwargs['country'])
            if not country.use_in_reports:
                kwargs['country'] = 'all'
                return HttpResponseRedirect(reverse('reports:advanced', kwargs=kwargs))
            country_id = country.pk

        self.country_id = country_id
        self.country = country

        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):

        survey = get_by_slug_or_pk(Survey, kwargs['survey_id'])
        prepare_charts = self.request.GET.get('prepareCharts', 'false')

        ctx = super(self.__class__, self).get_context_data(**kwargs)

        ctx['survey'] = survey
        ctx['country'] = self.country
        ctx['survey_stat'] = SurveyStat.objects.filter(survey=survey, country_id=self.country_id).last()
        ctx['organization_stat'] = OrganizationStat.objects.filter(survey=survey, country_id=self.country_id)
        ctx['prepare_charts'] = prepare_charts
        ctx['preview_mode'] = prepare_charts == 'true'
        ctx['question_stat'] = list(QuestionStat.objects.filter(survey=survey, country_id=self.country_id))

        return ctx


@login_required()
def update_stat(request, survey_id):
    survey = get_by_slug_or_pk(Survey, survey_id)
    evaluator = TotalEvaluator if 'total' in request.GET else LastEvaluator
    evaluator.process_answers(survey)
    return HttpResponse('console.log("stat was successfully updated");', "application/javascript")


@staff_member_required
def recalculate(request):
    messages = []
    for survey in Survey.objects.prefetch_related('organizations', 'countries').all():
        evaluator = TotalEvaluator.process_answers(survey)
        messages += evaluator.messages
    return render(request, 'reports/recalculate.html', {'evaluator_messages': messages})


@staff_member_required
def update_vars(request):
    messages = []
    for survey in Survey.objects.all():
        evaluator = LastEvaluator.process_answers(survey)
        messages += evaluator.messages
    return render(request, 'reports/update_vars.html', {'evaluator_messages': messages})
