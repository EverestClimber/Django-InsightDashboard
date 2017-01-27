from django.views.generic import TemplateView
from django.conf.urls import url

from .views import ReportsView, update_stat, recalculate, update_vars


urlpatterns = [

    url(r'^advanced/$', TemplateView.as_view(template_name='reports/advanced.html'), name='advanced'),
    url(r'^basic/$', TemplateView.as_view(template_name='reports/basic.html'), name='basic'),

    url(r'^advanced/europe$', ReportsView.as_view(), {'report_type': 'advanced'}, name='advanced_europe'),
    url(r'^advanced/(?P<country>\d+)$', ReportsView.as_view(), {'report_type': 'advanced'}, name='advanced_country'),
    url(r'^basic/europe$', ReportsView.as_view(), {'report_type': 'basic'}, name='basic_europe'),
    url(r'^basic/(?P<country>\d+)$', ReportsView.as_view(), {'report_type': 'basic'}, name='basic_country'),

    url(r'^update-stat/$', update_vars, name='update_vars'),
    url(r'^recalculate/$', recalculate, name='recalculate'),


]
