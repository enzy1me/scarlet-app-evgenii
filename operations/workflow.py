"""
WEEK 9 — Labs D and E. Rule 5 as a state machine: an order's life, and who may move it.

An order is always in exactly one status. A MOVE takes it from its status to another one.
Every rule about moving an order is in this file, so that every page of ours that moves an order
(the order page today, anything we add later) asks the same questions, in the same order:

    1. Is this move allowed from this status at all?          rule 5 (with rules 6 and 9)
    2. Is THIS person allowed to make it?                     rule 4 — the roles, Lab E
    3. Does the business allow it for THIS order, now?        rule 2 — the credit limit
    4. Make it: change the status, write the document the move creates
       (a shipment, an invoice, a payment), and record who did it.

refusal() answers questions 1-3 and changes nothing. move() asks refusal(), then does step 4.
(The admin is not one of our pages: no staff group may change an order there; only the superuser
can, and the admin skips these questions.)
"""

from decimal import Decimal

from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from .models import Invoice, OrderLine, Payment, SalesOrder, Shipment

# ---------------------------------------------------------------- the two tables of rules

# Rule 5: from each status, the statuses an order may move to. Anything else is refused.
NEXT = {
    "Draft":     ["Confirmed", "Cancelled"],
    "Confirmed": ["Shipped", "Cancelled"],
    "Shipped":   ["Invoiced"],      # a retail order goes Shipped → Paid instead (rules 6 and 9)
    "Invoiced":  ["Paid"],
    "Paid":      [],                # the end
    "Cancelled": [],                # the end
}

# Who may move an order INTO each status: Scarlet's jobs, as the case describes them (Daniel confirms,
# the warehouse ships, Tom invoices and records payments). This keeps rule 4 — whoever takes or ships an
# order does not invoice it — and is stricter: each move belongs to one job. A role is a Django group (Lab E).
WHO = {
    "Confirmed": ["Sales"],
    "Shipped":   ["Warehouse"],
    "Invoiced":  ["Bookkeeping"],
    "Paid":      ["Bookkeeping"],
    "Cancelled": ["Sales", "Owner"],
}

# What the button says for each move.
VERB = {"Confirmed": "Confirm", "Shipped": "Ship", "Invoiced": "Invoice",
        "Paid": "Record payment", "Cancelled": "Cancel"}


class MoveRefused(Exception):
    """A move the business does not allow. The message names the rule, in words a clerk understands."""


# ---------------------------------------------------------------- questions 1-3

def next_statuses(order):
    """Rule 5: where this order may go next."""
    if order.status == "Shipped" and order.customer.customer_type == "Retail":
        return ["Paid"]             # rule 6: a retail order was paid by card at checkout; rule 9: no invoice
    return NEXT.get(order.status, [])


def in_role(user, to_status):
    """Rule 4: is this user in a group that may move an order into to_status?"""
    if user.is_superuser:           # on purpose: the superuser passes this question for every move
        return True                 # (as in Django's own permission checks); questions 1 and 3 still apply
    return user.groups.filter(name__in=WHO[to_status]).exists()


def order_total(order):
    """The order's total: the sum of qty × unit_price over its lines (what v_order_lines computes)."""
    line_total = ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=12, decimal_places=2))
    return OrderLine.objects.filter(order=order).aggregate(t=Sum(line_total))["t"] or Decimal("0")


def unpaid_invoices(customer):
    """What the customer owes: the totals of its orders that are invoiced and not yet paid."""
    line_total = ExpressionWrapper(F("qty") * F("unit_price"), output_field=DecimalField(max_digits=12, decimal_places=2))
    owed = (OrderLine.objects.filter(order__customer=customer, order__status="Invoiced")
            .aggregate(t=Sum(line_total))["t"])
    return owed or Decimal("0")


def refusal(order, to_status, user):
    """Why this user may not move this order to to_status — or None if the move is allowed. Changes nothing."""
    # 1 · rule 5 — the order's life: Draft → Confirmed → Shipped → Invoiced → Paid
    if to_status not in next_statuses(order):
        return f"An order that is {order.status} cannot become {to_status} (rule 5)."
    # 2 · rule 4 — the right person for the job
    if not in_role(user, to_status):
        return (f"{VERB[to_status]} is a job for {' or '.join(WHO[to_status])}; "
                f"{user.get_username() or 'this visitor'} is not in that role (rule 4).")
    # 3 · rule 2 — a wholesale order may be confirmed only within the customer's credit limit
    if to_status == "Confirmed" and order.customer.customer_type == "Wholesale":
        owed, total = unpaid_invoices(order.customer), order_total(order)
        limit = order.customer.credit_limit or Decimal("0")
        if owed + total > limit:
            return (f"{order.customer} owes ${owed:,.2f} on unpaid invoices; with this order (${total:,.2f}) "
                    f"that is ${owed + total:,.2f}, over its credit limit of ${limit:,.2f} (rule 2).")
    return None


# ---------------------------------------------------------------- step 4

def next_invoice_no(day):
    """Invoices are numbered YEAR-NNNN, one sequence per year (2026-0481 is the last one in the data)."""
    prefix = f"{day.year}-"
    last = (Invoice.objects.filter(invoice_no__startswith=prefix)
            .order_by("-invoice_no").values_list("invoice_no", flat=True).first())
    number = int(last.split("-")[1]) + 1 if last else 1
    return f"{prefix}{number:04d}"   # two clerks at the same second could get the same number: Week 10


def move(order, to_status, user):
    """Move the order to to_status — or raise MoveRefused with the reason."""
    reason = refusal(order, to_status, user)
    if reason:
        raise MoveRefused(reason)

    today = timezone.localdate()
    was = order.status
    with transaction.atomic():      # all of it or none of it — Week 10 is about this line
        # the document each move creates (rule 9: a packing slip only for a shipped order,
        # an invoice only for a shipped wholesale order)
        if to_status == "Shipped":
            carrier = "Van" if order.customer.customer_type == "Wholesale" else "UPS"   # narrative §3
            Shipment.objects.create(order=order, ship_date=today, carrier=carrier)
        elif to_status == "Invoiced":
            Invoice.objects.create(invoice_no=next_invoice_no(today), order=order, invoice_date=today)
        elif to_status == "Paid":
            retail = order.customer.customer_type == "Retail"
            Payment.objects.create(order=order, paid_date=order.order_date if retail else today)  # rule 6

        order.status = to_status
        order.save(update_fields=["status"])     # UPDATE sales_orders SET status = … WHERE order_no = …

        # the audit trail: who moved which order, from what, to what, and when. The same log
        # the admin keeps for every change made in /admin/ (an order's History page shows it).
        LogEntry.objects.create(
            user=user, action_flag=CHANGE,
            content_type=ContentType.objects.get_for_model(SalesOrder),
            object_id=order.pk, object_repr=str(order),
            change_message=f"{was} → {to_status}",
        )
