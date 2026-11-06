"""
/status/ — the application's status page. Week 9 version: Part 2 and Part 3.

Every real application has one: a page that says what the app is connected to and whether
everything it depends on is in order. Ours has two sections:

  Part 3 · the rules (Week 9) — twelve checks, each one run live against YOUR code: the
           CustomerForm (rules 10 and 11), the database's CHECK and PROTECT, the workflow
           (rules 5, 9 and 2), the roles (rule 4), the customer you created through the form,
           and an order that went through its life, moved by the right people.
  Part 2 · the tables (Week 7) — the eleven tables of schema v1.1, the model that maps each one,
           its row count, whether the model agrees with the table, whether it is in the admin.

It is also how Individual Project Parts 2 and 3 are graded: the grader opens your public
/status/ and reads it.

Reads only. Nothing on this page writes to the database: it asks the form is_valid() without
saving, asks the workflow refusal() without moving, and asks Django what a delete WOULD touch.

Set STUDENT_NETID in .env (your laptop) and in Vercel → Settings → Environment Variables.
"""

import os
import re
from collections import defaultdict
from datetime import date
from types import SimpleNamespace

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.db.models import Q
from django.shortcuts import render

# (table, model, rows in v1.1) — the same numbers as `python manage.py counts`
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

ROLES = ["Owner", "Sales", "Warehouse", "Bookkeeping"]


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


def added_since_part2(by_table):
    """Rows the application itself has written since Part 2: new customers, and the shipments,
    invoices and payments that order moves create. Part 2's expected counts grow by these."""
    added = {}
    queries = {
        "customers": lambda m: m.objects.filter(customer_id__gt=92),
        "shipments": lambda m: m.objects.filter(shipment_id__gt=941),
        "invoices": lambda m: m.objects.filter(invoice_date__gte=date(2026, 9, 1)),
        "payments": lambda m: m.objects.filter(payment_id__gt=896),
    }
    for table, query in queries.items():
        try:
            added[table] = query(by_table[table]).count()
        except Exception:                                           # noqa: BLE001
            added[table] = 0
    return added


# ---------------------------------------------------------------- Part 3 · the rules

def run(label, rule, layer, test):
    """Run one check. A check that cannot run is a red row with the reason — never a crashed page."""
    try:
        ok, detail = test()
    except Exception as e:                                          # noqa: BLE001
        ok, detail = False, f"Could not run this check ({type(e).__name__}). Check the application configuration."
    return {"label": label, "rule": rule, "layer": layer, "ok": bool(ok), "detail": detail}


def part3_checks(netid):
    Customer = apps.get_model("operations", "Customer")
    SalesOrder = apps.get_model("operations", "SalesOrder")
    Employee = apps.get_model("operations", "Employee")

    def form_data(**changes):
        data = {"customer_name": "Status Check", "customer_type": "Retail", "contact_name": "",
                "email": "status-check@example.com", "phone": "", "credit_limit": "",
                "payment_terms": "", "resale_cert": ""}
        data.update(changes)
        return data

    def customer_form():
        from operations.forms import CustomerForm                   # Lab C
        return CustomerForm

    def workflow():
        from operations import workflow as wf                       # Labs D and E
        return wf

    superuser = SimpleNamespace(is_superuser=True, get_username=lambda: "superuser")
    wholesale = Customer.objects.filter(customer_type="Wholesale").order_by("pk").first()
    retail = Customer.objects.filter(customer_type="Retail").order_by("pk").first()

    def order_in(status, customer):                                 # an order that is never saved
        return SalesOrder(order_no="CHECK", status=status, customer=customer)

    # 1
    def login_required():
        from django.contrib.auth.mixins import LoginRequiredMixin
        from django.urls import Resolver404, resolve
        parts, ok = [], True
        for url in ("/customers/", "/orders/"):
            try:
                view_class = getattr(resolve(url).func, "view_class", None)
            except Resolver404:
                parts.append(f"{url} does not exist yet")
                ok = False
                continue
            guarded = view_class is not None and issubclass(view_class, LoginRequiredMixin)
            ok = ok and guarded
            parts.append(f"{url} {'asks for a login' if guarded else 'is OPEN to anyone'}")
        return ok, " · ".join(parts)

    # 2
    def rule10():
        CustomerForm = customer_form()
        used = Customer.objects.exclude(email__isnull=True).exclude(email="").order_by("pk").first()
        form = CustomerForm(data=form_data(email=used.email.upper()))
        ok = not form.is_valid() and "email" in form.errors
        return ok, (f"a new customer with the email of customer #{used.pk} is refused" if ok
                    else "a second customer with an email already in use was accepted")

    # 3
    def rule11():
        CustomerForm = customer_form()
        form = CustomerForm(data=form_data(customer_type="Wholesale", credit_limit="1000"))
        ok = not form.is_valid() and "resale_cert" in form.errors
        return ok, ("a wholesale customer without a resale certificate is refused" if ok
                    else "a wholesale customer without a resale certificate was accepted")

    # 4
    def credit_check():
        CustomerForm = customer_form()
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, "customers")
        in_db = any(c.get("check") and ("credit_limit" in name or "credit_limit" in (c.get("columns") or []))
                    for name, c in constraints.items())
        form = CustomerForm(data=form_data(customer_type="Wholesale", credit_limit="-1",
                                           resale_cert="NJ-RC-000000"))
        refused = not form.is_valid()
        detail = ("the CHECK is in the database" if in_db else "no CHECK on credit_limit in the database") + \
                 (" · the form shows a message instead of a crash" if refused else " · the form accepted −1")
        return in_db and refused, detail

    # 5
    def protect():
        from django.db.models.deletion import Collector, ProtectedError
        customer = Customer.objects.filter(orders__isnull=False).order_by("pk").first()
        try:
            Collector(using="default").collect([customer])           # what WOULD a delete touch? (deletes nothing)
            return False, f"{customer} has orders, and Django would delete it"
        except ProtectedError:
            return True, f"#{customer.pk} {customer} has {customer.orders.count()} orders: a delete is refused"

    # 6
    def cafe():
        if not netid:
            return False, "set STUDENT_NETID first"
        c = (Customer.objects.filter(Q(customer_name__iexact=f"Cafe {netid}") | Q(customer_name__iexact=f"Café {netid}"))
             .order_by("pk").first())
        if c is None:
            return False, f"no customer named Cafe {netid} — create it with New customer (Lab C)"
        if c.customer_id <= 92:
            return False, f"#{c.pk} was renamed, not created — create a new one with New customer"
        return True, f"#{c.customer_id} {c.customer_name} · {c.customer_type} · customer since {c.customer_since}"

    # 7
    def rule5():
        wf = workflow()
        tests = [("Draft", "Shipped", False), ("Shipped", "Cancelled", False), ("Paid", "Cancelled", False),
                 ("Draft", "Cancelled", True), ("Confirmed", "Shipped", True)]
        results = [(f, t, (wf.refusal(order_in(f, retail), t, superuser) is None) == allowed) for f, t, allowed in tests]
        ok = all(r for _, _, r in results)
        return ok, ("Draft → Shipped refused · Shipped → Cancelled refused · Paid is final · "
                    "Draft → Cancelled and Confirmed → Shipped allowed") if ok else \
            "wrong answer for: " + ", ".join(f"{f} → {t}" for f, t, r in results if not r)

    # 8
    def rule9():
        wf = workflow()
        r_inv = wf.refusal(order_in("Shipped", retail), "Invoiced", superuser)
        r_paid = wf.refusal(order_in("Shipped", retail), "Paid", superuser)
        w_inv = wf.refusal(order_in("Shipped", wholesale), "Invoiced", superuser)
        ok = r_inv is not None and r_paid is None and w_inv is None
        return ok, ("a shipped retail order cannot be invoiced (it goes to Paid); a shipped wholesale order can"
                    if ok else "retail and wholesale orders are not told apart after Shipped")

    # 9
    def rule2():
        wf = workflow()
        drafts = SalesOrder.objects.filter(status="Draft", customer__customer_type="Wholesale").select_related("customer")
        for order in drafts.order_by("-order_no"):                  # SO-25987 Old Bridge Bagels first
            owed, total = wf.unpaid_invoices(order.customer), wf.order_total(order)
            if order.customer.credit_limit is not None and owed + total > order.customer.credit_limit:
                reason = wf.refusal(order, "Confirmed", superuser)
                ok = reason is not None and "rule 2" in reason
                return ok, (f"{order.pk} ({order.customer}) cannot be confirmed: ${owed + total:,.2f} "
                            f"> ${order.customer.credit_limit:,.2f}" if ok
                            else f"{order.pk} would be confirmed over its credit limit")
        return False, "no Draft wholesale order over its credit limit left to test (were SO-25979 and SO-25987 changed?)"

    # 10
    def roles():
        from django.contrib.auth.models import Group, User
        missing = [r for r in ROLES if not Group.objects.filter(name=r).exists()]
        if missing:
            return False, "groups missing: " + ", ".join(missing) + " — run python manage.py setuproles (Lab E)"
        parts, ok = [], True
        for e in Employee.objects.order_by("employee_id"):
            u = User.objects.filter(username=e.first_name.lower()).first()
            good = (u is not None and u.is_active and u.is_staff and not u.is_superuser
                    and u.groups.filter(name=e.role).exists())
            ok = ok and good
            parts.append(f"{e.first_name.lower()} {e.role}" + ("" if good else " ✗"))
        return ok, "4 groups · " + " · ".join(parts)

    # 11
    def rule4():
        from django.contrib.auth.models import User
        wf = workflow()
        people = {name: User.objects.filter(username=name).first() for name in ("daniel", "priya", "tom")}
        if not all(people.values()):
            return False, "daniel, priya and tom do not all exist yet — run python manage.py setuproles (Lab E)"
        tests = [("daniel", "Draft", retail, "Confirmed", True), ("daniel", "Confirmed", retail, "Shipped", False),
                 ("daniel", "Shipped", wholesale, "Invoiced", False), ("priya", "Confirmed", retail, "Shipped", True),
                 ("priya", "Draft", retail, "Confirmed", False), ("priya", "Shipped", wholesale, "Invoiced", False),
                 ("tom", "Shipped", wholesale, "Invoiced", True), ("tom", "Confirmed", retail, "Shipped", False)]
        wrong = []
        for name, status, customer, to, allowed in tests:
            reason = wf.refusal(order_in(status, customer), to, people[name])
            if (reason is None) != allowed or (not allowed and "rule 4" not in reason):
                wrong.append(f"{name} {wf.VERB[to].lower()}")
        return not wrong, ("daniel confirms, cannot ship or invoice · priya ships, cannot confirm or invoice · "
                           "tom invoices, cannot ship") if not wrong else "wrong answer for: " + ", ".join(wrong)

    # 12
    def trail():
        from django.contrib.admin.models import LogEntry
        from django.contrib.contenttypes.models import ContentType
        moves = defaultdict(list)
        for e in (LogEntry.objects.filter(content_type=ContentType.objects.get_for_model(SalesOrder))
                  .select_related("user").order_by("action_time")):
            if "→" in (e.change_message or ""):
                roles_of = set(e.user.groups.values_list("name", flat=True))
                moves[e.object_id].append((e.change_message.split("→")[-1].strip(), e.user.get_username(), roles_of))
        if not moves:
            return False, "no order has been moved through the order page yet (Labs D and E)"

        def score(steps):
            return (any(t == "Shipped" and "Warehouse" in r for t, _, r in steps)
                    + any(t == "Invoiced" and "Bookkeeping" in r for t, _, r in steps)
                    + any(t == "Paid" and "Bookkeeping" in r for t, _, r in steps))
        order_no, steps = max(moves.items(), key=lambda kv: (score(kv[1]), len(kv[1])))
        text = f"{order_no}: " + " · ".join(f"{t} by {who}" for t, who, _ in steps)
        if score(steps) == 3:
            return True, text
        return False, text + " — still to do: shipped by Warehouse, invoiced and paid by Bookkeeping"

    return [
        run("The back office asks for a login", "who may see it", "Permission", login_required),
        run("No two customers share an email", "Rule 10", "Form", rule10),
        run("Wholesale needs a resale certificate", "Rule 11", "Form", rule11),
        run("A credit limit is never negative", "CHECK", "Database", credit_check),
        run("A customer with orders cannot be deleted", "PROTECT", "Database", protect),
        run(f"Cafe {netid or '<NetID>'} was created through the form", "your customer", "Form → database", cafe),
        run("An order moves one step at a time", "Rule 5", "Model layer", rule5),
        run("Invoices only for shipped wholesale orders", "Rule 9", "Model layer", rule9),
        run("No confirming over the credit limit", "Rule 2", "Model layer", rule2),
        run("Four roles, five staff accounts", "the roles", "Permission", roles),
        run("Only the right role makes each move", "Rule 4", "Permission", rule4),
        run("An order shipped, invoiced and paid by the right people", "the audit trail", "Model layer + permission", trail),
    ]


# ---------------------------------------------------------------- the page

def status(request):
    netid, n = netid_and_n()
    db = connection.settings_dict
    on_postgres = db["ENGINE"].endswith("postgresql")
    database = f"{db['NAME']} on {db.get('HOST')}" if on_postgres else "not PostgreSQL — DATABASE_URL is not set, or not a postgresql:// string"

    by_table = {m._meta.db_table: m for m in apps.get_app_config("operations").get_models()}
    rows, error, added = [], None, {}
    try:
        added = added_since_part2(by_table)
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))
            for table, model_name, base in EXPECTED:
                model = by_table.get(table)
                expected = base + added.get(table, 0)
                row = {"table": table, "model": model_name, "expected": expected, "added": added.get(table, 0),
                       "count": None, "times_n": None, "count_ok": False, "issues": [], "in_admin": False}
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

    # Week 9: with logins on the public site, SECRET_KEY must come from the environment (Vercel),
    # not from the fallback written in settings.py — which is public, in your repository.
    secret_from_env = bool(os.environ.get("SECRET_KEY", "").strip())

    checks = part3_checks(netid) if error is None else []
    ok_rows = sum(1 for r in rows if r["ok"])
    ok_checks = sum(1 for c in checks if c["ok"])
    context = {
        "netid": netid, "n": n, "database": database, "on_postgres": on_postgres,
        "debug": settings.DEBUG, "secret_from_env": secret_from_env, "rows": rows, "error": error,
        "ok_rows": ok_rows, "total_rows": len(EXPECTED), "inline_ok": inline_ok,
        "all_ok": bool(netid) and on_postgres and error is None and ok_rows == len(EXPECTED) and inline_ok,
        "checks": checks, "ok_checks": ok_checks, "total_checks": len(checks) or 12,
        "all_rules_ok": bool(netid) and bool(checks) and ok_checks == len(checks),
    }
    return render(request, "pages/status.html", context)
