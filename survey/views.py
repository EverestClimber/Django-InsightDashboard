from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.generic import FormView, CreateView
from django.core.urlresolvers import reverse

from survey.models import Answer
from survey.forms import StartForm

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
            response = Answer(
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
def pass_view(request, id):
    answer = Answer.objects.select_related('survey').get(pk=id)
    if answer.data:
        return HttpResponseRedirect(reverse('survey:start'))

    if answer.user_id != request.user.pk:
        return HttpResponseRedirect(reverse('survey:start'))


    if request.method == 'POST':
        answer.data = dict(request.POST)
        answer.save()
        return HttpResponseRedirect(reverse('survey:thanks'))


    items = answer.survey.survey_items.all().prefetch_related('question__option_set')
    return render(request, 'survey/pass.html', {'items': items})