"""
/status/ — the application's status page.

Every real application has one: a page that says what the app is connected to and whether
everything it depends on is in order. Ours lists the eleven tables of schema v1.1, the model
that maps each one, how many rows the ORM finds, whether the model agrees with the table
(the same comparison as `python manage.py checkmodels`), and whether the model is registered
in the admin. It is also how Individual Project Parts 2 and 3 are graded: the grader opens
your public /status/ and reads it.

Reads only. Nothing on this page writes to the database.

Set STUDENT_NETID in .env (your laptop) and in Vercel → Settings → Environment Variables.
"""

import os
import re

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.shortcuts import render

# (table, model, rows in v1.0 / v1.1) — the same numbers as `python manage.py counts`
EXPECTED = [
    ("customers", "Customer", 92), ("addresses", "Address", 93), ("employees", "Employee", 5),
    ("coffees", "Coffee", 8), ("products", "Product", 25), ("inventory", "Inventory", 25),
    ("sales_orders", "SalesOrder", 987), ("order_lines", "OrderLine", 2660),
    ("shipments", "Shipment", 941), ("invoices", "Invoice", 729), ("payments", "Payment", 896),
]

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


def netid_and_n():
    """The NetID from the environment, and N: the digits in it (yl1234 -> 1234). No digits: N = 1."""
    netid = os.environ.get("STUDENT_NETID", "").strip()
    digits = re.sub(r"\D", "", netid)
    return netid, (int(digits) if digits else 1)


def compare(model, cursor, tables):
    """Does this model agree with its table? The checkmodels comparison, returning a list of issues."""
    table = model._meta.db_table
    if table not in tables:
        return ["table does not exist in this database"]
    columns = {c.name: c for c in connection.introspection.get_table_description(cursor, table)}
    constraints = connection.introspection.get_constraints(cursor, table)
    pk_cols = next((c["columns"] for c in constraints.values() if c["primary_key"]), [])
    issues, seen = [], set()
    for f in model._meta.concrete_fields:
        col = f.column
        seen.add(col)
        if col not in columns:
            issues.append(f"field '{f.name}' expects column '{col}', which the table does not have")
            continue
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
        issues.append("columns in the table but not in the model: " + ", ".join(extra))
    return issues


def status(request):
    netid, n = netid_and_n()
    db = connection.settings_dict
    on_postgres = db["ENGINE"].endswith("postgresql")
    database = f"{db['NAME']} on {db.get('HOST')}" if on_postgres else "not PostgreSQL — DATABASE_URL is not set, or not a postgresql:// string"

    by_table = {m._meta.db_table: m for m in apps.get_app_config("operations").get_models()}
    rows, error = [], None
    try:
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))
            for table, model_name, expected in EXPECTED:
                model = by_table.get(table)
                row = {"table": table, "model": model_name, "expected": expected, "count": None,
                       "times_n": None, "count_ok": False, "issues": [], "in_admin": False}
                if model is None:
                    row["issues"] = ["no model with db_table = \"%s\"" % table]
                else:
                    row["model"] = model.__name__
                    row["issues"] = compare(model, cursor, tables)
                    if table in tables:
                        try:
                            row["count"] = model.objects.count()        # SELECT COUNT(*) FROM <table>
                        except Exception as e:                      # noqa: BLE001 — report, do not crash
                            row["issues"].append("Could not count rows; check the database connection and schema.")
                    row["in_admin"] = admin.site.is_registered(model)
                if row["count"] is not None:
                    row["times_n"] = row["count"] * n
                    row["count_ok"] = row["count"] == expected
                row["match_ok"] = not row["issues"]
                row["ok"] = row["count_ok"] and row["match_ok"] and row["in_admin"]
                rows.append(row)
    except Exception as e:                                          # noqa: BLE001 — a status page must not crash
        error = "Database check failed. Check DATABASE_URL and database availability."

    # the order's lines on the order's page: an OrderLine inline on SalesOrderAdmin
    inline_ok = False
    sales_order = by_table.get("sales_orders")
    if sales_order is not None and admin.site.is_registered(sales_order):
        inline_ok = any(getattr(inl, "model", None) is by_table.get("order_lines")
                        for inl in admin.site._registry[sales_order].inlines)

    ok_rows = sum(1 for r in rows if r["ok"])
    context = {
        "netid": netid, "n": n, "database": database, "on_postgres": on_postgres,
        "debug": settings.DEBUG, "rows": rows, "error": error,
        "ok_rows": ok_rows, "total_rows": len(EXPECTED), "inline_ok": inline_ok,
        "all_ok": bool(netid) and on_postgres and error is None and ok_rows == len(EXPECTED) and inline_ok,
    }
    return render(request, "pages/status.html", context)
