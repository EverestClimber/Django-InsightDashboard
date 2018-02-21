from django.conf.urls import url
from django.views.generic import TemplateView

from survey import views

urlpatterns = [
    url(r'^instructions/$', views.InstructionsView.as_view(), name='instructions'),
    url(r'^list/$', views.SurveyListView.as_view(), name='list'),
    url(r'^definition/$', views.definition_view, name='definition'),
    url(r'^start/(?P<survey_id>\d+)/?$', views.start_view, name='start'),
    url(r'^clear/(?P<survey_id>\d+)/?$', views.delete_survey_data, name='delete_survey_data'),
    url(r'^pass/(?P<id>\d+)$', views.pass_view, name='pass'),
    url(r'^preview/(?P<survey_id>\d+)/$', views.preview_view, name='preview'),
    url(r'^thanks/(?P<survey_id>.+)/?$', TemplateView.as_view(template_name='survey/thanks.html'), name='thanks'),
]
