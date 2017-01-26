from django.contrib import admin
from django import forms
from .models import Region, Organization, Question, Option, Survey, SurveyItem, Answer, HCPCategory


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'created_at')
    search_fields = ['name']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'ordering', 'name', 'name_plural', 'name_plural_short', 'label1', 'created_at')
    search_fields = ['name']


class QuestionModelForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'
        widgets = {
            'text': forms.Textarea(),
            'script': forms.Textarea(),
        }


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'field', 'text', 'created_at', 'depends_of', 'dependency_type')
    search_fields = ['text']
    form = QuestionModelForm




@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'value', 'ordering', 'created_at')
    search_fields = ['question']


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'created_at')
    search_fields = ['name']


@admin.register(SurveyItem)
class SurveyItemAdmin(admin.ModelAdmin):
    list_display = ('survey', 'question', 'ordering', 'created_at')



@admin.register(Answer)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'region', 'organization', 'survey', 'created_at')


@admin.register(HCPCategory)
class HCPCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
