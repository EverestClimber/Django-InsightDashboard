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
        self.c1 = mixer.blend(Country, name='Spain', ordering=1, use_in_reports=True)
        self.c2 = mixer.blend(Country, name='France', ordering=2, use_in_reports=True)
        self.c3 = mixer.blend(Country, name='Italy', ordering=3, use_in_reports=True)
        self.c3 = mixer.blend(Country, name='Other', ordering=3, use_in_reports=False)

        self.reg1 = mixer.blend(Region, country=self.c1, name='East', ordering=1)
        self.reg2 = mixer.blend(Region, country=self.c1, name='West', ordering=2)
        self.reg3 = mixer.blend(Region, country=self.c1, name='North', ordering=3)

        self.org1 = mixer.blend(Organization, name='Org1', name_plural_short='org1', ordering=1)
        self.org2 = mixer.blend(Organization, name='Org2', name_plural_short='org2', ordering=2)
        self.org3 = mixer.blend(Organization, name='Org3', name_plural_short='org3', ordering=3)

        self.q = mixer.blend(Question, text='Question text')
        self.r = mixer.blend(Representation, question=[self.q], label1='label1', label2='label2', label3='label3')

        QuestionStat.clear()
        OptionDict.clear()

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
        assert qs0.vars == {
            'available': True,
            'region_name': 'Europe',
            'header_by_country': 'BY COUNTRY',
            'question_text': 'Question text',
            'label1': 'label1',
            'pie_labels': ['label2', 'label3'],
            'pie_data': [30, 70],
            'bar_labels': ['SPAIN', 'FRANCE', 'ITALY'],
            'bar_series': [30, 30, -1],
            'bar_series_meta': [{'meta': 2, 'value': 30}, {'meta': 1, 'value': 30}, {'meta': 0, 'value': -1}],
            'org_labels': ['ORG1', 'ORG2', 'ORG3'],
            'org_series_meta': [{'meta': 3, 'value': 30}, {'meta': 0, 'value': -1}, {'meta': 0, 'value': -1}],
            'main_cnt': 3
        }

        qs1 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=self.c1,
                          type=QuestionStat.TYPE_AVERAGE_PERCENT)
        qs1.update_vars()
        assert qs1.vars == {
            'available': True,
            'region_name': 'Spain',
            'question_text': 'Question text',
            'header_by_country': 'BY REGION',
            'label1': 'label1',
            'pie_labels': ['label2', 'label3'],
            'pie_data': [30, 70],
            'bar_labels': ['EAST', 'WEST', 'NORTH'],
            'bar_series': [30, 30, -1],
            'bar_series_meta': [{'meta': 2, 'value': 30}, {'meta': 1, 'value': 30}, {'meta': 0, 'value': -1}],
            'org_labels': ['ORG1', 'ORG2', 'ORG3'],
            'org_series_meta': [{'meta': 3, 'value': 30}, {'meta': 0, 'value': -1}, {'meta': 0, 'value': -1}],
            'main_cnt': 3
        }

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
        assert qs0.vars == {
            'available': True,
            'region_name': 'Europe',
            'header_by_country': 'BY COUNTRY',
            'question_text': 'Question text',
            'label1': 'label1',
            'pie_labels': ['label2', 'label3'],
            'pie_data': [1, 2],
            'bar_labels': ['Spain', 'France', 'Italy'],
            'bar_negative_nums': [1, 0, -1],
            'bar_positive_nums': [1, 1, -1],
            'org_data': [
                {'label': 'ORG1', 'positiveNum': 2, 'negativeNum': 1},
                {'label': 'ORG2', 'positiveNum': -1, 'negativeNum': -1},
                {'label': 'ORG3', 'positiveNum': -1, 'negativeNum': -1},
            ]
        }

        qs1 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=self.c1,
                          type=QuestionStat.TYPE_YES_NO)
        qs1.update_vars()
        assert qs1.vars == {
            'available': True,
            'region_name': 'Spain',
            'header_by_country': 'BY REGION',
            'question_text': 'Question text',
            'label1': 'label1',
            'pie_labels': ['label2', 'label3'],
            'pie_data': [1, 2],
            'bar_labels': ['East', 'West', 'North'],
            'bar_negative_nums': [1, 0, -1],
            'bar_positive_nums': [1, 1, -1],
            'org_data': [
                {'label': 'ORG1', 'positiveNum': 2, 'negativeNum': 1},
                {'label': 'ORG2', 'positiveNum': -1, 'negativeNum': -1},
                {'label': 'ORG3', 'positiveNum': -1, 'negativeNum': -1},
            ]
        }

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
            'top1': {'x2': 4, 'x1': 6},
            'top3': {'x3': 4, 'x2': 6, 'x1': 10},
            'cnt': 10,
            'org': {
                '1': {
                    'top1': {'x2': 2, 'x1': 4},
                    'top3': {'x3': 2, 'x2': 4, 'x1': 8},
                    'cnt': 8
                },
                '2': {
                    'top1': {'x2': 2, 'x1': 2},
                    'top3': {'x3': 2, 'x2': 2, 'x1': 2},
                    'cnt': 2
                }
            }
        }

        mixer.blend(OptionDict, lower='x1', original='X1')

        qs0 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=None,
                          type=QuestionStat.TYPE_MULTISELECT_TOP)
        qs0.update_vars()
        org_table_1 = [
            (6, 'X1', (40.0, 20.0, 0)),
            (4, 'x2', (20.0, 20.0, 0))
        ]
        org_table_3 = [
            (10, 'X1', (40.0, 10.0, 0)),
            (6, 'x2', (20.0, 10.0, 0)),
            (4, 'x3', (10.0, 10.0, 0))
        ]

        top1 = {
            'table': [(6, 'X1', 60.0), (4, 'x2', 40.0)],
            'pie': {
                'data': (6, 4, 0, 0),
                'labels': ('X1', 'x2', '', ''),
                'hide_last_legend_item': 'false'
            },
            'org_table': org_table_1,
        }
        top3 = {
            'table': [(10, 'X1', 50.0), (6, 'x2', 30.0), (4, 'x3', 20.0)],
            'pie': {
                'data': (10, 6, 4, 0),
                'labels': ('X1', 'x2', 'x3', ''),
                'hide_last_legend_item': 'false'
            },
            'org_table': org_table_3,
        }

        assert qs0.vars['top1']['org_table'] == org_table_1
        assert qs0.vars['top3']['org_table'] == org_table_3

        assert qs0.vars == {
            'available': True,
            'region_name': 'Europe',
            'header_by_country': 'BY COUNTRY',
            'question_text': 'Question text',
            'label1': 'label1',
            'label2': 'label2',
            'top1': top1,
            'top3': top3,
            'org_names': ['ORG1', 'ORG2', 'ORG3']
        }

        qs1 = mixer.blend(QuestionStat,
                          representation=self.r,
                          data=data,
                          country=self.c1,
                          type=QuestionStat.TYPE_MULTISELECT_TOP)
        qs1.update_vars()
        assert qs1.vars['top1']['org_table'] == org_table_1
        assert qs1.vars['top3']['org_table'] == org_table_3
        assert qs1.vars == {
            'available': True,
            'region_name': 'Spain',
            'header_by_country': 'BY REGION',
            'question_text': 'Question text',
            'label1': 'label1',
            'label2': 'label2',
            'top1': top1,
            'top3': top3,
            'org_names': ['ORG1', 'ORG2', 'ORG3']
        }
