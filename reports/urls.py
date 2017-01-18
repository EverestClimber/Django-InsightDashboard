from django.views.generic import TemplateView
from django.conf.urls import url


urlpatterns = [
    url(r'^advanced/$', TemplateView.as_view(template_name='reports/advanced.html'), name='advanced'),
    url(r'^basic/$', TemplateView.as_view(template_name='reports/basic.html'), name='basic'),

]
