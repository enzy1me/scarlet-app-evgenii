"""
WEEK 9 — the back office: eight URLs, all of them behind a login.

Customers (Lab C): the five CRUD pages for one business object.
Orders (Lab D): the list, the order's page, and the move — where staff change an order's status.
(No staff group may change an order in /admin/; only the superuser can, and the admin skips the workflow.)
"""

from django.urls import path

from . import order_views, views

urlpatterns = [
    # Lab C — customers: Create, Read (list and one), Update, Delete
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/new/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("customers/<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("customers/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer_delete"),
    # Lab D — orders
    path("orders/", order_views.OrderListView.as_view(), name="order_list"),
    path("orders/<str:pk>/", order_views.OrderDetailView.as_view(), name="order_detail"),
    path("orders/<str:pk>/move/", order_views.move, name="order_move"),
]
