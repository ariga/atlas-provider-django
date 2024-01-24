INSTALLED_APPS = ["atlas_provider_django", "tests.app1", "tests.app2"]

# if there are no databases defined, the tests tear down will fail
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "atlas_provider_django.db",
    }
}
