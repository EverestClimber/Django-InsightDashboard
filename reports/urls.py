from django.views.generic import TemplateView
from django.conf.urls import url

from .views import ReportsView, update_stat, recalculate, update_vars


urlpatterns = [

    url(r'^(?P<survey_id>\d+)/(?P<country>.+)$', ReportsView.as_view(), name='advanced'),
    url(r'^(?P<survey_id>.+)/(?P<country>.+)$', ReportsView.as_view(), name='advanced'),

    url(r'^update-vars/$', update_vars, name='update_vars'),
    url(r'^update-stat/$', update_stat, name='update_stat'),
    url(r'^recalculate/$', recalculate, name='recalculate'),


]
