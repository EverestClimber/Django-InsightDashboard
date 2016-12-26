from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class StartView (LoginRequiredMixin, TemplateView):
    template_name = 'survey/start.html'
