from ..views import start_view, pass_view, definition_view, InstructionsView

from mixer.backend.django import mixer
from with_asserts.mixin import AssertHTMLMixin
import pytest

from django.core.urlresolvers import reverse, resolve
from django.test import RequestFactory
from test_plus import TestCase
from django.contrib.auth.models import AnonymousUser, Group
from django.utils import timezone

from insights.users.models import User, Country
from ..models import Survey, Organization, HCPCategory, Region, Answer

pytestmark = pytest.mark.django_db


class SurveyStartViewTest(AssertHTMLMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super(SurveyStartViewTest, cls).setUpClass()
        c1 = mixer.blend(Country, name='France')
        cls.c1 = c1
        c2 = mixer.blend(Country, name='Germany')
        o1 = mixer.blend(Organization)
        o2 = mixer.blend(Organization)

        now = timezone.now()
        s1 = mixer.blend(Survey, countries=[c1, c2], organizations=[o1, o2], active=True,
                         start=now - timezone.timedelta(days=1),
                         end=now + timezone.timedelta(days=1))
        cls.s1 = s1

    def test_anonimous(self):
        req = RequestFactory().get(reverse('survey:start'))
        req.user = AnonymousUser()
        resp = start_view(req)
        assert resp.status_code == 302, 'Should redirect to auth'

    def test_authenticated_without_country(self):
        req = RequestFactory().get(reverse('survey:start'))
        user = mixer.blend(User, country=None, groups=[Group.objects.get(name='Otsuka User')])
        req.user = user
        self.assertRaisesRegex(ValueError, 'User country is not set', start_view, req, self.s1.pk)

    def test_authenticated_with_country_and_survey_without_organization(self):
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country, groups=[Group.objects.get(name='Otsuka User')])
        self.s1.countries.add(country)
        req.user = user
        Organization.objects.all().delete()
        self.assertRaisesRegex(ValueError, 'no organizations assigned to selected survey',
                               start_view, req, self.s1.pk)

    def test_authenticated_with_country_and_survey_and_organization_inactive_survey(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country, groups=[Group.objects.get(name='Otsuka User')])
        req.user = user
        org = mixer.blend(Organization)

        now = timezone.now()
        s = mixer.blend(Survey, organizations=[org], active=True,
                        start=now - timezone.timedelta(days=2),
                        end=now - timezone.timedelta(days=1))
        self.assertRaisesRegex(ValueError, 'Cannot start inactive survey', start_view, req, s.pk)

    def test_survey_not_available_in_country(self):
        req = RequestFactory().get(reverse('survey:start'))
        user = mixer.blend(User, country__name="Legoland", groups=[Group.objects.get(name='Otsuka User')])
        req.user = user
        org = mixer.blend(Organization)

        country = mixer.blend(Country, name="USA")
        now = timezone.now()
        s = mixer.blend(Survey, organizations=[org], active=True, countries=[country],
                        start=now - timezone.timedelta(days=1),
                        end=now + timezone.timedelta(days=1))
        self.assertRaisesRegex(ValueError, 'not available in Legoland', start_view, req, s.pk)

    def test_authenticated_with_country_and_survey_and_organization(self):
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country, groups=[Group.objects.get(name='Otsuka User')])
        req.user = user
        org = mixer.blend(Organization)

        now = timezone.now()
        s = mixer.blend(Survey, organizations=[org], active=True, countries=[country],
                        start=now - timezone.timedelta(days=1),
                        end=now + timezone.timedelta(days=1))
        resp = start_view(req, s.pk)
        assert resp.status_code == 200, 'Start view failed'

    def test_authenticated_with_country_and_survey_and_organization_and_category(self):
        # user = mixer.blend(User, is_anonymous=True)
        req = RequestFactory().get(reverse('survey:start'))
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country, groups=[Group.objects.get(name='Otsuka User')])
        req.user = user
        self.s1.countries.add(country)
        resp = start_view(req, self.s1.pk)
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
        user = mixer.blend(User, country=country, groups=[Group.objects.get(name='Otsuka User')])
        req.user = user
        self.s1.countries.add(country)
        mixer.blend(Survey, active=True)
        organization = mixer.blend(Organization)
        self.s1.organizations.add(organization)
        mixer.blend(Organization)
        mixer.blend(HCPCategory)
        resp = start_view(req, self.s1.pk)
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
                'survey': self.s1.pk,
                'organization': organization.pk
            }
        )
        request.user = user

        resp = start_view(request, self.s1.pk)
        self.response_302(resp)
        _, _, kwargs = resolve(resp.url)
        survey_response = Answer.objects.get(pk=kwargs['id'])
        assert survey_response
        assert survey_response.user_id == user.pk
        assert survey_response.region_id == region.pk
        assert survey_response.survey_id == self.s1.pk
        assert survey_response.organization_id == organization.pk


class TestSurveyPass(AssertHTMLMixin, TestCase):
    fixtures = ['survey.json']

    def test_pass(self):
        country = mixer.blend(Country)
        user = mixer.blend(User, country=country, groups=[Group.objects.get(name='Otsuka User')])

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
        with self.assertHTML(resp, 'input'):
            pass

        request = RequestFactory().post(
            reverse('survey:start'),
            {'data[6][]': ['Health care system specific'], 'data[3][]': ['Quetapin-oral', 'Aloperidol-oral'],
             'data[4][other]': [''], 'data[6][other]': [''],
             'data[7][other]': [''], 'data[1][main]': ['33'], 'data[3][other]': [''], 'data[1][additional]': ['']}
        )
        request.user = user
        resp = pass_view(request, answer.pk)

        self.response_302(resp)
        assert resp.url == reverse('survey:thanks', kwargs={"survey_id": 1})
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
