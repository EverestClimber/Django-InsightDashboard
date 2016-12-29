from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.generic import FormView, CreateView
from django import forms

from survey.models import Response, Survey
from survey.forms import StartSurveyForm, StartForm

class StartView(CreateView):
    model = Response
    fields = ['region', 'organization']
    success_url = '/survey/questions/'
    template_name = 'survey/start.html'

    def form_valid(self, form):
        user = self.request.user
        form.instance.user = user
        return super(StartView, self).form_valid(form)

@login_required
def start_view(request):


    if request.user.country is None:
        raise ValueError('User country is not set')

    def get_choices_from_object_manager(object_manager):
        objects = object_manager.all()
        if len(objects):
            choices = [(region.pk, region.name) for region in objects]
        else:
            choices = []
        return choices

    regions = request.user.country.region_set.all()
    if len(regions):
        region_choices = [(region.pk, region.name) for region in regions]
    else:
        region_choices = []


    surveys = Survey.objects.filter(active=True).all()

    if len(surveys):
        survey_choices = [(survey.pk, survey.name) for survey in surveys]
    else:
        survey_choices = []

    form = StartForm(request.POST or None, region_choices=region_choices)


    # form['organization'].choices = (('', '---'), (1, 1), (2, 3))
    # form['survey'].choices = (('', '---'), (1, 1), (2, 3))

    if request.method == 'POST':
        if form.is_valid():
            return HttpResponseRedirect('/thanks/')

    return render(request, 'survey/start.html', {'form': form})
