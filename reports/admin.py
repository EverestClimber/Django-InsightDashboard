from django.contrib import admin

from .models import Representation


@admin.register(Representation)
class RepresentationAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'get_questions', 'ordering', 'label1', 'label2', 'label3')
    search_fields = ('label1', 'label2', 'label3')

    def get_questions(self, obj):
        return "\n".join(["%s %s" % (q.pk, q) for q in obj.question.all()])
