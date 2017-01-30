from mixer.backend.django import mixer
import pytest
from unittest.mock import patch

from django.core.urlresolvers import reverse, resolve
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from insights.users.models import User, Country

from survey.models import Survey, Organization

from ..models import SurveyStat, OrganizationStat
from ..evaluators import TotalEvaluator
from ..views import update_stat, ReportsView, update_vars, recalculate

pytestmark = pytest.mark.django_db


class TestUpdateStat(TestCase):
    def test_anonimous(self):
        req = RequestFactory().get(reverse('reports:update_stat'))
        req.user = AnonymousUser()
        resp = update_stat(req)
        assert resp.status_code == 302, 'Should redirect to auth'

    @patch('reports.views.LastEvaluator')
    def test_user_last(self, last_evaluator):
        req = RequestFactory().get(reverse('reports:update_stat'))

        req.user = mixer.blend(User)
        resp = update_stat(req)
        assert resp.status_code == 200, 'Allowed'
        last_evaluator.process_answers.assert_called_once_with()

    @patch('reports.views.TotalEvaluator')
    def test_user_last(self, total_evaluator):
        req = RequestFactory().get(reverse('reports:update_stat') + '?total=1')

        req.user = mixer.blend(User)
        resp = update_stat(req)
        assert resp.status_code == 200, 'Allowed'
        total_evaluator.process_answers.assert_called_once_with()


class TestReports(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestReports, cls).setUpClass()
        s1 = mixer.blend(Survey, active=True)
        c1 = mixer.blend(Country, slug='ukraine')
        cls.c1 = c1
        c2 = mixer.blend(Country, slug='germany')
        o1 = mixer.blend(Organization)
        o2 = mixer.blend(Organization)
        mixer.blend(SurveyStat, survey=s1, country=None)
        mixer.blend(SurveyStat, survey=s1, country=c1)
        mixer.blend(OrganizationStat, survey=s1, country_id=None, organization=o1)
        mixer.blend(OrganizationStat, survey=s1, country=c1, organization=o1)
        TotalEvaluator.process_answers()

    def test_anonimous(self):
        kwargs = {'country': 'europe', 'report_type': 'basic'}
        req = RequestFactory().get(reverse('reports:basic', kwargs=kwargs))
        req.user = AnonymousUser()
        resp = ReportsView.as_view()(req, **kwargs)
        assert resp.status_code == 302, 'Should redirect to auth'

    def test_non_staff(self):
        kwargs = {'country': 'europe', 'report_type': 'basic'}
        req = RequestFactory().get(reverse('reports:basic', kwargs=kwargs))
        req.user = mixer.blend(User)
        resp = ReportsView.as_view()(req, **kwargs)
        # assert resp.status_code == 302, 'Should redirect to auth'
        assert resp.status_code == 200, 'Allowed'

    def test_anonimous_advanced(self):
        kwargs = {'country': 'europe', 'report_type': 'advanced'}
        req = RequestFactory().get(reverse('reports:advanced', kwargs=kwargs))
        req.user = AnonymousUser()
        resp = ReportsView.as_view()(req, **kwargs)
        assert resp.status_code == 302, 'Should redirect to auth'

    def test_non_staff_advanced(self):
        kwargs = {'country': 'europe', 'report_type': 'advanced'}
        req = RequestFactory().get(reverse('reports:advanced', kwargs=kwargs))
        req.user = mixer.blend(User)
        resp = ReportsView.as_view()(req, **kwargs)
        # assert resp.status_code == 302, 'Should redirect to auth'
        assert resp.status_code == 200, 'Allowed'

    def test_staff_basic(self):
        kwargs = {'country': 'europe', 'report_type': 'basic'}
        req = RequestFactory().get(reverse('reports:basic', kwargs=kwargs))
        req.user = mixer.blend(User, is_staff=True)
        resp = ReportsView.as_view()(req, **kwargs)
        resp.render()
        assert resp.status_code == 200, 'Allowed'

    def test_staff_advanced(self):
        kwargs = {'country': 'europe', 'report_type': 'advanced'}
        req = RequestFactory().get(reverse('reports:advanced', kwargs=kwargs))
        req.user = mixer.blend(User, is_staff=True)
        resp = ReportsView.as_view()(req, **kwargs)
        resp.render()
        assert resp.status_code == 200, 'Allowed'

    def test_staff_basic_country(self):
        kwargs = {'country': self.c1.slug, 'report_type': 'basic'}
        req = RequestFactory().get(reverse('reports:basic', kwargs=kwargs))
        req.user = mixer.blend(User, is_staff=True)
        resp = ReportsView.as_view()(req, **kwargs)
        resp.render()
        assert resp.status_code == 200, 'Allowed'

    def test_staff_advanced_country(self):
        kwargs = {'country': self.c1.slug, 'report_type': 'advanced'}
        req = RequestFactory().get(reverse('reports:advanced', kwargs=kwargs))
        req.user = mixer.blend(User, is_staff=True)
        resp = ReportsView.as_view()(req, **kwargs)
        resp.render()
        assert resp.status_code == 200, 'Allowed'

    def test_non_staff_recalculate(self):
        req = RequestFactory().get(reverse('reports:recalculate'))
        req.user = mixer.blend(User, is_staff=False)
        resp = recalculate(req)
        assert resp.status_code == 302, 'Not allowed'

    def test_staff_recalculate(self):
        req = RequestFactory().get(reverse('reports:recalculate'))
        req.user = mixer.blend(User, is_staff=True)
        resp = recalculate(req)
        assert resp.status_code == 200, 'Allowed'

    def test_non_staff_update_vars(self):
        req = RequestFactory().get(reverse('reports:update_vars'))
        req.user = mixer.blend(User, is_staff=False)
        resp = update_vars(req)
        assert resp.status_code == 302, 'Not allowed'

    def test_staff_update_vars(self):
        req = RequestFactory().get(reverse('reports:update_vars'))
        req.user = mixer.blend(User, is_staff=True)
        resp = update_vars(req)
        assert resp.status_code == 200, 'Allowed'


