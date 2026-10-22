"""
The admin is the back office: every table of schema v1.0, browsable and editable by staff,
with no code written for the screens themselves. Register a model; Django builds the pages.

The options below are the ones worth knowing this week:
  list_display   the columns of the list page
  list_filter    the filters in the right-hand sidebar
  search_fields  the search box (use "fk__field" to search through a foreign key)
  ordering       default sort
  inlines        child rows edited on the parent's page (an order's lines on the order)
  readonly_fields / list_editable  what may be changed where
"""

from django.contrib import admin

from .models import (Address, Coffee, Customer, Employee, Inventory, Invoice, OrderLine,
                     Payment, Product, SalesOrder, Shipment)


# ---------------------------------------------------------------- master data

@admin.register(Coffee)
class CoffeeAdmin(admin.ModelAdmin):
    list_display = ("coffee", "origin", "roast_level", "supplier", "green_lbs_on_hand", "last_green_delivery")
    list_filter = ("roast_level", "supplier")
    search_fields = ("coffee", "origin")


class InventoryInline(admin.StackedInline):
    model = Inventory
    can_delete = False
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "product_name", "coffee", "size", "retail_price", "wholesale_price", "active")
    list_filter = ("active", "size", "coffee__roast_level")
    search_fields = ("sku", "product_name", "coffee__coffee")
    list_editable = ("active",)            # the owner takes a product off the catalog from the list page
    ordering = ("sku",)
    inlines = [InventoryInline]            # stock, on the product's page


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("product", "on_hand_bags", "reorder_point", "last_roast_date", "below_reorder_point")
    list_editable = ("on_hand_bags",)      # the warehouse adjusts stock here — and only stock
    ordering = ("product",)

    @admin.display(boolean=True, description="Reorder?")
    def below_reorder_point(self, obj):
        return obj.on_hand_bags < obj.reorder_point


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "customer_name", "customer_type", "contact_name", "email", "credit_limit", "payment_terms", "customer_since")
    list_filter = ("customer_type", "payment_terms")
    search_fields = ("customer_name", "contact_name", "email")
    ordering = ("customer_id",)
    inlines = [AddressInline]              # a customer's addresses, on the customer's page


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("address_id", "customer", "street", "city", "state", "zip", "is_current")
    list_filter = ("is_current", "state")
    search_fields = ("street", "city", "customer__customer_name")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "first_name", "last_name", "role")
    list_filter = ("role",)


# ---------------------------------------------------------------- transaction data

class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    fields = ("line_no", "product", "grind", "qty", "unit_price")


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "order_date", "customer", "status", "taken_by")
    list_filter = ("status", "order_date", "taken_by")
    search_fields = ("order_no", "customer__customer_name")
    date_hierarchy = "order_date"
    ordering = ("-order_date", "-order_no")
    inlines = [OrderLineInline]            # the order's lines, on the order's page — the paper order form, as a screen
    list_select_related = ("customer", "taken_by")
    autocomplete_fields = ("customer", "ship_to_address")


@admin.register(OrderLine)
class OrderLineAdmin(admin.ModelAdmin):
    list_display = ("order", "line_no", "product", "grind", "qty", "unit_price", "line_total")
    search_fields = ("order__order_no", "product__sku")
    list_select_related = ("order", "product")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("shipment_id", "order", "ship_date", "carrier", "tracking")
    list_filter = ("carrier", "ship_date")
    search_fields = ("order__order_no", "tracking")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_no", "order", "invoice_date")
    search_fields = ("invoice_no", "order__order_no")
    date_hierarchy = "invoice_date"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "order", "paid_date")
    search_fields = ("order__order_no",)
    date_hierarchy = "paid_date"
