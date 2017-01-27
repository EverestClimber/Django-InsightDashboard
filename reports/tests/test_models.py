from mixer.backend.django import mixer
import pytest

from django.test import TestCase

from survey.models import Option, Region, Organization, Question
from insights.users.models import User, Country
from ..models import OptionDict, QuestionStat, Representation

pytestmark = pytest.mark.django_db


class TestOptionDict(TestCase):

    def setUp(self):
        OptionDict.clear()

    def test_load(self):
        mixer.blend(Option, value='Qq')
        mixer.blend(Option, value='Ww')
        mixer.blend(Option, value='Ee')

        od1 = mixer.blend(OptionDict, lower='qq', original='Qq')
        od2 = mixer.blend(OptionDict, lower='ww', original='W')

        assert OptionDict.get('qq') == 'Qq'
        assert OptionDict.get('mm') == 'mm'

        assert OptionDict.data['qq'] == od1
        assert OptionDict.data['ww'] == od2
        assert OptionDict.data['ww'].original == 'Ww'
        assert OptionDict.data['ee'].original == 'Ee'

        OptionDict.register('mm', 'Mm')
        assert OptionDict.get('mm') == 'Mm'
        assert OptionDict.objects.get(lower='mm')


        assert OptionDict.get('xx') == 'xx'


class TestQuestionStat(TestCase):
    def test_updators(self):
        q = QuestionStat()
        for name, _ in QuestionStat.TYPE_CHOICES:
            assert callable(getattr(q, 'update_%s' % name))

    def setUp(self):
        self.c1 = mixer.blend(Country)
        self.c2 = mixer.blend(Country)
        self.c3 = mixer.blend(Country)

        self.reg1 = mixer.blend(Region, country=self.c1)
        self.reg2 = mixer.blend(Region, country=self.c1)
        self.reg3 = mixer.blend(Region, country=self.c1)

        self.org1 = mixer.blend(Organization)
        self.org2 = mixer.blend(Organization)
        self.org3 = mixer.blend(Organization)

        self.q = mixer.blend(Question)
        self.r = mixer.blend(Representation, question=[self.q])

        QuestionStat.clear()

    def test_update_type_average_percent(self):
        data = {
            'main_sum': 90.0,
            'main_cnt': 3,

            'reg_sum': {'1': 60.0, '2': 30.0},
            'reg_cnt': {'1': 2, '2': 1},

            'org_sum': {'1': 90.0},
            'org_cnt': {'1': 3},
        }
        qs0 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=None,
                          type=QuestionStat.TYPE_AVERAGE_PERCENT)
        qs0.update_vars()

        qs1 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=self.c1,
                          type=QuestionStat.TYPE_AVERAGE_PERCENT)
        qs1.update_vars()

    def test_update_type_yes_no(self):
        data = {
            'main_yes': 2,
            'main_cnt': 3,

            'reg_yes': {'1': 1, '2': 1},
            'reg_cnt': {'1': 2, '2': 1},

            'org_yes': {'1': 2},
            'org_cnt': {'1': 3},
        }

        qs0 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=None,
                          type=QuestionStat.TYPE_YES_NO)
        qs0.update_vars()

        qs1 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=self.c1,
                          type=QuestionStat.TYPE_YES_NO)
        qs1.update_vars()

    def test_calculate_top(self):
        top = {
            'x1': 100,
            'x2': 40,
            'x3': 20,
            'x4': 5,
            'x5': 5,
            'x6': 5,
            'x7': 5,
            'x8': 5,
            'x9': 5,
            'x10': 5,
            'x11': 5
        }
        result = QuestionStat._calculate_top(top)

        assert result['pie'] == {
            'labels': ('x1', 'x2', 'x3', 'Other'),
            'data': (100, 40, 20, 40),
            'hide_last_legend_item': 'true'
        }

        assert result['table'] == [
            (100, 'x1', 50.0),
            (40, 'x2', 20.0),
            (20, 'x3', 10.0),
            (5, 'x10', 2.5),
            (5, 'x11', 2.5),
            (5, 'x4', 2.5),
            (5, 'x5', 2.5),
            (5, 'x6', 2.5),
            (5, 'x7', 2.5),
            (5, 'x8', 2.5),

        ]

        top = {
            'x1': 40,
            'x2': 30,
            'x3': 20,
            'x4': 10,
        }
        result = QuestionStat._calculate_top(top)
        assert result['pie'] == {
            'labels': ('x1', 'x2', 'x3', 'Other'),
            'data': (40, 30, 20, 10),
            'hide_last_legend_item': 'true'
        }
        assert result['table'] == [
            (40, 'x1', 40.0),
            (30, 'x2', 30.0),
            (20, 'x3', 20.0),
            (10, 'x4', 10.0),
        ]

        top = {
            'x1': 50,
            'x2': 30,
            'x3': 20
        }
        result = QuestionStat._calculate_top(top)
        assert result['pie'] == {
            'labels': ('x1', 'x2', 'x3', ''),
            'data': (50, 30, 20, 0),
            'hide_last_legend_item': 'false'
        }

        top = {
            'x1': 50,
            'x2': 30,
        }
        result = QuestionStat._calculate_top(top)
        assert result['pie'] == {
            'labels': ('x1', 'x2', '', ''),
            'data': (50, 30, 0, 0),
            'hide_last_legend_item': 'false'
        }

        top = {
            'x1': 50,
        }
        result = QuestionStat._calculate_top(top)
        assert result['pie'] == {
            'labels': ('x1', '', '', ''),
            'data': (50, 0, 0, 0),
            'hide_last_legend_item': 'false'
        }

    def test_update_type_multiselect_top(self):
        data = {
            'top1': {'x2': 1, 'x1': 2},
            'top3': {'x3': 2, 'x2': 3, 'x1': 2},
            'cnt': 3,
            'org': {
                '1': {
                    'top1': {'x2': 1, 'x1': 2},
                    'top3': {'x3': 2, 'x2': 3, 'x1': 2},
                    'cnt': 3
                }
            }
        }

        qs0 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=None,
                          type=QuestionStat.TYPE_MULTISELECT_TOP)
        qs0.update_vars()

        qs1 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=self.c1,
                          type=QuestionStat.TYPE_MULTISELECT_TOP)
        qs1.update_vars()
