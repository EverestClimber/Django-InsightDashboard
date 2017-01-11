from django.conf.urls import url
from django.views.generic import TemplateView

from survey import views

urlpatterns = [
    url(r'^instructions/$', views.InstructionsView.as_view(), name='instructions'),
    url(r'^definition/$', views.definition_view, name='definition'),
    url(r'^start/$', views.start_view, name='start'),
    url(r'^pass/(?P<id>\d+)$', views.pass_view, name='pass'),
    url(r'^thanks/$', TemplateView.as_view(template_name='survey/thanks.html'), name='thanks'),
]
