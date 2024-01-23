import traceback
from enum import Enum
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.db.migrations.graph import MigrationGraph
from django.db.migrations.loader import MigrationLoader
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.sqlmigrate import Command as SqlMigrateCommand
from django.db.backends.sqlite3.base import DatabaseWrapper as Sqlite3DatabaseWrapper
from django.db.backends.sqlite3.schema import DatabaseSchemaEditor as SqliteSchemaEditor
from django.db.backends.postgresql.schema import DatabaseSchemaEditor as PGDatabaseSchemaEditor
from django.db.backends.postgresql.base import DatabaseWrapper as PGDatabaseWrapper
from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
from django.db.backends.mysql.schema import DatabaseSchemaEditor as MySQLDatabaseSchemaEditor
from django.db.backends.mysql.features import DatabaseFeatures as MySQLDatabaseFeatures

from atlas_provider_django.management.commands.migrations import get_migrations


class Dialect(str, Enum):
    mysql = "mysql"
    sqlite = "sqlite"
    postgresql = "postgresql"

    def __str__(self):
        return self.value


current_dialect = Dialect.sqlite


class MockSqliteSchemaEditor(SqliteSchemaEditor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __enter__(self):
        # Running the __enter__ method of the grandparent class.
        return super(SqliteSchemaEditor, self).__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        # Running the __exit__ method of the grandparent class.
        return super(SqliteSchemaEditor, self).__exit__(exc_type, exc_value, traceback)


class MockPGDatabaseSchemaEditor(PGDatabaseSchemaEditor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, sql, params=()):
        return super(PGDatabaseSchemaEditor, self).execute(sql, params)


class MockMySQLDatabaseSchemaEditor(MySQLDatabaseSchemaEditor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Override the method of MySQLDatabaseSchemaEditor since it checks the storage engine.
    # We assume that the storage engine is InnoDB.
    def _field_should_be_indexed(self, model, field):
        if not super(MySQLDatabaseSchemaEditor, self)._field_should_be_indexed(model, field):
            return False
        if field.get_internal_type() == "ForeignKey" and field.db_constraint:
            return False
        return not self._is_limited_data_type(field)


class MockMySQLDatabaseFeatures(MySQLDatabaseFeatures):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def has_native_uuid_field(self):
        return False


# Returns the database connection wrapper for the given dialect.
# Mocks some methods in order to get the sql statements without db connection.
def get_connection_by_dialect(dialect):
    conn = None
    if dialect == Dialect.sqlite:
        conn = Sqlite3DatabaseWrapper({
            "ENGINE": "django.db.backends.sqlite3",
        }, "sqlite3")
        conn.SchemaEditorClass = MockSqliteSchemaEditor
    elif dialect == Dialect.postgresql:
        conn = PGDatabaseWrapper({
            "ENGINE": "django.db.backends.postgresql",
        }, "postgresql")
        conn.SchemaEditorClass = MockPGDatabaseSchemaEditor
    elif dialect == Dialect.mysql:
        conn = MySQLDatabaseWrapper({
            "ENGINE": "django.db.backends.mysql",
        }, "mysql")
        conn.SchemaEditorClass = MockMySQLDatabaseSchemaEditor
        conn.features = MockMySQLDatabaseFeatures
    return conn


# MockMigrationLoader loads migrations without db connection.
class MockMigrationLoader(MigrationLoader):
    def __init__(self, connection, replace_migrations=False, load=False):
        super().__init__(connection, replace_migrations, load)

    def build_graph(self):
        self.disk_migrations = get_migrations()
        self.applied_migrations = {}
        self.unmigrated_apps = set()
        self.migrated_apps = set()
        self.graph = MigrationGraph()
        for key, migration in self.disk_migrations.items():
            self.graph.add_node(key, migration)
        self.graph.validate_consistency()
        self.graph.ensure_not_cyclic()

    # The method is almost the same as the original one, but it doesn't check if atomic transactions are enabled or not.
    # Copied from Django's MigrationLoader class: https://github.com/django/django/blob/8a1727dc7f66db7f0131d545812f77544f35aa57/django/db/migrations/loader.py#L365-L385
    # Code licensed under the BSD 3-Clause License: https://github.com/django/django/blob/main/LICENSE
    def collect_sql(self, plan):
        statements = []
        state = None
        for migration, backwards in plan:
            for operation in migration.operations:
                operation.allow_migrate_model = lambda *args: True
            with self.connection.schema_editor(
                    collect_sql=True, atomic=False
            ) as schema_editor:
                if state is None:
                    state = self.project_state(
                        (migration.app_label, migration.name), at_end=False
                    )
                state = migration.apply(state, schema_editor, collect_sql=True)
            statements.extend(schema_editor.collected_sql)
        return statements


# Override the handle method of the sqlmigrate command in order to get the sql statements without db connection.
# Copied from Django's sqlmigrate command: https://github.com/django/django/blob/8a1727dc7f66db7f0131d545812f77544f35aa57/django/core/management/commands/sqlmigrate.py#L40-L83
# Code licensed under the BSD 3-Clause License: https://github.com/django/django/blob/main/LICENSE
def mock_handle(self, *args, **options):
    connection = get_connection_by_dialect(current_dialect)
    loader = MockMigrationLoader(connection, replace_migrations=False, load=False)
    loader.build_graph()

    app_label, migration_name = options.get("app_label"), options.get("migration_name")
    try:
        apps.get_app_config(app_label)
    except LookupError as err:
        raise CommandError(str(err))
    try:
        migration = loader.get_migration_by_prefix(app_label, migration_name)
    except KeyError:
        raise CommandError(
            "Cannot find a migration matching '%s' from app '%s'. Is it in "
            "INSTALLED_APPS?" % (migration_name, app_label)
        )

    target = (app_label, migration.name)
    nodes = loader.graph.nodes.get(target)
    plan = [(nodes, False)]
    sql_statements = loader.collect_sql(plan)
    return "\n".join(sql_statements)


class Command(BaseCommand):
    help = "Import Django migrations into Atlas"

    def add_arguments(self, parser):
        parser.add_argument("--dialect", type=Dialect, choices=list(Dialect), help="The database dialect to use.",
                            default=Dialect.sqlite)

    SqlMigrateCommand.handle = mock_handle

    def handle(self, *args, **options):
        global current_dialect
        current_dialect = options.get("dialect", Dialect.sqlite)
        print(self.get_ddl())

    def create_migrations(self):
        try:
            call_command(
                "makemigrations",
                "--no-input",
                stdout=StringIO(),
                stderr=StringIO()
            )
        except Exception as e:
            traceback.print_exc()
            self.stderr.write(f"failed to create migrations, {e}")
            exit(1)

    # Load migrations and get the sql statements describing the migrations.
    def get_ddl(self):
        ddl = ""
        for app_name, migration_name in get_migrations():
            try:
                out = StringIO()
                call_command(
                    "sqlmigrate",
                    app_name,
                    migration_name,
                    stdout=out,
                    stderr=StringIO(),
                )
                ddl += out.getvalue()
            except Exception as e:
                traceback.print_exc()
                self.stderr.write(
                    f"failed to get migration {app_name} {migration_name}, {e}"
                )
                exit(1)

        return ddl
