from django.db import models
from querystring_parser import parser as queryparser

from survey.models import Country, Survey, Organization, Answer


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
    def update_survey_stat(cls, surv_key, answer):
        survey_id, country_id = surv_key
        if surv_key not in cls.survey_stat:
            cls.survey_stat[surv_key] = SurveyStat(survey_id=survey_id, country_id=country_id)
        cls.survey_stat[surv_key].total += 1
        cls.survey_stat[surv_key].last = max(cls.survey_stat[surv_key].last, answer.created_at)

        surv_key_all = (survey_id, None)
        if surv_key_all not in cls.survey_stat:
            cls.survey_stat[surv_key_all] = SurveyStat(survey_id=survey_id, country_id=None)
        cls.survey_stat[surv_key_all].total += 1
        cls.survey_stat[surv_key_all].last = max(cls.survey_stat[surv_key].last, answer.created_at)

    @classmethod
    def update_organization_stat(cls, org_key):
        survey_id, country_id, organization_id = org_key
        if org_key not in cls.organization_stat:
            cls.organization_stat[org_key] = OrganizationStat(
                survey_id=survey_id, country_id=country_id, organization_id=organization_id)
        cls.organization_stat[org_key].total += 1

        org_key_all = (survey_id, None, organization_id)
        if org_key_all not in cls.organization_stat:
            cls.organization_stat[org_key] = OrganizationStat(
                survey_id=survey_id, country_id=None, organization_id=organization_id)
        cls.organization_stat[org_key].total += 1

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
    def update_stat(cls):
        raise NotImplementedError


    @classmethod
    def process_answers(cls):
        cls.clear()
        cls.load_stat()
        answers = cls.get_answers()
        for answer in answers:
            cls.process_answer(answer)
        cls.update_stat()

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

