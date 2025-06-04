# atlas-provider-django

Use [Atlas](https://atlasgo.io/) with [Django](https://www.djangoproject.com/) to manage your database schema as code. By connecting your Django models to Atlas,
you can define and edit your schema directly in Python. Atlas will then automatically plan and apply database schema migrations for you, 
eliminating the need to write migrations manually.

Atlas brings automated CI/CD workflows to your database, along with built-in support for [testing](https://atlasgo.io/testing/schema), [linting](https://atlasgo.io/versioned/lint),
schema [drift detection](https://atlasgo.io/monitoring/drift-detection), and [schema monitoring](https://atlasgo.io/monitoring). It also allows you to extend Django with advanced 
database objects such as triggers, row-level security, and custom functions that are not supported natively.

### Use-cases
1. [**Declarative migrations**](https://atlasgo.io/declarative/apply) - Use the Terraform-like `atlas schema apply --env django` command to apply your Django schema to the database.
2. [**Automatic migration planning**](https://atlasgo.io/versioned/diff) - Use `atlas migrate diff --env django` to automatically plan database schema changes and generate
   a migration from the current database version to the desired version defined by your Django schema.

### Installation

Install Atlas for macOS or Linux by running:
```bash
curl -sSf https://atlasgo.sh | sh
```

See [atlasgo.io](https://atlasgo.io/getting-started#installation) for more installation options.

Install the provider by running:

```bash
pip install atlas-provider-django
```

### Configuration

Add the provider to your Django project's `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...,
    'atlas_provider_django',
    ...
]
```

In your project directory, create a new file named `atlas.hcl` with the following contents:

```hcl
data "external_schema" "django" {
  program = [
    "python",
    "manage.py",
    "atlas-provider-django",
    "--dialect", "mysql" // mariadb | postgresql | sqlite | mssql
    // if you want to only load a subset of your app models, you can specify the apps by adding
    // "--apps", "app1", "app2", "app3"
  ]
}

env "django" {
  src = data.external_schema.django.url
  dev = "docker://mysql/8/dev"
  migration {
    dir = "file://migrations"
  }
  format {
    migrate {
      diff = "{{ sql . \"  \" }}"
    }
  }
}
```


### Usage

### Inspect

You can use the `atlas schema inspect` command to visualize your Django schema in Atlas Cloud.

```bash
atlas schema inspect -w --env django --url env://src
```

![inspect example](https://atlasgo.io/u/cloud/images/erd-example-v1.png)

#### Apply

You can use the `atlas schema apply` command to plan and apply a migration of your database to your current Django schema.
This works by inspecting the target database and comparing it to the Django Apps models and creating a migration plan.
Atlas will prompt you to confirm the migration plan before applying it to the database.

```bash
atlas schema apply --env django -u "mysql://root:password@localhost:3306/mydb"
```
Where the `-u` flag accepts the [URL](https://atlasgo.io/concepts/url) to the
target database.

#### Diff

Atlas supports a [versioned migrations](https://atlasgo.io/concepts/declarative-vs-versioned#versioned-migrations) 
workflow, where each change to the database is versioned and recorded in a migration file. You can use the
`atlas migrate diff` command to automatically generate a migration file that will migrate the database
from its latest revision to the current Django schema.

```bash
atlas migrate diff --env django 
````

### Supported Databases

The provider supports the following databases:
* MySQL
* MariaDB
* PostgreSQL
* SQLite
* Microsoft SQL Server

### Issues

Please report any issues or feature requests in the [ariga/atlas](https://github.com/ariga/atlas/issues) repository.

### License

This project is licensed under the [Apache License 2.0](LICENSE).
