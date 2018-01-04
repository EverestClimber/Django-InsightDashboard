from django.apps import AppConfig
from django.db.models.signals import post_migrate


def ensure_permission_groups(sender, **kwargs):
    from django.contrib.auth.models import Permission, Group
    g = Group.objects.get_or_create(name='Otsuka User')[0]
    g.permissions.set(
        Permission.objects.filter(codename__in=('add_answer', 'change_answer', 'delete_answer')))


class SurveyConfig(AppConfig):
    name = 'survey'

    def ready(self):
        post_migrate.connect(ensure_permission_groups, sender=self)
