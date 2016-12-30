from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.generic import FormView, CreateView
from django.core.urlresolvers import reverse

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

    regions = request.user.country.region_set.all()
    if len(regions):
        region_choices = [(region.pk, region.name) for region in regions]
    else:
        region_choices = []

    form = StartForm(request.POST or None, region_choices=region_choices)


    # form['organization'].choices = (('', '---'), (1, 1), (2, 3))
    # form['survey'].choices = (('', '---'), (1, 1), (2, 3))

    if request.method == 'POST':
        if form.is_valid():
            response = Response(
                user=request.user,
                country=request.user.country,
                organization_id=form.cleaned_data['organization'],
                hcp_category_id=form.cleaned_data['hcp'],
                survey_id=form.cleaned_data['survey']
            )
            if form.cleaned_data['region']:
                response.region_id = form.cleaned_data['region']
            response.save()
            return HttpResponseRedirect(reverse('survey:pass', kwargs={'id': response.pk}))


    return render(request, 'survey/start.html', {'form': form})

@login_required
def pass_view(request):
    if request.method == 'POST':
        pass
    return render(request, 'survey/start.html', {'form': form})