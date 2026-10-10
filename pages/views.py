"""
Views: one Python function per page.

A view takes the request and returns a response. render() fills a template with a
context dictionary and wraps the result in an HttpResponse.

This week the catalog comes from a Python list (pages/catalog.py). In Week 6 the same
view will read from the database — and the template will not change.
"""

from django.shortcuts import render

from .catalog import COFFEES, PRODUCTS


def home(request):
    featured = [p for p in PRODUCTS if p["size"] == "12 oz bag" and p["active"]]
    return render(request, "pages/home.html", {"featured": featured[:4]})


def catalog(request):
    active = [p for p in PRODUCTS if p["active"]]
    return render(
        request,
        "pages/catalog.html",
        {"products": active, "coffees": COFFEES, "count": len(active)},
    )


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")
