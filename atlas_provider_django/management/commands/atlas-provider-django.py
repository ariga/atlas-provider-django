import ast
import inspect
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

from atlas_provider_django.management.commands.migrations import get_migrations


class Dialect(str, Enum):
    mysql = "mysql"
    mariadb = "mariadb"
    sqlite = "sqlite"
    postgresql = "postgresql"
    mssql = "mssql"

    def __str__(self):
        return self.value


current_dialect = Dialect.mysql


class MockSqliteSchemaEditor(SqliteSchemaEditor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __enter__(self):
        # Running the __enter__ method of the grandparent class.
        return super(SqliteSchemaEditor, self).__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        # Running the __exit__ method of the grandparent class.
        return super(SqliteSchemaEditor, self).__exit__(exc_type, exc_value, traceback)


# Returns the database connection wrapper for the given dialect.
# Mocks some methods in order to get the sql statements without db connection.
def get_connection_by_dialect(dialect):
    conn = None
    match dialect:
        case Dialect.sqlite:
            conn = Sqlite3DatabaseWrapper({
                "ENGINE": "django.db.backends.sqlite3",
            }, "sqlite3")
            conn.SchemaEditorClass = MockSqliteSchemaEditor
        case Dialect.postgresql:
            from django.db.backends.postgresql.base import DatabaseWrapper as PGDatabaseWrapper
            from django.db.backends.postgresql.schema import DatabaseSchemaEditor as PGDatabaseSchemaEditor

            class MockPGDatabaseSchemaEditor(PGDatabaseSchemaEditor):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

                def execute(self, sql, params=()):
                    return super(PGDatabaseSchemaEditor, self).execute(sql, params)

            conn = PGDatabaseWrapper({
                "ENGINE": "django.db.backends.postgresql",
            }, "postgresql")
            conn.SchemaEditorClass = MockPGDatabaseSchemaEditor
        case Dialect.mysql:
            from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
            from django.db.backends.mysql.schema import DatabaseSchemaEditor as MySQLDatabaseSchemaEditor
            from django.db.backends.mysql.features import DatabaseFeatures as MySQLDatabaseFeatures

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

                def _supports_limited_data_type_defaults(self):
                    return True

            class MockMySQLDatabaseFeatures(MySQLDatabaseFeatures):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

                def has_native_uuid_field(self):
                    return False

                def _mysql_storage_engine(self):
                    return "InnoDB"

            conn = MySQLDatabaseWrapper({
                "ENGINE": "django.db.backends.mysql",
            }, "mysql")
            conn.SchemaEditorClass = MockMySQLDatabaseSchemaEditor
            conn.features = MockMySQLDatabaseFeatures(conn)
        case Dialect.mariadb:
            from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
            from django.db.backends.mysql.schema import DatabaseSchemaEditor as MySQLDatabaseSchemaEditor
            from django.db.backends.mysql.features import DatabaseFeatures as MySQLDatabaseFeatures

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

                def _supports_limited_data_type_defaults(self):
                    return True

            class MockMariaDBDatabaseFeatures(MySQLDatabaseFeatures):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

                def has_native_uuid_field(self):
                    return True

            conn = MySQLDatabaseWrapper({
                "ENGINE": "django.db.backends.mysql",
            }, "mysql")
            conn.SchemaEditorClass = MockMySQLDatabaseSchemaEditor
            conn.features = MockMariaDBDatabaseFeatures(conn)
        case Dialect.mssql:
            # import dynamically to avoid unixodbc not installed error on mac os for other dialects
            from mssql.base import DatabaseWrapper as MSSQLDatabaseWrapper
            conn = MSSQLDatabaseWrapper({
                "ENGINE": "mssql",
                "OPTIONS": {},
            }, "mssql")
    return conn


# MockMigrationLoader loads migrations without db connection.
class MockMigrationLoader(MigrationLoader):
    def __init__(self, connection, replace_migrations=False, load=False):
        super().__init__(connection, replace_migrations, load)

    def build_graph(self):
        self.load_disk()
        manual_migrations = get_migrations()
        self.disk_migrations = {**self.disk_migrations, **manual_migrations}
        self.applied_migrations = {}
        self.graph = MigrationGraph()
        for key, migration in self.disk_migrations.items():
            self.graph.add_node(key, migration)
        for key, migration in self.disk_migrations.items():
            self.add_internal_dependencies(key, migration)
        for key, migration in self.disk_migrations.items():
            self.add_external_dependencies(key, migration)
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
    self.output_transaction = False
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
        parser.add_argument("--dialect", type=Dialect, choices=list(Dialect),
                            help="The database dialect to use, Default: mysql",
                            default=Dialect.mysql)
        parser.add_argument("--apps", nargs="+", help="List of apps to get ddl for.")

    SqlMigrateCommand.handle = mock_handle

    def handle(self, *args, **options):
        global current_dialect
        current_dialect = options.get("dialect", Dialect.sqlite)
        selected_apps = options.get("apps", None)
        pos_directives = self.generate_pos_directives(selected_apps)
        ddl = self.get_ddl(selected_apps)
        return pos_directives + "\n\n" + ddl

    # Generate the position directives for the models in the selected apps.
    def generate_pos_directives(self, selected_apps):
        directives = []
        for model in apps.get_models():
            app_label = model._meta.app_label
            if selected_apps and app_label not in selected_apps:
                continue
            try:
                file_path = inspect.getfile(model)
            except TypeError:
                continue
            with open(file_path, "r") as f:
                source = f.read()
            tree = ast.parse(source, filename=file_path)

            class ModelVisitor(ast.NodeVisitor):
                def visit_ClassDef(self, node):
                    if node.name == model.__name__:
                        start_line = node.lineno
                        col = node.col_offset
                        end_line = getattr(node, "end_lineno", "?")
                        end_col = getattr(node, "end_col_offset", "?")
                        table_name = model._meta.db_table
                        directive = f"-- atlas:pos {table_name}[type=table] {file_path}:{start_line}:{col+1}-{end_line}:{end_col+1}"
                        directives.append(directive)
                    self.generic_visit(node)

            ModelVisitor().visit(tree)
        return "\n".join(directives)

    # Load migrations and get the sql statements describing the migrations.
    def get_ddl(self, selected_apps):
        ddl = ""
        for app_name, migration_name in get_migrations(selected_apps):
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
