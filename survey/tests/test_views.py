from mixer.backend.django import mixer
from with_asserts.mixin import AssertHTMLMixin

import pytest

from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser

from insights.users.models import User, Country
from ..models import Survey, Organization

pytestmark = pytest.mark.django_db

from ..views import start_view


class SurveyStartViewTest(AssertHTMLMixin, TestCase):
    def test_anonimous(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        req.user = AnonymousUser()
        resp = start_view(req)
        assert resp.status_code == 302, 'Should redirect to auth'

    def test_authenticated_without_country(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        req.user = User()
        self.assertRaises(ValueError, start_view, req)

    def test_authenticated_with_country_without_survey(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country)
        req.user = user
        self.assertRaises(ValueError, start_view, req)

    def test_authenticated_with_country_and_survey_without_organization(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country)
        req.user = user
        mixer.blend(Survey, active=True)
        # resp = start_view(req)
        # assert resp.status_code == 200, 'Now we a ready to start'
        self.assertRaises(ValueError, start_view, req)
        # self.assertRaises(ValueError, start_view, req, 'Survy should be set')

    def test_authenticated_with_country_and_survey_and_organization(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country)
        req.user = user
        mixer.blend(Survey, active=True)
        mixer.blend(Organization)
        resp = start_view(req)
        assert resp.status_code == 200, 'Now we a ready to start'
        self.assertNotHTML(resp, 'input[name="country"]')
        self.assertHTML(resp, 'input[name="region"]').__enter__()
        self.assertHTML(resp, 'input[name="organization"]').__enter__()
        self.assertHTML(resp, 'input[name="survey"]').__enter__()




