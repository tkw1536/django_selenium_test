from __future__ import annotations

from unittest import mock

from django_selenium_test import IntegrationTest


class ExampleIntegrationTest(IntegrationTest):
    user = "alice"

    def setUp(self):

        # crate the alice user
        from django.contrib.auth.hashers import make_password
        from django.contrib.auth.models import User

        alice = User.objects.create(
            username="alice", password=make_password("topsecret"), is_active=True
        )

        # create the alice user
        super().setUp()

    def test_auto_login(self):
        """ Checks that the user was actually logged in """

        element = self.load_live_url("core", selector="#user")
        self.assertEqual(element.text, "The logged on user is alice.")
        self.assertIsNone(self.user.last_login)
