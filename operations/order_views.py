"""
WEEK 9 — Lab D. The orders: a list by status, the order's page, and the move.

These views show things and pass requests on. They decide nothing about the business:
every rule about moving an order is in workflow.py. The order page asks workflow.refusal()
for each possible move, so it can say before you click why a move would be refused —
and the move view asks workflow.move() again when you do click, because a button that is
hidden or greyed out protects nothing: anyone can send the POST request without the button.
"""

from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from . import workflow
from .models import SalesOrder

STATUSES = ["Draft", "Confirmed", "Shipped", "Invoiced", "Paid", "Cancelled"]


class OrderListView(LoginRequiredMixin, ListView):
    """/orders/?status=Draft — one tab per status, with how many orders are in it."""
    template_name = "operations/order_list.html"
    context_object_name = "orders"
    paginate_by = 25

    def get_queryset(self):
        self.status = self.request.GET.get("status", "Draft")
        line_total = ExpressionWrapper(F("lines__qty") * F("lines__unit_price"),
                                       output_field=DecimalField(max_digits=12, decimal_places=2))
        return (SalesOrder.objects.filter(status=self.status)
                .select_related("customer").annotate(total=Sum(line_total))
                .order_by("-order_date", "-order_no"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counts = dict(SalesOrder.objects.values_list("status").annotate(n=Count("pk")))  # GROUP BY status
        context["tabs"] = [(s, counts.get(s, 0)) for s in STATUSES]
        context["status"] = self.status
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """/orders/SO-25986/ — the order form from Week 1 as a screen, its moves, and its history."""
    model = SalesOrder
    template_name = "operations/order_detail.html"
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order, user = self.object, self.request.user
        context["lines"] = order.lines.select_related("product")
        context["total"] = workflow.order_total(order)
        # every move there is, and for each one: None if this user may make it now, or the reason why not
        context["moves"] = [{"to": s, "verb": verb, "who": " or ".join(workflow.WHO[s]),
                             "refusal": workflow.refusal(order, s, user)}
                            for s, verb in workflow.VERB.items()]
        context["history"] = (LogEntry.objects
                              .filter(content_type=ContentType.objects.get_for_model(SalesOrder), object_id=order.pk)
                              .select_related("user").order_by("action_time"))
        return context


@login_required
@require_POST
def move(request, pk):
    """POST /orders/SO-25986/move/ with to=Confirmed — ask the workflow, then show what it said."""
    order = get_object_or_404(SalesOrder, pk=pk)
    to_status = request.POST.get("to", "")
    try:
        workflow.move(order, to_status, request.user)
        messages.success(request, f"{order.pk} is now {to_status}.")
    except workflow.MoveRefused as refused:
        messages.error(request, f"Refused. {refused}")
    return redirect("order_detail", pk=pk)
