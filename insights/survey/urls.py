from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^start/$', views.StartView.as_view(), name='start')
]