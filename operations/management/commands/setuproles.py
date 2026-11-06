"""
WEEK 9 — Lab E.   python manage.py setuproles

The narrative's four roles become four Django GROUPS, and every person in the employees table
gets a staff ACCOUNT in the group of their role:

    employees.role      group           account
    Owner               Owner           maya
    Sales               Sales           daniel
    Warehouse           Warehouse       priya, luis
    Bookkeeping         Bookkeeping     tom

Each group also gets the admin permissions of its job: what it may view, add and change in
/admin/ — the authorization matrix (Jukic ch. 11). Shipments, invoices and payments are added
by the order workflow (workflow.py), never typed into the admin; nobody but the superuser
may delete anything.

The five accounts share one password, STAFF_PASSWORD from your .env — never from the code.
The first time, there is none yet: the command stops and prints a line to paste into .env, with a
password made up just for you by Python's secrets module (the way Lab F makes SECRET_KEY).
These accounts can log in to your PUBLIC site, so it refuses a weak password and the example
printed on the slides — everyone in the class can read that one.
Run it as often as you like: it updates the groups and the accounts, it never duplicates them.
"""

import os
import secrets

from django.contrib.auth import password_validation
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from operations.models import Employee

ALL = ["customer", "address", "employee", "coffee", "product", "inventory",
       "salesorder", "orderline", "shipment", "invoice", "payment"]
TABLE = {"customer": "customers", "address": "addresses", "employee": "employees", "coffee": "coffees",
         "product": "products", "inventory": "inventory", "salesorder": "sales_orders",
         "orderline": "order_lines", "shipment": "shipments", "invoice": "invoices", "payment": "payments"}

# The authorization matrix: for each role, the tables it may view, add, and change in /admin/.
MATRIX = {
    "Owner":       {"view": ALL,
                    "add": ["customer", "product", "coffee"],
                    "change": ["customer", "product", "coffee"]},      # rule 3: prices and credit limits
    "Sales":       {"view": ["customer", "address", "salesorder", "orderline", "product", "inventory", "coffee"],
                    "add": ["customer", "address"],
                    "change": ["customer", "address"]},
    "Warehouse":   {"view": ["customer", "address", "salesorder", "orderline", "product", "inventory", "coffee",
                             "shipment"],
                    "add": [],
                    "change": ["inventory"]},
    "Bookkeeping": {"view": ["customer", "address", "salesorder", "orderline", "shipment", "invoice", "payment"],
                    "add": [],
                    "change": []},
}


WORDS = ["arabica", "barista", "bayonne", "brew", "brunswick", "camden", "caramel", "cinnamon", "clifton",
         "cocoa", "colombia", "cortado", "crema", "cupping", "decaf", "drip", "edison", "espresso", "ethiopia",
         "filter", "grinder", "harvest", "hazelnut", "hoboken", "kenya", "kettle", "latte", "macchiato", "maple",
         "metuchen", "mocha", "newark", "origin", "paterson", "pourover", "princeton", "raritan", "roast",
         "robusta", "scarlet", "siphon", "steam", "sumatra", "tamper", "trenton", "vanilla"]
EXAMPLES = {"choose-a-real-one-2026", "kenya-trenton-origin-6104"}   # printed on the slides and in the handout


def made_up():
    """A password made by the machine, not by a person: three words and four digits, chosen by secrets."""
    return "-".join(secrets.choice(WORDS) for _ in range(3)) + f"-{secrets.randbelow(9000) + 1000}"


def use_this():
    return f"\n\n    STAFF_PASSWORD={made_up()}\n\nIt was made up just now, for you: every run makes a different one."


class Command(BaseCommand):
    help = "Create the four roles as groups and one staff account per employee (password: STAFF_PASSWORD)."

    def handle(self, *args, **options):
        password = os.environ.get("STAFF_PASSWORD", "").strip()
        if not password:
            raise CommandError("STAFF_PASSWORD is not in your .env yet. Add this line to .env (under DATABASE_URL), "
                               "save, and run this again:" + use_this())
        if password in EXAMPLES:
            raise CommandError("STAFF_PASSWORD is the example from the slides: everyone in the class can read it, "
                               "and these accounts can log in to your public site. Put this line in .env instead:"
                               + use_this())
        try:
            password_validation.validate_password(password)   # the same checks createsuperuser makes
        except ValidationError as e:
            raise CommandError("STAFF_PASSWORD is too weak: " + " ".join(e.messages) + " These accounts can log in "
                               "to your public site. Put this line in .env instead:" + use_this())

        self.stdout.write("Groups, and what each may do in /admin/ (the authorization matrix):")
        for role, rights in MATRIX.items():
            group, _ = Group.objects.get_or_create(name=role)
            codenames = [f"{action}_{model}" for action, models in rights.items() for model in models]
            group.permissions.set(Permission.objects.filter(content_type__app_label="operations",
                                                            codename__in=codenames))
            view = "all 11 tables" if rights["view"] == ALL else f"{len(rights['view'])} tables"
            adds, changes = sorted(rights["add"]), sorted(set(rights["change"]) - set(rights["add"]))
            edits = (["adds and changes " + ", ".join(TABLE[m] for m in adds)] if adds else []) + \
                    (["changes " + ", ".join(TABLE[m] for m in changes)] if changes else [])
            self.stdout.write(f"  {role:<12} views {view:<14} {'; '.join(edits) or 'changes nothing by hand'}")

        self.stdout.write("Staff accounts, one per row of the employees table:")
        for e in Employee.objects.order_by("employee_id"):
            user, created = User.objects.get_or_create(username=e.first_name.lower())
            user.first_name, user.last_name = e.first_name, e.last_name
            user.is_staff, user.is_superuser, user.is_active = True, False, True
            user.set_password(password)                      # stored as a salted hash, never as text
            user.save()
            user.groups.set([Group.objects.get(name=e.role)])
            self.stdout.write(f"  {user.username:<8} {e.role:<12} {e.first_name + ' ' + e.last_name:<18}"
                              f"{'new' if created else 'updated'}")

        self.stdout.write(self.style.SUCCESS("Done. Log in at /accounts/login/ as daniel, priya or tom."))
