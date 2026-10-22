"""
python manage.py counts

The Week 4 row-count query, asked through the models instead of SQL. When the eleven numbers
read 92 · 93 · 5 · 8 · 25 · 25 · 987 · 2,660 · 941 · 729 · 896, your models are talking to your
v1.0 database. Tables whose model you have not written yet (Part 2) are reported as such.
"""

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import ProgrammingError

EXPECTED = [  # (db_table, rows in v1.0)
    ("customers", 92), ("addresses", 93), ("employees", 5), ("coffees", 8), ("products", 25), ("inventory", 25),
    ("sales_orders", 987), ("order_lines", 2660), ("shipments", 941), ("invoices", 729), ("payments", 896),
]


class Command(BaseCommand):
    help = "Row counts of the eleven tables of schema v1.0, through the ORM."

    def handle(self, *args, **options):
        db = connection.settings_dict
        self.stdout.write(f"database: {db['NAME']} on {db.get('HOST') or 'this laptop (SQLite — DATABASE_URL is not set)'}")
        by_table = {m._meta.db_table: m for m in apps.get_app_config("operations").get_models()}
        all_ok = True
        for table, expected in EXPECTED:
            model = by_table.get(table)
            if model is None:
                self.stdout.write(f"  {table:<13}      –   no model yet (Part 2)"); all_ok = False; continue
            try:
                n = model.objects.count()                  # SELECT COUNT(*) FROM <table>
            except ProgrammingError:
                self.stdout.write(f"  {table:<13}      –   the model exists but this database has no such table (wrong DATABASE_URL?)"); all_ok = False; continue
            ok = n == expected
            all_ok = all_ok and ok
            self.stdout.write(f"  {table:<13} {n:>6,}   {'ok' if ok else f'expected {expected:,}'}")
        self.stdout.write(self.style.SUCCESS("v1.0: all eleven counts match.") if all_ok
                          else self.style.WARNING("Not v1.0 yet."))
