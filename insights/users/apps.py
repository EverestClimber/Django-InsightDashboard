from django.apps import AppConfig
from django.db.models.signals import post_migrate


def ensure_permission_groups(sender, **kwargs):
    from django.contrib.auth.models import Permission, Group
    g = Group.objects.get_or_create(name='Otsuka Administrator')[0]
    g.permissions.set(
        Permission.objects.filter(codename__in=('add_country', 'change_country', 'delete_country',
                                                'add_user', 'change_user', 'delete_user')))


class UsersConfig(AppConfig):
    name = 'insights.users'
    verbose_name = "Users"

    def ready(self):
        post_migrate.connect(ensure_permission_groups, sender=self)
