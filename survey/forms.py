from django import forms
from django.shortcuts import get_object_or_404
from .models import Answer, Survey, Organization
from .widgets import FancyRadioSelect


class StartSurveyForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['region', 'organization']


class StartForm(forms.Form):
    region = forms.ChoiceField('Region', required=False)
    organization = forms.ChoiceField('Organization', required=True)
    survey = forms.ChoiceField('Survey', required=True)

    def __init__(self, *args, **kwargs):
        region_choices = kwargs.pop('region_choices')
        survey_id = kwargs.pop('survey_id')

        super(StartForm, self).__init__(*args, **kwargs)

        if len(region_choices):
            # region_choices = [('', '---')] + region_choices
            self.fields["region"] = forms.ChoiceField(choices=region_choices, required=True, widget=FancyRadioSelect)
        else:
            self.fields['region'] = forms.IntegerField(widget=forms.HiddenInput(), initial=None, required=False)

        survey = get_object_or_404(Survey, pk=survey_id)
        self.fields['survey'] = forms.IntegerField(initial=survey.pk, widget=forms.HiddenInput())

        organizations = survey.organizations.all()
        organization_choices = [(organization.pk, organization.name) for organization in organizations]
        if len(organization_choices):
            self.fields["organization"] = forms.ChoiceField(choices=organization_choices,
                                                            widget=FancyRadioSelect,
                                                            label='Organization')
        else:
            raise ValueError('There are no organizations assigned to selected survey')

    def clean_survey(self):
        survey_id = self.cleaned_data['survey']
        if not Survey.objects.get(pk=survey_id).is_active():
            raise forms.ValidationError('Cannot start inactive survey')
        return survey_id
