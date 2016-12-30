from django.db import models
from insights.users.models import User, Country
import jsonfield


class Region(models.Model):
    name = models.CharField('Region name', max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    def __str__(self):
        return self.name


class Organization(models.Model):
    name = models.CharField('Organization name', max_length=100)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    def __str__(self):
        return self.name


# class HCPCategory(models.Model):
#     name = models.CharField('Name of HCP', max_length=100)
#     created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)
#
#     class Meta:
#         verbose_name = 'Category of HCP'


class Question(models.Model):

    TYPE_TWO_DEPENDEND_FIELDS = 1
    TYPE_YES_NO = 2
    TYPE_MULTISELECT_WITH_OTHER = 3
    TYPE_MULTISELECT_ORDERED = 4
    TYPE_DEPENDEND_QUESTION = 11

    TYPE_CHOICES = (
        (TYPE_TWO_DEPENDEND_FIELDS, 'Two dependend fields'),
        (TYPE_YES_NO, 'For "yes" or "no" answers'),
        (TYPE_MULTISELECT_WITH_OTHER, 'Unordered multiselect with "Other" option'),
        (TYPE_MULTISELECT_ORDERED, 'Multiselect with ordering and "Other" option'),
        (TYPE_DEPENDEND_QUESTION, 'Dependend question for TYPE_TWO_DEPENDEND_FIELDS type'),
    )

    FIELD_PERCENT = 1
    FIELD_NUMBER = 2
    FIELD_CHOICES = (
        (FIELD_PERCENT, 'Field with percents'),
        (FIELD_NUMBER, 'Field number'),
    )

    DEPENDENCY_INCLUSION = 1
    DEPENDENCY_CONTEXTUAL = 2

    DEPENDENCY_CHOICES = (
        (DEPENDENCY_INCLUSION, 'Question is included to other question with TYPE_TWO_DEPENDEND_FIELDS type'),
        (DEPENDENCY_CONTEXTUAL, 'Question availability depends of other question'),
    )

    type = models.PositiveIntegerField('Question Type', choices=TYPE_CHOICES)
    field = models.PositiveIntegerField('Field Type', null=True, blank=True, choices=FIELD_CHOICES)
    text = models.CharField('Question text', max_length=1000)
    depends_of = models.ForeignKey('self', null=True, blank=True)
    dependency_type = models.PositiveIntegerField('Dependency Type', null=True, blank=True, choices=DEPENDENCY_CHOICES)
    script = models.CharField('Additional script', max_length=5000, null=True, blank=True)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.text


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.CharField('Option value', max_length=200)
    ordering = models.PositiveIntegerField('Order', default=0)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    class Meta:
        ordering = ['question_id', 'ordering', 'created_at']


    def __str__(self):
        return self.value


class Survey(models.Model):
    name = models.CharField('Name of survey', max_length=100)
    active = models.BooleanField('Is survey active or not', default=False, db_index=True)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    def __str__(self):
        return self.name


class SurveyItem(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    question = models.ForeignKey(Question)
    ordering = models.PositiveIntegerField('Order', default=0)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    class Meta:
        ordering = ['survey_id', 'ordering', 'created_at']
        verbose_name = 'Survey Item'

    def __str__(self):
        return "%s/%s" % (self.ordering, self.pk)

class HCPCategory(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    class Meta:
        verbose_name = 'Category of HCP'
        verbose_name_plural = 'Categories of HCP'

class Response(models.Model):
    user = models.ForeignKey(User)
    country = models.ForeignKey(Country)
    region = models.ForeignKey(Region, null=True, blank=True)
    organization = models.ForeignKey(Organization)
    hcp_category = models.ForeignKey(HCPCategory)
    survey = models.ForeignKey(Survey)
    data = jsonfield.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s - %s Response" % (self.pk, self.created_at)

