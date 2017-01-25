from collections import OrderedDict
from datetime import datetime
from mixer.backend.django import mixer
import pytest
from querystring_parser.parser import MalformedQueryStringError
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from survey.models import Answer, Survey, Organization, Question, Region
from insights.users.models import User, Country

from ..models import SurveyStat, OrganizationStat, QuestionStat, Representation
from ..evaluators import AbstractEvaluator, TotalEvaluator, LastEvaluator

pytestmark = pytest.mark.django_db


class TestTotalEvaluator(TestCase):
    evaluator = TotalEvaluator
    # fixtures = ['survey.json']

    def setUp(self):
        self.evaluator.survey_stat = {}
        self.evaluator.organization_stat = {}
        self.evaluator.question_stat = {}
        self.evaluator.question_representation_link = {}
        self.evaluator.question_dict = {}

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
        mixer.blend(QuestionStat)

        self.evaluator.clear()

        assert SurveyStat.objects.all().count() == 0, 'Cleared'
        assert OrganizationStat.objects.all().count() == 0, 'Cleared'
        assert QuestionStat.objects.all().count() == 0, 'Cleared'

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

        r1 = mixer.blend(Representation, active=True)
        r2 = mixer.blend(Representation, active=True)

        mixer.blend(QuestionStat, survey=s1, country=None, representation=r1)
        mixer.blend(QuestionStat, survey=s1, country=c1, representation=r1)
        mixer.blend(QuestionStat, survey=s1, country=c1, representation=r2)

        self.evaluator.load_stat()
        assert len(self.evaluator.survey_stat) == 3
        assert len(self.evaluator.organization_stat) == 4
        assert len(self.evaluator.question_stat) == 3

    def test_fill_out(self):
        s1 = mixer.blend(Survey, active=True)
        c1 = mixer.blend(Country)
        c2 = mixer.blend(Country)
        o1 = mixer.blend(Organization)
        o2 = mixer.blend(Organization)
        q1 = mixer.blend(Question)
        q2 = mixer.blend(Question)
        mixer.blend(Question)
        r1 = mixer.blend(Representation, active=True, question=[q1])
        r2 = mixer.blend(Representation, active=True, question=[q2])

        mixer.blend(SurveyStat, survey=s1, country=None)
        mixer.blend(SurveyStat, survey=s1, country=c1)
        mixer.blend(OrganizationStat, survey=s1, country_id=None, organization=o1)
        mixer.blend(OrganizationStat, survey=s1, country=c1, organization=o1)
        mixer.blend(QuestionStat, survey=s1, country=None, representation=r1)
        mixer.blend(QuestionStat, survey=s1, country=c1, representation=r1)
        self.evaluator.load_stat()
        assert len(self.evaluator.survey_stat) == 2
        assert len(self.evaluator.organization_stat) == 2
        assert len(self.evaluator.question_stat) == 2
        self.evaluator.fill_out()
        assert len(self.evaluator.survey_stat) == 3
        assert len(self.evaluator.organization_stat) == 6
        assert len(self.evaluator.question_stat) == 6
        assert self.evaluator.question_representation_link == {
            q1.pk: r1,
            q2.pk: r2
        }
        assert self.evaluator.question_dict == {
            q1.pk: q1,
            q2.pk: q2
        }


    @patch('reports.evaluators.AbstractEvaluator.process_answer')
    @patch('reports.evaluators.AbstractEvaluator.load_stat')
    @patch('reports.evaluators.AbstractEvaluator.fill_out')
    @patch('reports.evaluators.AbstractEvaluator.save')
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

    @patch('reports.evaluators.AbstractEvaluator.update_survey_stat')
    @patch('reports.evaluators.AbstractEvaluator.update_organization_stat')
    def test_process_answer_with_empty_data(self, organization_stat, survey_stat):
        user = mixer.blend(User, country_id=1)

        answer = mixer.blend(Answer, user=user, body='')
        self.assertRaises(KeyError, self.evaluator.process_answer, answer)
        assert organization_stat.call_count == 0
        assert survey_stat.call_count == 0

        answer = mixer.blend(Answer, body='111')
        self.assertRaises(MalformedQueryStringError, self.evaluator.process_answer, answer)
        assert organization_stat.call_count == 0
        assert survey_stat.call_count == 0

        answer = mixer.blend(Answer, user=user, body='a=1')
        self.assertRaises(KeyError, self.evaluator.process_answer, answer)

        answer = mixer.blend(Answer, user=user, body='data=1')
        self.assertRaises(KeyError, self.evaluator.process_answer, answer)

        answer = mixer.blend(Answer, user=user, body='data[111]=Yes')
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

        qs1 = MagicMock()
        qs2 = MagicMock()
        self.evaluator.question_stat = {
            (1, 2, 3): qs1,
            (1, 3, 3): qs2,
        }

        self.evaluator.save()

        os1.save.assert_called_once_with()
        ss1.save.assert_called_once_with()
        qs1.save.assert_called_once_with()
        os2.save.assert_called_once_with()
        ss2.save.assert_called_once_with()
        qs2.save.assert_called_once_with()

    def test_parse_query_string(self):
        results = self.evaluator.parse_query_string('data%5B12%5D%5B%5D=&data%5B4%5D%5B%5D=Age&data%5B4%5D%5B%5D=Preference+of+the+patients&data%5B4%5D%5B%5D=Efficacy+profile&data%5B4%5D%5B%5D=&csrfmiddlewaretoken=C7UlUxD6GI60dwB3PnGtA9en518LhHhRfqQwzXRb6pMVAs9jgaMIgWK0mq2AH8a6&data%5B14%5D%5B%5D=&data%5B3%5D%5Bother%5D=&data%5B7%5D=No&data%5B9%5D%5Badditional%5D=&data%5B2%5D=Yes&data%5B3%5D%5B%5D=Ari-oral&data%5B3%5D%5B%5D=Resperidol-oral&data%5B3%5D%5B%5D=Ari-LAI&data%5B3%5D%5B%5D=&data%5B11%5D%5Bother%5D=&data%5B9%5D%5Bmain%5D=&data%5B6%5D%5B%5D=Age&data%5B6%5D%5B%5D=Mechanism+of+Action&data%5B6%5D%5B%5D=Preference+of+the+patients&data%5B6%5D%5B%5D=&data%5B16%5D=xxx&data%5B11%5D%5B%5D=&data%5B14%5D%5Bother%5D=&data%5B1%5D%5Bmain%5D=10&data%5B4%5D%5Bother%5D=&data%5B12%5D%5Bother%5D=&data%5B6%5D%5Bother%5D=&data%5B1%5D%5Badditional%5D=')
        assert results['data'] == {

            1: {'main': '10', 'additional': ''},
            2: 'Yes',
            3: {'': ['Ari-oral', 'Resperidol-oral', 'Ari-LAI', ''], 'other': ''},
            4: {'': ['Age', 'Preference of the patients', 'Efficacy profile', ''], 'other': ''},
            6: {'': ['Age', 'Mechanism of Action', 'Preference of the patients', ''], 'other': ''},
            7: 'No',
            9: {'main': '', 'additional': ''},
            11: {'': '', 'other': ''},
            12: {'': '', 'other': ''},
            14: {'': '', 'other': ''},
            16: 'xxx'
        }

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


class TestTypeProcessor(TestCase):
    evaluator = TotalEvaluator

    def setUp(self):
        self.evaluator.survey_stat = {}
        self.evaluator.organization_stat = {}
        self.evaluator.question_stat = {}
        self.evaluator.question_representation_link = {}
        self.evaluator.question_dict = {}

    def test_types(self):
        for name, dsc in Representation.TYPE_CHOICES:
            assert callable(getattr(self.evaluator, "%s_processor" % name))

        s1 = mixer.blend(Survey, active=True)
        c1 = mixer.blend(Country)

        q1 = mixer.blend(Question, type=Question.TYPE_TWO_DEPENDEND_FIELDS)
        q2 = mixer.blend(Question, type=Question.TYPE_YES_NO)
        q3 = mixer.blend(Question, type=Question.TYPE_YES_NO_JUMPING)
        q4 = mixer.blend(Question, type=Question.TYPE_MULTISELECT_ORDERED)
        q5 = mixer.blend(Question, type=Question.TYPE_MULTISELECT_WITH_OTHER)
        q6 = mixer.blend(Question, type=Question.TYPE_DEPENDEND_QUESTION)
        q7 = mixer.blend(Question, type=Question.TYPE_CHOICES)

        r1 = mixer.blend(Representation, active=True, question=[q1])
        r2 = mixer.blend(Representation, active=True, question=[q2])
        r3 = mixer.blend(Representation, active=True, question=[q3])
        r4 = mixer.blend(Representation, active=True, question=[q4])
        r5 = mixer.blend(Representation, active=True, question=[q5])
        r6 = mixer.blend(Representation, active=True, question=[q6])
        r7 = mixer.blend(Representation, active=True, question=[q7])

        a = mixer.blend(Answer, survey=s1)

        qs = mixer.blend(QuestionStat)
        self.evaluator.fill_out()

        self.assertRaises(ValueError, self.evaluator.type_average_percent_processor, q2.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_average_percent_processor, q3.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_average_percent_processor, q4.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_average_percent_processor, q5.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_average_percent_processor, q6.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_average_percent_processor, q7.pk, {}, a)

        self.assertRaises(ValueError, self.evaluator.type_multiselect_top_processor, q1.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_multiselect_top_processor, q2.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_multiselect_top_processor, q3.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_multiselect_top_processor, q5.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_multiselect_top_processor, q6.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_multiselect_top_processor, q7.pk, {}, a)

        self.assertRaises(ValueError, self.evaluator.type_yes_no_processor, q1.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_yes_no_processor, q4.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_yes_no_processor, q5.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_yes_no_processor, q6.pk, {}, a)
        self.assertRaises(ValueError, self.evaluator.type_yes_no_processor, q7.pk, {}, a)

    def init_models(self, question_type, representation_type):
        self.surv = mixer.blend(Survey, active=True)
        self.c1 = mixer.blend(Country)
        self.c2 = mixer.blend(Country)
        self.c3 = mixer.blend(Country)
        self.u1 = mixer.blend(User, country=self.c1)
        self.u11 = mixer.blend(User, country=self.c1)
        self.u2 = mixer.blend(User, country=self.c2)
        self.u3 = mixer.blend(User, country=self.c3)
        self.reg11 = mixer.blend(Region, country=self.c1)
        self.reg12 = mixer.blend(Region, country=self.c1)
        self.reg13 = mixer.blend(Region, country=self.c1)
        self.reg21 = mixer.blend(Region, country=self.c2)
        self.reg31 = mixer.blend(Region, country=self.c3)
        self.org = mixer.blend(Organization)
        self.q = mixer.blend(Question, type=question_type)
        self.r = mixer.blend(Representation, question=[self.q], type=representation_type)

        self.evaluator.survey_stat = {}
        self.evaluator.organization_stat = {}
        self.evaluator.question_stat = {}
        self.evaluator.question_representation_link = {}
        self.evaluator.question_dict = {}

        self.evaluator.load_stat()
        self.evaluator.fill_out()

    def create_answer(self, **kwargs):
        if 'survey' not in kwargs:
            kwargs['survey'] = self.surv
        if 'region' not in kwargs:
            kwargs['region'] = self.reg11
        if 'user' not in kwargs:
            kwargs['user'] = self.u1
        if 'org' not in kwargs:
            kwargs['organization'] = self.org
        if 'is_updated' not in kwargs:
            kwargs['is_update'] = False
        return mixer.blend(Answer, **kwargs)

    def test_type_average_percent_processor(self):

        self.init_models(Question.TYPE_TWO_DEPENDEND_FIELDS, Representation.TYPE_AVERAGE_PERCENT)
        qid = self.q.pk
        a1 = self.create_answer(body='data[%s][main]=40' % qid, user=self.u1, region=self.reg11)
        a2 = self.create_answer(body='data[%s][main]=20' % qid, user=self.u11, region=self.reg12)
        a3 = self.create_answer(body='data[%s][main]=30' % qid, user=self.u2, region=self.reg21)

        self.evaluator.type_average_percent_processor(qid, {'main': '40', 'additional': ''}, a1)
        self.evaluator.type_average_percent_processor(qid, {'main': '20', 'additional': ''}, a2)
        self.evaluator.type_average_percent_processor(qid, {'main': '30', 'additional': ''}, a3)

        k0 = (self.surv.pk, None, self.r.pk)
        k1 = (self.surv.pk, self.c1.pk, self.r.pk)

        data = self.evaluator.question_stat[k0].data
        assert data['main_cnt'] == 3
        self.assertAlmostEqual(data['main_sum'],  90.0)

        assert data['reg_cnt'][self.c1.pk] == 2
        self.assertAlmostEqual(data['reg_sum'][self.c1.pk],  60.0)

        assert data['reg_cnt'][self.c2.pk] == 1
        self.assertAlmostEqual(data['reg_sum'][self.c2.pk],  30.0)

        assert data['org_cnt'][self.org.pk] == 3
        self.assertAlmostEqual(data['org_sum'][self.org.pk],  90.0)

        data = self.evaluator.question_stat[k1].data
        assert data['main_cnt'] == 2
        self.assertAlmostEqual(data['main_sum'],  60.0)

        assert data['reg_cnt'][self.reg11.pk] == 1
        self.assertAlmostEqual(data['reg_sum'][self.reg11.pk],  40.0)

        assert data['reg_cnt'][self.reg12.pk] == 1
        self.assertAlmostEqual(data['reg_sum'][self.reg12.pk],  20.0)

        assert data['org_cnt'][self.org.pk] == 2
        self.assertAlmostEqual(data['org_sum'][self.org.pk],  60.0)


    def test_type_yes_no_processor(self):
        self.init_models(Question.TYPE_YES_NO, Representation.TYPE_YES_NO)
        qid = self.q.pk
        a1 = self.create_answer(body='data[%s]=Yes' % qid, user=self.u1, region=self.reg11)
        a2 = self.create_answer(body='data[%s]=No' % qid, user=self.u11, region=self.reg12)
        a3 = self.create_answer(body='data[%s]=Yes' % qid, user=self.u2, region=self.reg21)

        self.evaluator.type_yes_no_processor(qid, 'Yes', a1)
        self.evaluator.type_yes_no_processor(qid, 'No', a2)
        self.evaluator.type_yes_no_processor(qid, 'Yes', a3)

        k0 = (self.surv.pk, None, self.r.pk)
        k1 = (self.surv.pk, self.c1.pk, self.r.pk)

        data = self.evaluator.question_stat[k0].data
        assert data['main_cnt'] == 3
        assert data['main_yes'] == 2

        assert data['reg_cnt'][self.c1.pk] == 2
        assert data['reg_yes'][self.c1.pk] == 1

        assert data['reg_cnt'][self.c2.pk] == 1
        assert data['reg_yes'][self.c2.pk] == 1

        assert data['org_cnt'][self.org.pk] == 3
        assert data['org_yes'][self.org.pk] == 2

        data = self.evaluator.question_stat[k1].data
        assert data['main_cnt'] == 2
        assert data['main_yes'] == 1

        assert data['reg_cnt'][self.reg11.pk] == 1
        assert data['reg_yes'][self.reg11.pk] == 1

        assert data['reg_cnt'][self.reg12.pk] == 1
        assert data['reg_yes'][self.reg12.pk] == 0

        assert data['org_cnt'][self.org.pk] == 2
        assert data['org_yes'][self.org.pk] == 1
