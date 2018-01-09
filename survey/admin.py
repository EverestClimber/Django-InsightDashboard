from querystring_parser import parser as queryparser

from django.contrib import admin
from django.utils.translation import gettext as _
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe, mark_for_escaping
from .models import (Region, Organization, Question, QuestionTranslation,
                     Option, Survey, Answer, HCPCategory)
from reports.models import Representation
import nested_admin


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


class QuestionTranslationInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        has_lang = {}
        for form in self.forms:
            try:
                if form.cleaned_data and not form.cleaned_data['DELETE']:
                    lang = form.cleaned_data['lang'].pk
                    if lang in has_lang:
                        raise forms.ValidationError(_('Only one translation per language is allowed'))
                    has_lang[lang] = True
            except AttributeError:
                pass


class QuestionTranslationInline(admin.StackedInline):
    formset = QuestionTranslationInlineFormset
    model = QuestionTranslation
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionTranslationInline]
    list_display = ('id', 'ordering', 'type', 'field', 'text', 'created_at', 'depends_of', 'dependency_type')
    search_fields = ['text']
    form = QuestionModelForm


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'value', 'ordering', 'created_at')
    search_fields = ['question']


class QTranslationInline(nested_admin.NestedStackedInline):
    formset = QuestionTranslationInlineFormset
    model = QuestionTranslation
    extra = 0


class OptionInline(nested_admin.NestedStackedInline):
    model = Option
    extra = 0


class RepresentationInline(nested_admin.NestedStackedInline):
    model = Representation
    extra = 0


class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    extra = 0
    inlines = [QTranslationInline, OptionInline, RepresentationInline]


class SurveyForm(forms.ModelForm):
    def clean_organizations(self):
        Survey.validate_organizations(self.cleaned_data['organizations'])
        return self.cleaned_data['organizations']


@admin.register(Survey)
class SurveyAdmin(nested_admin.NestedModelAdmin):
    list_display = ('name', 'active', 'created_at')
    search_fields = ['name']
    form = SurveyForm
    prepopulated_fields = {'slug': ('name',), }
    inlines = [QuestionInline]

    class Media:
        css = {
            'all': ('css/custom_admin.css',)
        }


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'country', 'region', 'organization', 'survey', 'created_at', 'has_data', 'get_data')

    def has_data(self, item):
        return bool(item.body)

    def get_data(self, item):
        data = queryparser.parse(item.body)
        if 'data' not in data:
            return None

        items = list(data['data'].items())
        items.sort()
        out = ''
        for i, dt in items:
            out += "%s %s<br>" % (i, mark_for_escaping(dt))
        return mark_safe(out)

    has_data.boolean = True


@admin.register(HCPCategory)
class HCPCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
