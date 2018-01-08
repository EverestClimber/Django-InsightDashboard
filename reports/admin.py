from django.contrib import admin

from .models import Representation


@admin.register(Representation)
class RepresentationAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'question', 'ordering', 'label1', 'label2', 'label3')
    search_fields = ('label1', 'label2', 'label3')
