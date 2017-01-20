from django.db import models

from survey.models import Country, Survey, Organization, Answer


class Stat(models.Model):
    country = models.ForeignKey(Country, blank=True, null=True)
    survey = models.ForeignKey(Survey, null=True)
    total = models.PositiveIntegerField()

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.total)


class SurveyStat(Stat):
    last = models.DateTimeField(blank=True, null=True)


class OrganizationStat(Stat):
    organization = models.ForeignKey(Organization, null=True)


class AbstractEvaluator(object):
    def evaluate(self):
        pass


class TotalEvaluator(AbstractEvaluator):
    pass

class LastEvaluator(AbstractEvaluator):
    pass

