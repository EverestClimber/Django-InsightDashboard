from django.views.generic import TemplateView
from django.conf.urls import url

from .views import ReportsView, update_stat, recalculate, update_vars


urlpatterns = [

    # url(r'^advanced/$', TemplateView.as_view(template_name='reports/advanced.html'), name='advanced'),
    # url(r'^basic/$', TemplateView.as_view(template_name='reports/basic.html'), name='basic'),

    url(r'^advanced/(?P<survey_id>\d+)/(?P<country>.+)$', ReportsView.as_view(), {'report_type': 'advanced'}, name='advanced'),
    url(r'^basic/(?P<country>.+)$', ReportsView.as_view(), {'report_type': 'basic'}, name='basic'),

    url(r'^update-vars/$', update_vars, name='update_vars'),
    url(r'update-stat/$', update_stat, name='update_stat'),
    url(r'^recalculate/$', recalculate, name='recalculate'),


]
