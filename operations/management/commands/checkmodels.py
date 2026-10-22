"""
python manage.py checkmodels [app_label]

Database-first check: does each model in `operations` agree with the table that already
exists in the database? For every model: the table is there; every field's column is there,
with a compatible type and the same NULL / NOT NULL; the primary key is the same column(s);
and no column of the table is missing from the model. This is the acceptance test for a
hand-written model that maps an existing table — Django reads the live database
(connection.introspection, the same machinery inspectdb uses) and compares.
Teams: copy this file into your own app's management/commands/ and run it with your app's label.
"""

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection

# Django field type (from the model) -> acceptable types as introspected from PostgreSQL
COMPATIBLE = {
    "CharField": {"CharField", "TextField"},
    "TextField": {"TextField", "CharField"},
    "IntegerField": {"IntegerField", "AutoField", "SmallIntegerField", "BigIntegerField", "BigAutoField"},
    "AutoField": {"AutoField", "IntegerField"},
    "BigAutoField": {"BigAutoField", "BigIntegerField"},
    "DecimalField": {"DecimalField"},
    "DateField": {"DateField"},
    "DateTimeField": {"DateTimeField"},
    "BooleanField": {"BooleanField"},
}


class Command(BaseCommand):
    help = "Compare an app's models with the tables that exist in the database (default app: operations)."

    def add_arguments(self, parser):
        parser.add_argument("app_label", nargs="?", default="operations",
                            help="the app whose models to check — your team's app, for the project")

    def handle(self, *args, **options):
        db = connection.settings_dict
        self.stdout.write(f"database: {db['NAME']} on {db.get('HOST') or 'this laptop (SQLite — DATABASE_URL is not set)'}")
        problems = 0
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))
            for model in apps.get_app_config(options["app_label"]).get_models():
                table = model._meta.db_table
                if table not in tables:
                    self.stdout.write(self.style.ERROR(f"  {table:<13} table does not exist")); problems += 1; continue
                columns = {c.name: c for c in connection.introspection.get_table_description(cursor, table)}
                constraints = connection.introspection.get_constraints(cursor, table)
                pk_cols = next((c["columns"] for c in constraints.values() if c["primary_key"]), [])
                issues = []
                seen = set()
                for f in model._meta.concrete_fields:
                    col = f.column
                    seen.add(col)
                    if col not in columns:
                        issues.append(f"field {f.name!r} expects column {col!r}, which the table does not have"); continue
                    c = columns[col]
                    target = f.target_field if f.is_relation else f
                    model_type = target.get_internal_type()
                    db_type = connection.introspection.get_field_type(c.type_code, c)
                    if db_type not in COMPATIBLE.get(model_type, {model_type}):
                        issues.append(f"{col}: model says {model_type}, table says {db_type}")
                    if bool(c.null_ok) != bool(f.null) and not f.primary_key:
                        issues.append(f"{col}: model null={f.null}, table {'allows' if c.null_ok else 'forbids'} NULL")
                    if model_type == "DecimalField" and (c.precision, c.scale) != (target.max_digits, target.decimal_places):
                        issues.append(f"{col}: NUMERIC({c.precision},{c.scale}) in the table, ({target.max_digits},{target.decimal_places}) in the model")
                    if model_type == "CharField" and c.internal_size and target.max_length and c.internal_size != target.max_length:
                        issues.append(f"{col}: VARCHAR({c.internal_size}) in the table, max_length={target.max_length} in the model")
                model_pk = [model._meta.pk.column]
                if pk_cols and pk_cols != model_pk:
                    issues.append(f"primary key: table {tuple(pk_cols)}, model {tuple(model_pk)}")
                extra = sorted(set(columns) - seen)
                if extra:
                    issues.append(f"columns in the table but not in the model: {', '.join(extra)}")
                if issues:
                    problems += len(issues)
                    self.stdout.write(self.style.WARNING(f"  {table:<13} {len(issues)} issue(s)"))
                    for i in issues: self.stdout.write(f"                  - {i}")
                else:
                    self.stdout.write(f"  {table:<13} ok  ({len(columns)} columns, pk {', '.join(pk_cols)})")
        self.stdout.write(self.style.SUCCESS("Every model matches its table.") if problems == 0
                          else self.style.WARNING(f"{problems} issue(s). Fix the model, not the table."))
