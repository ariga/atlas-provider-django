import os

from django.test import TestCase
from django.core.management import call_command
from io import StringIO


class TestAtlasProviderDjango(TestCase):
    def test_atlas_provider_django_all_apps(self):
        out = StringIO()
        call_command("atlas-provider-django", stdout=out)
        with open("tests/expected_all_apps.sql", "r") as f:
            self.assertEqual(out.getvalue().replace(os.getcwd() + '/', ''), f.read())

    def test_atlas_provider_django_specific_app(self):
        out = StringIO()
        call_command("atlas-provider-django", "--app", "app1", stdout=out)
        with open("tests/expected_app1.sql", "r") as f:
            self.assertEqual(out.getvalue().replace(os.getcwd() + '/', ''), f.read())
