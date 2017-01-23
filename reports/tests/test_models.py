from datetime import datetime
from mixer.backend.django import mixer
import pytest
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from survey.models import Answer, Survey, Organization
from insights.users.models import User, Country

from ..models import TotalEvaluator, LastEvaluator, SurveyStat, OrganizationStat

pytestmark = pytest.mark.django_db


class TestTotalEvaluator(TestCase):
    evaluator = TotalEvaluator
    # fixtures = ['survey.json']

    def setUp(self):
        self.evaluator.survey_stat = {}
        self.evaluator.organization_stat = {}

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
        s1 = mixer.blend(Survey)
        s2 = mixer.blend(Survey)
        c1 = mixer.blend(Country)
        c2 = mixer.blend(Country)
        o1 = mixer.blend(Organization)
        o2 = mixer.blend(Organization)
        mixer.blend(SurveyStat, survey=s1, country=None)
        mixer.blend(SurveyStat, survey=s1, country=c1)
        mixer.blend(SurveyStat, survey=s2, country=c1)
        mixer.blend(OrganizationStat, survey=s1, country_id=None, organization=o1)
        mixer.blend(OrganizationStat, survey=s1, country=c1, organization=o1)
        mixer.blend(OrganizationStat, survey=s2, country=c1, organization=o1)
        mixer.blend(OrganizationStat, survey=s2, country=c1, organization=o2)
        self.evaluator.load_stat()
        assert len(self.evaluator.survey_stat) == 3
        assert len(self.evaluator.organization_stat) == 4

    def test_fill_out(self):
        s1 = mixer.blend(Survey, active=True)
        c1 = mixer.blend(Country)
        c2 = mixer.blend(Country)
        o1 = mixer.blend(Organization)
        o2 = mixer.blend(Organization)
        mixer.blend(SurveyStat, survey=s1, country=None)
        mixer.blend(SurveyStat, survey=s1, country=c1)
        mixer.blend(OrganizationStat, survey=s1, country_id=None, organization=o1)
        mixer.blend(OrganizationStat, survey=s1, country=c1, organization=o1)
        self.evaluator.load_stat()
        assert len(self.evaluator.survey_stat) == 2
        assert len(self.evaluator.organization_stat) == 2
        self.evaluator.fill_out()
        assert len(self.evaluator.survey_stat) == 3
        assert len(self.evaluator.organization_stat) == 6


    @patch('reports.models.AbstractEvaluator.process_answer')
    @patch('reports.models.AbstractEvaluator.load_stat')
    @patch('reports.models.AbstractEvaluator.fill_out')
    @patch('reports.models.AbstractEvaluator.save')
    def test_process_answers(self, save, fill_out, load_stat, process_answer):
        s1 = mixer.blend(Survey)
        s2 = mixer.blend(Survey)
        c1 = mixer.blend(Country)
        c2 = mixer.blend(Country)
        o1 = mixer.blend(Organization)
        o2 = mixer.blend(Organization)
        mixer.blend(SurveyStat, survey=s1, country=None)
        mixer.blend(SurveyStat, survey=s1, country=c1)
        mixer.blend(SurveyStat, survey=s2, country=c1)
        mixer.blend(OrganizationStat, survey=s1, country=None, organization=o1)
        mixer.blend(OrganizationStat, survey=s1, country=c1, organization=o1)
        mixer.blend(OrganizationStat, survey=s2, country=c1, organization=o1)
        mixer.blend(OrganizationStat, survey=s2, country=c1, organization=o2)
        mixer.blend(Answer, is_updated=False)
        mixer.blend(Answer, is_updated=False)
        self.evaluator.process_answers()
        assert process_answer.call_count == 2
        fill_out.assert_called_once_with()
        assert load_stat.call_count == 1
        assert save.call_count == 1

    @patch('reports.models.AbstractEvaluator.update_survey_stat')
    @patch('reports.models.AbstractEvaluator.update_organization_stat')
    def test_process_answer_with_empty_data(self, organization_stat, survey_stat):
        user = mixer.blend(User, country_id=1)

        answer = mixer.blend(Answer, user=user, body='')
        self.evaluator.process_answer(answer)
        assert organization_stat.call_count == 0
        assert survey_stat.call_count == 0

        answer = mixer.blend(Answer, body='111')
        self.evaluator.process_answer(answer)
        assert organization_stat.call_count == 0
        assert survey_stat.call_count == 0

        answer = mixer.blend(Answer, user=user, body='a=1')
        self.evaluator.process_answer(answer)
        survey_stat.assert_called_once_with((answer.survey_id, user.country_id), answer)
        organization_stat.assert_called_once_with((answer.survey_id, user.country_id, answer.organization_id))

    def test_process_answer(self):
        d1 = timezone.make_aware(datetime(2017, 1, 1))
        d2 = timezone.make_aware(datetime(2017, 1, 2))
        mixer.blend(SurveyStat, survey_id=1, country_id=None, total=2, last=d1)
        mixer.blend(SurveyStat, survey_id=1, country_id=1, total=2, last=d1)
        mixer.blend(OrganizationStat, survey_id=1, country_id=None, organization_id=1, total=2)
        mixer.blend(OrganizationStat, survey_id=1, country_id=1, organization_id=1, total=2)

        self.evaluator.load_stat()

    def test_update_survey_stat(self):
        d1 = timezone.make_aware(datetime(2017, 1, 1))
        d2 = timezone.make_aware(datetime(2017, 1, 2))
        a1 = mixer.blend(Answer)
        a1.created_at = d1
        a2 = mixer.blend(Answer)
        a2.created_at = d2
        self.evaluator.update_survey_stat((1, 2), a1)
        self.evaluator.update_survey_stat((1, 2), a2)
        assert self.evaluator.survey_stat[(1, 2)].total == 2
        assert self.evaluator.survey_stat[(1, 2)].last == d2
        assert self.evaluator.survey_stat[(1, None)].total == 2
        assert self.evaluator.survey_stat[(1, None)].last == d2

    def test_update_organization_stat(self):
        self.evaluator.update_organization_stat((1, 2, 3))
        self.evaluator.update_organization_stat((1, 2, 3))
        self.evaluator.update_organization_stat((1, 2, 4))
        self.evaluator.update_organization_stat((1, 2, 4))
        assert self.evaluator.organization_stat[(1, 2, 3)].total == 2

    def test_save(self):
        ss1 = MagicMock()
        ss2 = MagicMock()
        self.evaluator.survey_stat = {
            (1, 1): ss1,
            (1, 2): ss2,
        }

        os1 = MagicMock()
        os2 = MagicMock()
        self.evaluator.organization_stat = {
            (1, 2, 3): os1,
            (1, 3, 3): os2,
        }

        self.evaluator.save()

        os1.save.assert_called_once_with()
        ss1.save.assert_called_once_with()
        os2.save.assert_called_once_with()
        ss2.save.assert_called_once_with()


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
