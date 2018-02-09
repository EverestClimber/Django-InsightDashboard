from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView, ListView
from django.utils.translation import ugettext_lazy as _

from survey.models import Answer, Survey
from survey.forms import StartForm, PreviewForm


@login_required
def definition_view(request):
    if request.COOKIES.get(InstructionsView.cookie_name):
        return render(request, 'survey/definition.html')
    else:
        return HttpResponseRedirect(reverse('survey:instructions'))


class InstructionsView(LoginRequiredMixin, TemplateView):
    template_name = 'survey/instructions.html'
    cookie_name = 'instructions_was_viewed2'

    def get(self, request, *args, **kwargs):
        response = super(self.__class__, self).get(self, request, *args, **kwargs)
        response.set_cookie(self.cookie_name, True, 365*24*60*60)
        return response


class SurveyListView(LoginRequiredMixin, ListView):
    model = Survey
    template_name = 'survey/list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return (qs.get_active(), qs.get_inactive())

    def get(self, *args, **kwargs):
        if not self.request.COOKIES.get(InstructionsView.cookie_name):
            return HttpResponseRedirect(reverse('survey:instructions'))
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        return dict(
            super(SurveyListView, self).get_context_data(),
            has_permissions=self.has_permissions()
        )

    def has_permissions(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return 'Otsuka Administrator' in user.get_flags()

    def post(self, *args, **kwargs):

        if "survey_id" in self.request.POST and self.has_permissions():
            survey_id = self.request.POST['survey_id']
            try:
                survey = Survey.objects.get(pk=survey_id)
                survey.clear()
                messages.success(self.request, _('The survey data is cleared successfully.'))
            except Survey.DoesNotExist:
                messages.warning(
                    self.request,
                    _('Survey with id=%(survey_id)s does not exist.') % {'survey_id': survey_id})
        return HttpResponseRedirect(reverse('survey:list'))


@login_required
@permission_required('survey.add_answer', raise_exception=True)
def start_view(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if not survey.is_active():
        raise ValueError("Cannot start inactive survey")
    if request.user.country is None:
        raise ValueError('User country is not set')
    if not survey.countries.filter(pk=request.user.country_id).exists():
        raise ValueError('The survey is not available in {}'.format(request.user.country.name))

    regions = request.user.country.region_set.all()
    if len(regions):
        region_choices = [(region.pk, region.name) for region in regions]
    else:
        region_choices = []

    form = StartForm(request.POST or None, region_choices=region_choices, survey_id=survey_id)

    if request.method == 'POST':
        if form.is_valid():
            response = Answer(
                user=request.user,
                country=request.user.country,
                organization_id=form.cleaned_data['organization'],
                survey_id=form.cleaned_data['survey']
            )
            if form.cleaned_data['region']:
                response.region_id = form.cleaned_data['region']
            response.save()
            return HttpResponseRedirect(reverse('survey:pass', kwargs={'id': response.pk}))

    return render(request, 'survey/start.html', {'form': form, 'survey': survey})


@login_required
@permission_required('survey.add_answer', raise_exception=True)
def preview_view(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if request.user.country is None:
        raise ValueError('User country is not set')
    if not survey.countries.filter(pk=request.user.country_id).exists():
        raise ValueError('The survey is not available in {}'.format(request.user.country.name))

    regions = request.user.country.region_set.all()
    if len(regions):
        region_choices = [(region.pk, region.name) for region in regions]
    else:
        region_choices = []

    form = PreviewForm(request.POST or None, region_choices=region_choices, survey_id=survey_id)

    if request.method == 'POST':
        if form.is_valid():
            response = Answer(
                user=request.user,
                country=request.user.country,
                organization_id=form.cleaned_data['organization'],
                survey_id=form.cleaned_data['survey']
            )
            if form.cleaned_data['region']:
                response.region_id = form.cleaned_data['region']
            response.save()
            return HttpResponseRedirect(reverse('survey:pass_preview', kwargs={'id': response.pk}))

    return render(request, 'survey/preview.html', {'form': form, 'survey': survey})



@login_required
@permission_required('survey.add_answer', raise_exception=True)
def pass_view(request, id):
    answer = Answer.objects.select_related('survey').get(pk=id)
    if answer.body:
        return HttpResponseRedirect(reverse('survey:list'))

    if answer.user_id != request.user.pk:
        return HttpResponseRedirect(reverse('survey:list'))

    if request.method == 'POST':
        answer.body = request.POST.urlencode()
        answer.save()
        return HttpResponseRedirect(reverse('survey:thanks', kwargs={'survey_id': answer.survey.slug}))

    questions = answer.survey.questions.prefetch_related('options')
    return render(request, 'survey/pass.html', {'questions': questions})


@login_required
@permission_required('survey.add_answer', raise_exception=True)
def pass_preview_view(request, id):
    answer = Answer.objects.select_related('survey').get(pk=id)
    if answer.body:
        return HttpResponseRedirect(reverse('survey:list'))

    if answer.user_id != request.user.pk:
        return HttpResponseRedirect(reverse('survey:list'))

    if request.method == 'POST':
        answer.body = request.POST.urlencode()
        answer.save()
        return HttpResponseRedirect(reverse('survey:thanks', kwargs={'survey_id': answer.survey.slug}))

    questions = answer.survey.questions.prefetch_related('options')
    return render(request, 'survey/pass_preview.html', {'questions': questions})

