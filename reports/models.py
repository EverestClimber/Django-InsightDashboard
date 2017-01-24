import jsonfield

from django.db import models
from querystring_parser import parser as queryparser

from survey.models import Country, Survey, Organization, Answer, Question


class Stat(models.Model):
    country = models.ForeignKey(Country, blank=True, null=True)
    survey = models.ForeignKey(Survey, null=True)
    total = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.total)


class SurveyStat(Stat):
    last = models.DateTimeField(blank=True, null=True)


class OrganizationStat(Stat):
    organization = models.ForeignKey(Organization, null=True)
    ordering = models.PositiveIntegerField('Ordering in reports', default=1, blank=True, db_index=True)


class RepresentationTypeMixin(object):
    TYPE_AVERAGE_PERCENT = 'type_average_percent'
    TYPE_YES_NO = 'type_yes_no'
    TYPE_MULTISELECT_TOP = 'type_multiselect_top'

    TYPE_CHOICES = (
        (TYPE_AVERAGE_PERCENT, 'Average percent representation'),
        (TYPE_YES_NO, 'Representation for "yes" or "no" answers'),
        (TYPE_MULTISELECT_TOP, 'Top 1 and top 3 representation for ordered multiselect'),

    )
    type = models.CharField('Representation Type', choices=TYPE_CHOICES, max_length=50)


class Representation(RepresentationTypeMixin, models.Model):
    survey = models.ForeignKey(Survey)
    question = models.ForeignKey(Question)
    ordering = models.PositiveIntegerField('Ordering in reports', default=1, blank=True, db_index=True)
    label1 = models.CharField('Label 1', max_length=400, default='', blank=True)
    label2 = models.CharField('Label 2', max_length=400, default='', blank=True)
    label3 = models.CharField('Label 3', max_length=400, default='', blank=True)


class QuestionStat(RepresentationTypeMixin, models.Model):
    country = models.ForeignKey(Country, blank=True, null=True)
    survey = models.ForeignKey(Survey, null=True)
    representation = models.ForeignKey(Representation)
    data = jsonfield.JSONField()
    ordering = models.PositiveIntegerField('Ordering in reports', default=1, blank=True, db_index=True)


####################### Evaluators ###############################
class AbstractEvaluator(object):

    survey_stat = {}
    organization_stat = {}

    @staticmethod
    def get_answers():
        raise NotImplementedError


    @staticmethod
    def clear():
        raise NotImplementedError

    @classmethod
    def load_stat(cls):
        surveys = SurveyStat.objects.all()
        for survey in surveys:
            cls.survey_stat[(survey.survey_id, survey.country_id)] = survey

        orgs = OrganizationStat.objects.all()
        for org in orgs:
            cls.organization_stat[(org.survey_id, org.country_id, org.organization_id)] = org

    @classmethod
    def fill_out(cls):
        countries = list(Country.objects.all())
        countries.append(None)
        organizations = list(Organization.objects.all())
        for surv in Survey.objects.filter(active=True):
            for country in countries:
                if country is None:
                    country_id = country
                else:
                    country_id = country.pk
                surv_key = (surv.pk, country_id)

                if surv_key not in cls.survey_stat:
                    cls.survey_stat[surv_key] = SurveyStat(survey=surv, country=country)
                for org in organizations:
                    org_key = (surv.pk, country_id, org.pk)
                    if org_key not in cls.organization_stat:
                        cls.organization_stat[org_key] = OrganizationStat(
                            survey=surv, country=country, organization=org, report_order=org.report_order)
                    else:
                        if cls.organization_stat[org_key].report_order != org.report_order:
                            cls.organization_stat[org_key].report_order = org.report_order

    @classmethod
    def update_survey_stat(cls, surv_key, answer):
        survey_id, country_id = surv_key
        if surv_key not in cls.survey_stat:
            cls.survey_stat[surv_key] = SurveyStat(survey_id=survey_id, country_id=country_id, last=answer.created_at)
        cls.survey_stat[surv_key].total += 1
        if cls.survey_stat[surv_key].last:
            cls.survey_stat[surv_key].last = max(cls.survey_stat[surv_key].last, answer.created_at)
        else:
            cls.survey_stat[surv_key].last = answer.created_at

        surv_key_all = (survey_id, None)
        if surv_key_all not in cls.survey_stat:
            cls.survey_stat[surv_key_all] = SurveyStat(survey_id=survey_id, country_id=None)
        cls.survey_stat[surv_key_all].total += 1
        if cls.survey_stat[surv_key_all].last:
            cls.survey_stat[surv_key_all].last = max(cls.survey_stat[surv_key].last, answer.created_at)
        else:
            cls.survey_stat[surv_key_all].last = answer.created_at

    @classmethod
    def update_organization_stat(cls, org_key):
        survey_id, country_id, organization_id = org_key
        if org_key not in cls.organization_stat:
            cls.organization_stat[org_key] = OrganizationStat(
                survey_id=survey_id, country_id=country_id, organization_id=organization_id)
        cls.organization_stat[org_key].total += 1

        org_key_all = (survey_id, None, organization_id)
        if org_key_all not in cls.organization_stat:
            cls.organization_stat[org_key_all] = OrganizationStat(
                survey_id=survey_id, country_id=None, organization_id=organization_id)
        cls.organization_stat[org_key_all].total += 1

    @classmethod
    def process_answer(cls, answer):
        if not answer.body:
            return

        try:
            data = queryparser.parse(answer.body)
        except queryparser.MalformedQueryStringError:
            return

        survey_id = answer.survey_id
        country_id = answer.user.country_id
        organization_id = answer.organization_id

        surv_key = (survey_id, country_id)
        cls.update_survey_stat(surv_key, answer)

        org_key = (survey_id, country_id, organization_id)
        cls.update_organization_stat(org_key)

        answer.is_updated = True
        answer.save()


    @classmethod
    def save(cls):
        for surv_stat in cls.survey_stat.values():
            surv_stat.save()
        for org_stat in cls.organization_stat.values():
            org_stat.save()





    @classmethod
    def process_answers(cls):
        cls.clear()
        cls.load_stat()
        cls.fill_out()
        answers = cls.get_answers()
        for answer in answers:
            cls.process_answer(answer)
        cls.save()

    def evaluate(self):
        pass


class TotalEvaluator(AbstractEvaluator):
    @staticmethod
    def get_answers():
        return Answer.objects.all()

    @staticmethod
    def clear():
        SurveyStat.objects.all().delete()
        OrganizationStat.objects.all().delete()


class LastEvaluator(AbstractEvaluator):
    @staticmethod
    def get_answers():
        return Answer.objects.filter(is_updated=False)

    @staticmethod
    def clear():
        pass

