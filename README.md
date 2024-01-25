# atlas-provider-django

Load [Django](https://www.djangoproject.com/) models into an [Atlas](https://atlasgo.io) project.

### Use-cases
1. **Declarative migrations** - use a Terraform-like `atlas schema apply --env django` to apply your Django schema to the database.
2. **Automatic migration planning** - use `atlas migrate diff --env django` to automatically plan a migration from the current database version to the Django schema.

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