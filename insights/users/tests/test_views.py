from django.test import RequestFactory, Client
from django.core.urlresolvers import reverse, resolve
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group
from mixer.backend.django import mixer
from insights.users.models import User, Country, TherapeuticArea
from insights.users.views import UserListView, UserCreateView, UserUpdateView
from with_asserts.mixin import AssertHTMLMixin
from django.core import mail
from freezegun import freeze_time
import datetime
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

    def _send_set_password_email(self, admin, email):
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

        return finish_url

    def test_create_user(self):
        user = mixer.blend(User, country=self.country,
                           groups=[Group.objects.get(name='Otsuka Administrator')])

        finish_url = self._send_set_password_email(user, "test@example.com")

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

    def test_set_password_for_already_deleted_user(self):
        user = mixer.blend(User, country=self.country,
                           groups=[Group.objects.get(name='Otsuka Administrator')])

        finish_url = self._send_set_password_email(user, "test@example.com")
        User.objects.filter(email="test@example.com").delete()

        c = Client()
        resp = c.get(finish_url)
        self.response_302(resp)
        assert resp.url == reverse('home')
        resp = c.get(resp.url)
        self.assertContains(resp, 'The e-mail address is not assigned to any user account')

    def test_create_user_link_expiration(self):
        user = mixer.blend(User, country=self.country,
                           groups=[Group.objects.get(name='Otsuka Administrator')])

        initial_datetime = datetime.datetime.now()
        with freeze_time(initial_datetime) as frozen_datetime:
            finish_url = self._send_set_password_email(user, "test@example.com")

            frozen_datetime.move_to(initial_datetime + datetime.timedelta(days=13, hours=23,
                                                                          minutes=59, seconds=59))
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

            frozen_datetime.move_to(initial_datetime + datetime.timedelta(days=14))
            c = Client()
            resp = c.get(finish_url)
            self.response_302(resp)
            assert resp.url == reverse('home')
            resp = c.get(resp.url)
            self.assertContains(resp, 'Your link has expired')

            resp = c.post(finish_url, {
                "password1": "Otsuka2018!!!",
                "password2": "Otsuka2018!!!",
            })
            self.response_302(resp)
            assert resp.url == reverse('home')
            resp = c.get(resp.url)
            self.assertContains(resp, 'Your link has expired')

            resp = c.post(reverse('home'), {
                "login": "test@example.com",
                "password": "Otsuka2018!!!",
            })
            self.response_200(resp)
            resp.render()
            self.assertContains(resp, 'are not correct')

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

    def test_django_token_generator_with_frozen_time(self):
        from django.contrib.auth.tokens import default_token_generator
        user = mixer.blend(User, country=self.country, is_active=True,
                           groups=[Group.objects.get(name='Otsuka User')])
        initial_datetime = datetime.datetime.now()
        with freeze_time(initial_datetime) as frozen_datetime:
            token = default_token_generator.make_token(user)
            self.assertEqual(default_token_generator.check_token(user, token), True,
                             'Newly generated token should be valid')

            frozen_datetime.move_to(initial_datetime + datetime.timedelta(hours=23))
            self.assertEqual(default_token_generator.check_token(user, token), True,
                             'Token should be valid after 23 hours')

            frozen_datetime.move_to(initial_datetime + datetime.timedelta(days=2))
            self.assertEqual(default_token_generator.check_token(user, token), False,
                             'Token should expire after two days')

    def _send_password_reset_email(self, user):
        c = Client()
        resp = c.post(reverse('account_reset_password'), {
            "email": user.email,
        })
        self.response_302(resp)
        assert resp.url == reverse('account_reset_password_done')
        resp = c.get(resp.url)
        self.response_200(resp)
        resp.render()
        self.assertContains(resp, 'Instructions on how to reset your password')

        self.assertEqual(1, len(mail.outbox), 'Should be one email')
        msg = mail.outbox[0]
        self.assertIn("Password Reset E-mail", msg.subject)
        m = re.search(r'(http:.+)\n', str(msg.body), re.MULTILINE)
        self.assertEqual(1, len(m.groups()), 'Should be only one link in email body')
        finish_url = m.group(1)

        return finish_url

    def test_password_reset_email_success(self):
        user = mixer.blend(User, country=self.country, is_active=True,
                           groups=[Group.objects.get(name='Otsuka User')])
        finish_url = self._send_password_reset_email(user)

        c = Client()
        resp = c.post(finish_url, {
            "password1": "Otsuka2018!",
            "password2": "Otsuka2018!",
        })
        self.response_302(resp)
        assert resp.url == reverse('account_reset_password_from_key_done')

        resp = c.post(reverse('home'), {
            "login": user.email,
            "password": "Otsuka2018!",
        })
        assert resp.url == reverse('survey:list')

    def test_password_reset_email_expiration(self):
        user = mixer.blend(User, country=self.country, is_active=True,
                           groups=[Group.objects.get(name='Otsuka User')])
        initial_datetime = datetime.datetime.now()
        with freeze_time(initial_datetime) as frozen_datetime:
            finish_url = self._send_password_reset_email(user)

            frozen_datetime.move_to(initial_datetime + datetime.timedelta(hours=23, minutes=59,
                                                                          seconds=59))
            c = Client()
            resp = c.get(finish_url)
            self.response_200(resp)
            with self.assertHTML(resp, 'input[name=password1], input[name=password2]') as elems:
                self.assertEqual(2, len(elems), 'Two password inputs should be shown')

            frozen_datetime.move_to(initial_datetime + datetime.timedelta(days=2))
            c = Client()
            resp = c.post(finish_url, {
                "password1": "Otsuka2018!",
                "password2": "Otsuka2018!",
            })
            self.response_200(resp)
            resp.render()
            self.assertContains(resp, 'Bad Token')


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
