variable "dialect" {
  type = string
}

locals {
  dev_url = {
    mysql = "docker://mysql/8/dev"
    postgresql = "docker://postgres/15"
    mssql = "docker://sqlserver/2022-latest"
    sqlite = "sqlite://?mode=memory&_fk=1"
  }[var.dialect]
}

data "external_schema" "django" {
  program = [
    "poetry",
    "run",
    "python3",
    "../manage.py",
    "atlas-provider-django",
    "--dialect", var.dialect, // mysql | postgresql | sqlite
  ]
}

env "django" {
  src = data.external_schema.django.url
  dev = local.dev_url
  migration {
    dir = "file://migrations/${var.dialect}"
  }
  diff {
    skip {
      rename_constraint = true
    }
  }
  format {
    migrate {
      diff = "{{ sql . \"  \" }}"
    }
  }
}
