import traceback
from enum import Enum
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.db.migrations.exceptions import NodeNotFoundError
from django.db.migrations.graph import MigrationGraph
from django.db.migrations.loader import MigrationLoader, AmbiguityError
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.sqlmigrate import Command as SqlMigrateCommand
from django.db.backends.sqlite3.base import DatabaseWrapper as Sqlite3DatabaseWrapper
from django.db.backends.sqlite3.schema import DatabaseSchemaEditor as SqliteSchemaEditor


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
        return super(SqliteSchemaEditor, self).__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        return super(SqliteSchemaEditor, self).__exit__(exc_type, exc_value, traceback)


# Returns the database connection wrapper for the given dialect.
# Mocks some methods in order to get the sql statements without db connection.
def get_connection_by_dialect(dialect):
    if dialect == Dialect.sqlite:
        conn = Sqlite3DatabaseWrapper({
            "ENGINE": "django.db.backends.sqlite3",
        }, "sqlite3")
        conn.SchemaEditorClass = MockSqliteSchemaEditor
        return conn


# MockMigrationLoader loads migrations without db connection.
class MockMigrationLoader(MigrationLoader):
    def __init__(self, connection, replace_migrations=False, load=True):
        super().__init__(connection, replace_migrations, load)

    # The method is almost the same as the original one, but it doesn't check if the migrations are applied or not.
    def build_graph(self):
        self.load_disk()
        self.applied_migrations = {}
        self.graph = MigrationGraph()
        self.replacements = {}
        for key, migration in self.disk_migrations.items():
            self.graph.add_node(key, migration)
            if migration.replaces:
                self.replacements[key] = migration
        for key, migration in self.disk_migrations.items():
            self.add_internal_dependencies(key, migration)
        for key, migration in self.disk_migrations.items():
            self.add_external_dependencies(key, migration)
        if self.replace_migrations:
            for key, migration in self.replacements.items():
                applied_statuses = [
                    (target in self.applied_migrations) for target in migration.replaces
                ]
                if all(applied_statuses):
                    self.applied_migrations[key] = migration
                else:
                    self.applied_migrations.pop(key, None)
                if all(applied_statuses) or (not any(applied_statuses)):
                    self.graph.remove_replaced_nodes(key, migration.replaces)
                else:
                    self.graph.remove_replacement_node(key, migration.replaces)
        try:
            self.graph.validate_consistency()
        except NodeNotFoundError as exc:
            reverse_replacements = {}
            for key, migration in self.replacements.items():
                for replaced in migration.replaces:
                    reverse_replacements.setdefault(replaced, set()).add(key)
            if exc.node in reverse_replacements:
                candidates = reverse_replacements.get(exc.node, set())
                is_replaced = any(
                    candidate in self.graph.nodes for candidate in candidates
                )
                if not is_replaced:
                    tries = ", ".join("%s.%s" % c for c in candidates)
                    raise NodeNotFoundError(
                        "Migration {0} depends on nonexistent node ('{1}', '{2}'). "
                        "Django tried to replace migration {1}.{2} with any of [{3}] "
                        "but wasn't able to because some of the replaced migrations "
                        "are already applied.".format(
                            exc.origin, exc.node[0], exc.node[1], tries
                        ),
                        exc.node,
                    ) from exc
            raise
        self.graph.ensure_not_cyclic()

    # The method is almost the same as the original one, but it doesn't check if atomic transactions are enabled or not.
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
def mock_handle(self, *args, **options):
    connection = get_connection_by_dialect(current_dialect)
    loader = MockMigrationLoader(connection, replace_migrations=False, load=False)
    loader.build_graph()

    app_label, migration_name = options["app_label"], options["migration_name"]
    try:
        apps.get_app_config(app_label)
    except LookupError as err:
        raise CommandError(str(err))
    if app_label not in loader.migrated_apps:
        raise CommandError("App '%s' does not have migrations" % app_label)
    try:
        migration = loader.get_migration_by_prefix(app_label, migration_name)
    except AmbiguityError:
        raise CommandError(
            "More than one migration matches '%s' in app '%s'. Please be more "
            "specific." % (migration_name, app_label)
        )
    except KeyError:
        raise CommandError(
            "Cannot find a migration matching '%s' from app '%s'. Is it in "
            "INSTALLED_APPS?" % (migration_name, app_label)
        )

    target = (app_label, migration.name)
    plan = [(loader.graph.nodes[target], False)]
    sql_statements = loader.collect_sql(plan)
    return "\n".join(sql_statements)


def order_migrations_by_dependency():
    loader = MigrationLoader(None)
    graph = loader.graph
    all_nodes = graph.nodes
    return graph._generate_plan(nodes=all_nodes, at_end=True)


class Command(BaseCommand):
    help = "Import Django migrations into Atlas"

    def add_arguments(self, parser):
        parser.add_argument("--dialect", type=Dialect, choices=list(Dialect), help="The database dialect to use.",
                            default=Dialect.sqlite)

    SqlMigrateCommand.handle = mock_handle

    def handle(self, *args, **options):
        global current_dialect
        current_dialect = options["dialect"]
        migrations = self.get_migrations()
        print(migrations)

    def get_migrations(self):
        migration_loader = MigrationLoader(None, ignore_no_migrations=True)
        migration_loader.load_disk()
        migrations = ""
        ordered_migrations = order_migrations_by_dependency()
        for app_name, migration_name in ordered_migrations:
            try:
                out = StringIO()
                call_command(
                    "sqlmigrate",
                    app_name,
                    migration_name,
                    stdout=out,
                    stderr=StringIO(),
                )
                migrations += out.getvalue()
            except Exception as e:
                traceback.print_exc()
                self.stderr.write(
                    f"failed to get migration {app_name} {migration_name}, {e}"
                )
                exit(1)

        return migrations
