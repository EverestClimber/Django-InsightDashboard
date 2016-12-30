from mixer.backend.django import mixer
from with_asserts.mixin import AssertHTMLMixin

import pytest

from django.core.urlresolvers import reverse, resolve
from django.test import RequestFactory
from test_plus import TestCase
from django.contrib.auth.models import AnonymousUser

from insights.users.models import User, Country
from ..models import Survey, Organization, HCPCategory, Region, Response

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
        self.assertRaises(ValueError, start_view, req)

    def test_authenticated_with_country_and_survey_and_organization(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country)
        req.user = user
        mixer.blend(Survey, active=True)
        mixer.blend(Organization)
        self.assertRaises(ValueError, start_view, req)

    def test_authenticated_with_country_and_survey_and_organization(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country)
        req.user = user
        mixer.blend(Survey, active=True)
        mixer.blend(Organization)
        mixer.blend(Organization)
        mixer.blend(HCPCategory)
        mixer.blend(HCPCategory)
        resp = start_view(req)
        assert resp.status_code == 200, 'Now we a ready to start'
        self.assertNotHTML(resp, 'input[name="country"]')
        self.assertHTML(resp, 'input[name="region"]').__enter__()
        self.assertHTML(resp, 'input[name="organization"]').__enter__()
        self.assertHTML(resp, 'input[name="survey"]').__enter__()

    def test_authenticated_with_country_and_survey_and_organization_and_region(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        region = mixer.blend(Region, country=country)
        mixer.blend(Region, country=country)
        mixer.blend(Region, country=country)
        user = mixer.blend(User, country=country)
        req.user = user
        survey = mixer.blend(Survey, active=True)
        mixer.blend(Survey, active=True)
        organization = mixer.blend(Organization)
        mixer.blend(Organization)
        hcp = mixer.blend(HCPCategory)
        mixer.blend(HCPCategory)
        resp = start_view(req)
        assert resp.status_code == 200, 'Now we a ready to start'
        self.assertNotHTML(resp, 'input[name="country"]')
        self.assertHTML(resp, 'input[name="region"]').__enter__()
        self.assertHTML(resp, 'input[name="organization"]').__enter__()
        self.assertHTML(resp, 'input[name="survey"]').__enter__()

        request = RequestFactory().post(
            reverse('survey:start'),
            {
                'country': country.pk,
                'region': region.pk,
                'survey': survey.pk,
                'organization': organization.pk,
                'hcp': hcp.pk
            }
        )
        request.user = user

        resp = start_view(request)
        self.response_302(resp)
        _, _, kwargs = resolve(resp.url)
        survey_response = Response.objects.get(pk=kwargs['id'])
        assert survey_response
        assert survey_response.user_id == user.pk
        assert survey_response.region_id == region.pk
        assert survey_response.survey_id == survey.pk
        assert survey_response.organization_id == organization.pk
        assert survey_response.hcp_category_id == hcp.pk



