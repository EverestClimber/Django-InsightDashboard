from django.views.generic import TemplateView
from django.conf.urls import url

from .views import ReportsView


urlpatterns = [
    url(r'^advanced/$', ReportsView.as_view(), name='advanced'),
    url(r'^advanced/(?P<country>\d+)$', ReportsView.as_view(), name='advanced_country'),
    url(r'^basic/$', ReportsView.as_view(), name='basic'),
    url(r'^basic/(?P<country>\d+)$$', ReportsView.as_view(), name='basic_country'),

]
