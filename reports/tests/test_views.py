from mixer.backend.django import mixer
import pytest
from unittest.mock import patch

from django.core.urlresolvers import reverse, resolve
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from insights.users.models import User, Country

from survey.models import Survey, Organization

from ..models import SurveyStat, OrganizationStat, TotalEvaluator
from ..views import update_stat, ReportsView

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
        c1 = mixer.blend(Country)
        cls.c1 = c1
        c2 = mixer.blend(Country)
        o1 = mixer.blend(Organization)
        o2 = mixer.blend(Organization)
        mixer.blend(SurveyStat, survey=s1, country=None)
        mixer.blend(SurveyStat, survey=s1, country=c1)
        mixer.blend(OrganizationStat, survey=s1, country_id=None, organization=o1)
        mixer.blend(OrganizationStat, survey=s1, country=c1, organization=o1)
        TotalEvaluator.process_answers()

    def test_anonimous(self):
        req = RequestFactory().get(reverse('reports:basic_europe'))
        req.user = AnonymousUser()
        resp = ReportsView.as_view()(req)
        assert resp.status_code == 302, 'Should redirect to auth'

    def test_non_staff(self):
        req = RequestFactory().get(reverse('reports:basic_europe'))
        req.user = mixer.blend(User)
        resp = ReportsView.as_view()(req)
        # assert resp.status_code == 302, 'Should redirect to auth'
        assert resp.status_code == 200, 'Allowed'

    def test_anonimous_advanced(self):
        req = RequestFactory().get(reverse('reports:advanced_europe'))
        req.user = AnonymousUser()
        resp = ReportsView.as_view()(req)
        assert resp.status_code == 302, 'Should redirect to auth'

    def test_non_staff_advanced(self):
        req = RequestFactory().get(reverse('reports:advanced_europe'))
        req.user = mixer.blend(User)
        resp = ReportsView.as_view()(req)
        # assert resp.status_code == 302, 'Should redirect to auth'
        assert resp.status_code == 200, 'Allowed'

    def test_staff_basic(self):
        req = RequestFactory().get(reverse('reports:basic_europe'))
        req.user = mixer.blend(User, is_staff=True)
        resp = ReportsView.as_view()(req)
        resp.render()
        assert resp.status_code == 200, 'Allowed'

    def test_staff_advanced(self):
        req = RequestFactory().get(reverse('reports:advanced_europe'))
        req.user = mixer.blend(User, is_staff=True)
        resp = ReportsView.as_view()(req)
        resp.render()
        assert resp.status_code == 200, 'Allowed'

    def test_staff_basic_country(self):
        kwargs = {'country': self.c1.pk}
        req = RequestFactory().get(reverse('reports:basic_country', kwargs=kwargs))
        req.user = mixer.blend(User, is_staff=True)
        resp = ReportsView.as_view()(req, kwargs=kwargs)
        resp.render()
        assert resp.status_code == 200, 'Allowed'

    def test_staff_basic_country(self):
        kwargs = {'country': self.c1.pk}
        req = RequestFactory().get(reverse('reports:advanced_country', kwargs=kwargs))
        req.user = mixer.blend(User, is_staff=True)
        resp = ReportsView.as_view()(req, kwargs=kwargs)
        resp.render()
        assert resp.status_code == 200, 'Allowed'



