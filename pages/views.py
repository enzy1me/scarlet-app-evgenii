"""
Views: one Python function per page.

A view takes the request and returns a response. render() fills a template with a
context dictionary and wraps the result in an HttpResponse.

WEEK 6: the catalog no longer comes from a Python list. The view asks the database through
the Product model — Product.objects.filter(active=True) — and Django writes the SQL:
    SELECT ... FROM products LEFT OUTER JOIN coffees ON ... WHERE products.active ORDER BY sku
The templates did not change their structure; the view changed where the data comes from.
"""

from django.shortcuts import render

from operations.models import Product


def home(request):
    featured = (
        Product.objects.filter(active=True, size="12 oz bag")
        .select_related("coffee")        # one query, with the JOIN, instead of one query per card
        .order_by("sku")[:4]
    )
    return render(request, "pages/home.html", {"featured": featured})


def catalog(request):
    products = (
        Product.objects.filter(active=True)   # WEEK 6 — was: [p for p in PRODUCTS if p["active"]]
        .select_related("coffee")
        .order_by("sku")
    )
    return render(
        request,
        "pages/catalog.html",
        {"products": products, "count": products.count()},
    )


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")
