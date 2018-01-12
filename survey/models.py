from django.db import models
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from insights.users.models import User, Country, Language, TherapeuticArea
from django.utils import timezone


class Region(models.Model):
    name = models.CharField('Region name', max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)
    ordering = models.PositiveIntegerField('Order in reports', default=1, blank=True, db_index=True)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return self.name


class Organization(models.Model):
    name = models.CharField('Organization name', max_length=100, default='')
    name_plural = models.CharField('Organization name in plural form', max_length=100, default='')
    name_plural_short = models.CharField('Short organization name in plural form', max_length=100, default='')
    label1 = models.CharField('Label1 for reports', max_length=200, default='')
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)
    ordering = models.PositiveIntegerField('Order in reports', default=1, blank=True, db_index=True)

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return self.name


class SurveyQuerySet(models.QuerySet):
    def get_active(self):
        now = timezone.now()
        return self.filter(active=True, start__lte=now, end__gte=now)

    def get_inactive(self):
        now = timezone.now()
        q = models.Q(active=False) | models.Q(start__gt=now) | models.Q(end__lt=now)
        return self.filter(q)


class Survey(models.Model):
    MAX_ORGANIZATIONS = 3

    objects = SurveyQuerySet.as_manager()

    name = models.CharField(_('Name of survey'), max_length=100)
    slug = models.SlugField(_('Survey slug'), unique=True)
    therapeutic_area = models.ForeignKey(TherapeuticArea, on_delete=models.CASCADE, null=True)
    countries = models.ManyToManyField(Country, related_name="surveys")
    organizations = models.ManyToManyField(Organization, related_name="surveys", blank=True)
    active = models.BooleanField('Is active', default=False, db_index=True)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)
    start = models.DateTimeField(_('Starts at'))
    end = models.DateTimeField(_('Ends at'))

    def get_last_answer(self):
        try:
            return self.answers.order_by('-created_at')[0]
        except IndexError:
            return None

    def is_active(self):
        now = timezone.now()
        return self.active and self.start <= now <= self.end

    def __str__(self):
        return self.name

    @classmethod
    def on_organizations_changed(cls, sender, **kwargs):
        cls.validate_organizations(kwargs['instance'].organizations)

    @classmethod
    def validate_organizations(cls, organizations):
        if organizations.count() > cls.MAX_ORGANIZATIONS:
            raise ValidationError(_('Cannot assign more than %(max_organizations)s organizations to survey')
                                  % {'max_organizations': cls.MAX_ORGANIZATIONS})

models.signals.m2m_changed.connect(Survey.on_organizations_changed, sender=Survey.organizations.through)


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
        (DEPENDENCY_CONTEXTUAL, 'Question availability depends on other question'),
    )

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions',
                               null=True, blank=True)
    ordering = models.PositiveIntegerField('Order', default=0)
    type = models.CharField('Question Type', choices=TYPE_CHOICES, max_length=50)
    field = models.PositiveIntegerField('Field Type', null=True, blank=True, choices=FIELD_CHOICES)
    text = models.CharField('Question text', max_length=1000)
    depends_on = models.ForeignKey('self', null=True, blank=True)
    available_if = models.CharField(_('Dependent question answer'), max_length=200, blank=True)
    dependency_type = models.PositiveIntegerField('Dependency Type', null=True, blank=True, choices=DEPENDENCY_CHOICES)
    script = models.CharField('Additional script', max_length=5000, null=True, blank=True)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    class Meta:
        ordering = ['survey_id', 'ordering', 'created_at']

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


class QuestionTranslation(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="translations")
    lang = models.ForeignKey(Language, on_delete=models.CASCADE)
    text = models.CharField('Question text', max_length=1000)

    def __str__(self):
        return "[{0.lang.name}] {0.text}".format(self)


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    value = models.CharField('Option value', max_length=200)
    ordering = models.PositiveIntegerField('Order', default=0)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    class Meta:
        ordering = ['question_id', 'ordering', 'created_at']

    def __str__(self):
        return self.value


class HCPCategory(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField('Datetime of creation', auto_now_add=True)

    class Meta:
        verbose_name = 'Category of HCP'
        verbose_name_plural = 'Categories of HCP'


class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    country = models.ForeignKey(Country)
    region = models.ForeignKey(Region, null=True, blank=True)
    organization = models.ForeignKey(Organization)
    hcp_category = models.ForeignKey(HCPCategory, null=True, blank=True)
    survey = models.ForeignKey(Survey, related_name="answers")
    body = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    is_updated = models.BooleanField(db_index=True, default=False)

    def __str__(self):
        return "%s - %s Response" % (self.pk, self.created_at)
