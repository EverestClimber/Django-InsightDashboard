from unittest.mock import MagicMock
from mixer.backend.django import mixer
from with_asserts.mixin import AssertHTMLMixin
import pytest

from django.core.urlresolvers import reverse, resolve
from django.test import RequestFactory
from test_plus import TestCase
from django.contrib.auth.models import AnonymousUser

from insights.users.models import User, Country
from ..models import Survey, Organization, HCPCategory, Region, Answer

pytestmark = pytest.mark.django_db

from ..views import start_view, pass_view, definition_view, InstructionsView


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
        resp = start_view(req)
        # https://app.asana.com/0/inbox/227388348049228/248961928381934/248963770361765
        assert resp.status_code == 200, 'Woring without organization now also is possible'

    def test_authenticated_with_country_and_survey_and_organization_and_category(self):
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
                'organization': organization.pk
            }
        )
        request.user = user

        resp = start_view(request)
        self.response_302(resp)
        _, _, kwargs = resolve(resp.url)
        survey_response = Answer.objects.get(pk=kwargs['id'])
        assert survey_response
        assert survey_response.user_id == user.pk
        assert survey_response.region_id == region.pk
        assert survey_response.survey_id == survey.pk
        assert survey_response.organization_id == organization.pk



class TestSurveyPass(AssertHTMLMixin, TestCase):
    fixtures = ['survey.json']

    def test_pass(self):
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country)

        answer = mixer.blend(Answer,
                             user=user,
                             country=country,
                             organization_id=1,
                             hcp_category_id=1,
                             survey_id=1)

        kwargs = {'id': answer.pk}
        request = RequestFactory().get(reverse('survey:pass', kwargs=kwargs))
        request.user = user
        resp = pass_view(request, answer.pk)
        self.response_200(resp)
        with self.assertHTML(resp, 'input'): pass

        request = RequestFactory().post(
            reverse('survey:start'),
            {'data[6][]': ['Health care system specific'], 'data[3][]': ['Quetapin-oral', 'Aloperidol-oral'],
             'data[4][other]': [''], 'data[6][other]': [''],
             'data[7][other]': [''], 'data[1][main]': ['33'], 'data[3][other]': [''], 'data[1][additional]': ['']}
        )
        request.user = user
        resp = pass_view(request, answer.pk)

        self.response_302(resp)
        assert resp.url == reverse('survey:thanks')
        answer.refresh_from_db()
        assert answer.body


class TestSurveyDefinition(AssertHTMLMixin, TestCase):

    def test_defines_unauthorized(self):
        request = RequestFactory().get(reverse('survey:definition'))
        request.user = AnonymousUser()
        response = definition_view(request)
        self.response_302(response)
        assert '/accounts/login/' in response.url


    def test_definitions_wo_cookies(self):
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country)
        request = RequestFactory().get(reverse('survey:definition'))
        request.user = user
        response = definition_view(request)
        self.response_302(response)
        assert '/survey/instructions/' in response.url

    def test_with_cookies(self):
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country)
        request = RequestFactory().get(reverse('survey:definition'))
        request.user = user
        request.COOKIES[InstructionsView.cookie_name] = True
        response = definition_view(request)
        self.response_200(response)
        with self.assertHTML(response, 'a.btn'):
            pass


class TestSurveyInstructions(AssertHTMLMixin, TestCase):
    def test_instructions_unauthorized(self):
        request = RequestFactory().get(reverse('survey:instructions'))
        request.user = AnonymousUser()
        response = definition_view(request)
        self.response_302(response)
        assert '/accounts/login/' in response.url

    def test_with_cookies(self):
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country)
        request = RequestFactory().get(reverse('survey:instructions'))
        request.user = user
        response = InstructionsView.as_view()(request)
        response.render()
        self.response_200(response)
        assert response.cookies.get(InstructionsView.cookie_name)
        with self.assertHTML(response, 'a.btn'):
            pass
