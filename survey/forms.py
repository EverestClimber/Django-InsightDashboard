from django import forms
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

        surveys = Survey.objects.get_active()
        if survey_id is not None:
            surveys = surveys.filter(pk=survey_id)
        survey_choices = [(survey.pk, survey.name) for survey in surveys]
        survey_choices_len = len(survey_choices)
        if survey_choices_len > 1:
            # survey_choices = [('', '---')] + survey_choices
            self.fields["survey"] = forms.ChoiceField(choices=survey_choices, widget=FancyRadioSelect)
        elif survey_choices_len == 1:
            self.fields['survey'] = forms.IntegerField(initial=survey_choices[0][0], widget=forms.HiddenInput())
        else:
            raise ValueError('There is no surveys yet, please add one')

        organizations = Organization.objects.all()
        organization_choices = [(organization.pk, organization.name) for organization in organizations]
        if len(organization_choices):
            # organization_choices = [('', '---')] + organization_choices
            self.fields["organization"] = forms.ChoiceField(choices=organization_choices, widget=FancyRadioSelect, label='Organization')
        else:
            raise ValueError('There is no organizations yet, please add one')

    def clean_survey(self):
        survey_id = self.cleaned_data['survey']
        if not Survey.objects.get(pk=survey_id).is_active():
            raise ValidationError('Cannot start inactive survey')
        return survey_id

