from django.test import RequestFactory, Client
from django.core.urlresolvers import reverse, resolve
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group
from mixer.backend.django import mixer
from insights.users.models import User, Country, TherapeuticArea
from insights.users.views import UserListView, UserCreateView, UserUpdateView
from with_asserts.mixin import AssertHTMLMixin
from django.core import mail
import re

from test_plus.test import TestCase

from ..views import (
    UserRedirectView,
)


class BaseUserTestCase(TestCase):

    def setUp(self):
        self.user = self.make_user()
        self.factory = RequestFactory()


class TestUserRedirectView(BaseUserTestCase):

    def test_get_redirect_url(self):
        # Instantiate the view directly. Never do this outside a test!
        view = UserRedirectView()
        # Generate a fake request
        request = self.factory.get('/fake-url')
        # Attach the user to the request
        request.user = self.user
        # Attach the request to the view
        view.request = request
        # Expect: '/users/testuser/', as that is the default username for
        #   self.make_user()
        self.assertEqual(
            view.get_redirect_url(),
            '/users/testuser'
        )


class TestUserPermissions(TestCase, AssertHTMLMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = mixer.blend(Country)
        cls.therapeutic_area = mixer.blend(TherapeuticArea)

    def test_non_admin_forbidden(self):
        for user in (mixer.blend(User, country=self.country, groups=[Group.objects.get(name='Otsuka User')]),
                     mixer.blend(User, country=self.country, groups=[])):

            req = RequestFactory().get(reverse('users:list'))
            req.user = user
            self.assertRaises(PermissionDenied, UserListView.as_view(), req)

            req = RequestFactory().get(reverse('users:create_user'))
            req.user = user
            self.assertRaises(PermissionDenied, UserCreateView.as_view(), req)

            req = RequestFactory().get(reverse('users:update_user', kwargs={'username': user.email}))
            req.user = user
            self.assertRaises(PermissionDenied, UserUpdateView.as_view(), req, user.email)

    def test_admin_granted(self):
        user = mixer.blend(User, country=self.country,
                           groups=[Group.objects.get(name='Otsuka Administrator')])

        req = RequestFactory().get(reverse('users:list'))
        req.user = user
        resp = UserListView.as_view()(req)
        self.response_200(resp)
        resp.render()
        with self.assertHTML(resp, '.users-list>tbody>tr') as elems:
            self.assertEqual(1, len(elems), 'More than one user is shown')

        req = RequestFactory().get(reverse('users:create_user'))
        req.user = user
        resp = UserCreateView.as_view()(req)
        self.response_200(resp)
        resp.render()
        with self.assertHTML(resp, 'input[name=email]') as elems:
            self.assertEqual(1, len(elems), 'Should be only one email input')

        req = RequestFactory().get(reverse('users:update_user', kwargs={'username': user.email}))
        req.user = user
        resp = UserUpdateView.as_view()(req, username=user.username)
        self.response_200(resp)
        resp.render()
        with self.assertHTML(resp, 'input[name=email]') as (elem,):
            self.assertEqual(elem.value, user.email)

    def test_create_user(self):
        user = mixer.blend(User, country=self.country,
                           groups=[Group.objects.get(name='Otsuka Administrator')])
        c = Client()
        c.force_login(user)
        resp = c.post(reverse('users:create_user'), {
            "email": "test@example.com",
            "name": "Test User",
            "therapeutic_areas": [self.therapeutic_area.pk],
            "country": self.country.pk,
            "groups": [Group.objects.get(name='Otsuka User').pk],
        })
        self.response_302(resp)
        assert resp.url == reverse('users:list')

        resp = c.get(resp.url)
        resp.render()
        with self.assertHTML(resp, '.users-list>tbody>tr') as elems:
            self.assertEqual(2, len(elems), 'New user should be shown')
            self.assertIn("Test User", elems[1].find("td/a").text)

        self.assertEqual(1, len(mail.outbox), 'Should be one email')
        msg = mail.outbox[0]
        self.assertIn("Finish your account setup", msg.subject)
        m = re.search(r'href="(.+)"', str(msg.body), re.MULTILINE)
        self.assertEqual(1, len(m.groups()), 'Should be only one href in email body')
        finish_url = m.group(1)

        c = Client()
        resp = c.get(finish_url)
        with self.assertHTML(resp, 'input[name=password1], input[name=password2]') as elems:
            self.assertEqual(2, len(elems), 'Two password inputs should be shown')

        resp = c.post(finish_url, {
            "password1": "Otsuka2018!",
            "password2": "Otsuka2018!",
        })
        self.response_302(resp)
        assert resp.url == reverse('home')

        resp = c.post(resp.url, {
            "login": "test@example.com",
            "password": "Otsuka2018!",
        })
        assert resp.url == reverse('survey:list')

    def test_set_password_for_user_by_admin(self):
        admin = mixer.blend(User, country=self.country,
                            groups=[Group.objects.get(name='Otsuka Administrator')])

        email = "test@example.com"

        c = Client()
        c.force_login(admin)
        resp = c.post(reverse('users:create_user'), {
            "email": "test@example.com",
            "name": "Test User",
            "therapeutic_areas": [self.therapeutic_area.pk],
            "country": self.country.pk,
            "groups": [Group.objects.get(name='Otsuka User').pk],
        })
        self.response_302(resp)
        assert resp.url == reverse('users:list')

        resp = c.post(reverse('users:set_password', kwargs={"username": email}), {
            "password1": "Otsuka2018!",
            "password2": "Otsuka2018!",
        })
        self.response_302(resp)

        c = Client()
        resp = c.post(reverse('home'), {
            "login": email,
            "password": "Otsuka2018!",
        })
        assert resp.url == reverse('survey:list')

        c = Client()
        c.force_login(admin)
        resp = c.post(reverse('users:set_password', kwargs={"username": email}), {
            "password1": "Otsuka2018!New",
            "password2": "Otsuka2018!New",
        })
        self.response_302(resp)

        c = Client()
        resp = c.post(reverse('home'), {
            "login": email,
            "password": "Otsuka2018!New",
        })
        assert resp.url == reverse('survey:list')

    def test_no_superusers_in_list(self):
        user = mixer.blend(User, country=self.country, groups=[Group.objects.get(name='Otsuka Administrator')])
        mixer.blend(User, country=self.country, is_superuser=True)

        req = RequestFactory().get(reverse('users:list'))
        req.user = user
        resp = UserListView.as_view()(req)
        self.response_200(resp)
        resp.render()
        with self.assertHTML(resp, '.users-list>tbody>tr') as elems:
            self.assertEqual(1, len(elems), 'Super user should not be shown')

    def test_superusers_in_list(self):
        mixer.blend(User, country=self.country, groups=[Group.objects.get(name='Otsuka Administrator')])
        user = mixer.blend(User, country=self.country, is_superuser=True)

        req = RequestFactory().get(reverse('users:list'))
        req.user = user
        resp = UserListView.as_view()(req)
        self.response_200(resp)
        resp.render()
        with self.assertHTML(resp, '.users-list>tbody>tr') as elems:
            self.assertEqual(2, len(elems), 'Super user should be shown for superusers')


# class TestUserUpdateView(BaseUserTestCase):

#     def setUp(self):
#         # call BaseUserTestCase.setUp()
#         super(TestUserUpdateView, self).setUp()
#         # Instantiate the view directly. Never do this outside a test!
#         self.view = UserUpdateView()
#         # Generate a fake request
#         request = self.factory.get('/fake-url')
#         # Attach the user to the request
#         request.user = self.user
#         # Attach the request to the view
#         self.view.request = request

#     def test_get_success_url(self):
#         # Expect: '/users/testuser/', as that is the default username for
#         #   self.make_user()
#         self.assertEqual(
#             self.view.get_success_url(),
#             '/users/'
#         )

#     def test_get_object(self):
#         # Expect: self.user, as that is the request's user object
#         self.assertEqual(
#             self.view.get_object(),
#             self.user
#         )
