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

            'reg_sum': {1: 60.0, 2: 30.0},
            'reg_cnt': {1: 2, 2: 1},

            'org_sum': {1: 90.0},
            'org_cnt': {1: 3},
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

            'reg_yes': {1: 1, 2: 1},
            'reg_cnt': {1: 2, 2: 1},

            'org_yes': {1: 2},
            'org_cnt': {1: 3},
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

    def test_update_type_multiselect_top(self):
        data = {
            'top1': {'x2': 1, 'x1': 2},
            'top3': {'x3': 2, 'x2': 3, 'x1': 2},
            'cnt': 3,
            'org': {
                1: {
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
