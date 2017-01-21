from django.db import models
from insights.users.models import User, Country



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

    TYPE_TWO_DEPENDEND_FIELDS = 'type_two_dependend_fields'
    TYPE_YES_NO = 'type_yes_no'
    TYPE_MULTISELECT_WITH_OTHER = 'type_multiselect_with_other'
    TYPE_MULTISELECT_ORDERED = 'type_multiselect_ordered'
    TYPE_DEPENDEND_QUESTION = 'type_dependeend_question'
    TYPE_SIMPLE_INPUT = 'type_simple_input'
    TYPE_YES_NO_JUMPING = 'type_yes_no_jumping'

    TYPE_CHOICES = (
        (TYPE_TWO_DEPENDEND_FIELDS, 'Two dependend fields'),
        (TYPE_YES_NO, 'For "yes" or "no" answers'),
        (TYPE_MULTISELECT_WITH_OTHER, 'Unordered multiselect with "Other" option'),
        (TYPE_MULTISELECT_ORDERED, 'Multiselect with ordering and "Other" option'),
        (TYPE_DEPENDEND_QUESTION, 'Dependend question for TYPE_TWO_DEPENDEND_FIELDS type'),
        (TYPE_SIMPLE_INPUT, 'Simple input field'),
        (TYPE_YES_NO_JUMPING, 'Yes-No, that allow to jump to the certain question'),
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

    type = models.CharField('Question Type', choices=TYPE_CHOICES, max_length=50)
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

    def get_type_template_name(self):
        return "survey/question_types/%s.html" % self.type

    def get_subquestion(self):
        if self.type != self.TYPE_TWO_DEPENDEND_FIELDS:
            raise ValueError("Question type doesn't support subuquestions")
        dependend = self.question_set.filter(type=self.TYPE_DEPENDEND_QUESTION)
        if not len(dependend):
            raise ValueError("Question has no subqueries")

        return dependend.first()


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
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='survey_items')
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


class Answer(models.Model):
    user = models.ForeignKey(User)
    country = models.ForeignKey(Country)
    region = models.ForeignKey(Region, null=True, blank=True)
    organization = models.ForeignKey(Organization)
    hcp_category = models.ForeignKey(HCPCategory, null=True, blank=True)
    survey = models.ForeignKey(Survey)
    body = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    is_updated = models.BooleanField(db_index=True, default=False)

    def __str__(self):
        return "%s - %s Response" % (self.pk, self.created_at)

