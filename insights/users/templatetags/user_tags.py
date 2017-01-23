from insights.users.models import Country
from django import template

register = template.Library()

@register.assignment_tag
def get_countries():
    return list(Country.objects.all())
