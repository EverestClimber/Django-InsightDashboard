from mixer.backend.django import mixer
import pytest
from unittest.mock import patch

from django.test import TestCase

from survey.models import Answer, Option
from insights.users.models import User

from ..models import TotalEvaluator, LastEvaluator, SurveyStat, OrganizationStat

pytestmark = pytest.mark.django_db


class TestTotalEvaluator(TestCase):
    evaluator = TotalEvaluator
    # fixtures = ['survey.json']

    def test_get_answers(self):
        mixer.blend(Answer, is_updated=True)
        mixer.blend(Answer, is_updated=False)
        answers = self.evaluator.get_answers()
        assert len(answers) == 2, 'Should return all records'

    def test_clear(self):
        mixer.blend(SurveyStat)
        mixer.blend(SurveyStat)
        mixer.blend(OrganizationStat)
        mixer.blend(OrganizationStat)

        self.evaluator.clear()

        assert SurveyStat.objects.all().count() == 0, 'Cleared'
        assert OrganizationStat.objects.all().count() == 0, 'Cleared'

    def test_load_stat(self):
        mixer.blend(SurveyStat, survey_id=1, country_id=None)
        mixer.blend(SurveyStat, survey_id=1, country_id=1)
        mixer.blend(SurveyStat, survey_id=2, country_id=1)
        mixer.blend(OrganizationStat, survey_id=1, country_id=None, organization_id=1)
        mixer.blend(OrganizationStat, survey_id=1, country_id=1, organization_id=1)
        mixer.blend(OrganizationStat, survey_id=2, country_id=1, organization_id=1)
        mixer.blend(OrganizationStat, survey_id=2, country_id=1, organization_id=2)
        self.evaluator.load_stat()
        assert len(self.evaluator.survey_stat) == 3
        assert len(self.evaluator.organization_stat) == 4

    @patch('reports.models.AbstractEvaluator.process_answer')
    @patch('reports.models.AbstractEvaluator.load_stat')
    @patch('reports.models.AbstractEvaluator.update_stat')
    def test_process_answers(self, update_stat, load_stat, process_answer):
        mixer.blend(SurveyStat, survey_id=1, country_id=None)
        mixer.blend(SurveyStat, survey_id=1, country_id=1)
        mixer.blend(SurveyStat, survey_id=2, country_id=1)
        mixer.blend(OrganizationStat, survey_id=1, country_id=None, organization_id=1)
        mixer.blend(OrganizationStat, survey_id=1, country_id=1, organization_id=1)
        mixer.blend(OrganizationStat, survey_id=2, country_id=1, organization_id=1)
        mixer.blend(OrganizationStat, survey_id=2, country_id=1, organization_id=2)
        mixer.blend(Answer, is_updated=False)
        mixer.blend(Answer, is_updated=False)
        self.evaluator.process_answers()
        assert process_answer.call_count == 2
        assert load_stat.call_count == 1
        assert update_stat.call_count == 1

    @patch('reports.models.AbstractEvaluator.update_survey_stat')
    @patch('reports.models.AbstractEvaluator.update_organization_stat')
    def test_process_answer(self, organization_stat, survey_stat):
        user = mixer.blend(User, country_id=1)

        answer = mixer.blend(Answer, survey_id=1, organization_id=2, user=user, body='')
        self.evaluator.process_answer(answer)
        assert organization_stat.call_count == 0
        assert survey_stat.call_count == 0

        answer = mixer.blend(Answer, survey_id=1, organization_id=2, body='111')
        self.evaluator.process_answer(answer)
        assert organization_stat.call_count == 0
        assert survey_stat.call_count == 0

        answer = mixer.blend(Answer, survey_id=1, organization_id=2, user=user, body='a=1')
        self.evaluator.process_answer(answer)
        assert organization_stat.call_count == 1
        assert survey_stat.call_count == 1




class TestLastEvaluator(object):
    evaluator = LastEvaluator

    def test_get_answers(self):
        mixer.blend(Answer, is_updated=True)
        mixer.blend(Answer, is_updated=False)
        answers = self.evaluator.get_answers()
        assert len(answers) == 1, 'Should return just one last record'


    def test_clear(self):
        mixer.blend(SurveyStat)
        mixer.blend(SurveyStat)
        mixer.blend(OrganizationStat)
        mixer.blend(OrganizationStat)

        self.evaluator.clear()

        assert SurveyStat.objects.all().count() == 2, 'Cleared'
        assert OrganizationStat.objects.all().count() == 2, 'Cleared'
