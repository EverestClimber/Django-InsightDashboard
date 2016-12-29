from django.conf.urls import url

from survey import views

urlpatterns = [
    url(r'^start/$', views.start_view, name='start')
]