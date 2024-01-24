from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.db.migrations.loader import MigrationLoader
from django.apps import apps as all_apps


# Creates the migrations of the installed apps from empty baseline and returns them as a dictionary
def get_migrations(apps=None):
    autodetector = MigrationAutodetector(
        ProjectState(),
        ProjectState.from_apps(all_apps),
    )
    loader = MigrationLoader(None, ignore_no_migrations=True)
    changes = autodetector.changes(
        graph=loader.graph,
        trim_to_apps=None,
        convert_apps=None,
    )
    migrations = {}
    for app_label, app_migrations in changes.items():
        if apps and app_label not in apps:
            continue
        migrations[(app_label, app_migrations[0].name)] = app_migrations[0]
    return migrations
