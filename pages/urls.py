"""
The pages app's URLs. Four public pages — the company's front door — and the status page (Week 7).

Each line: a URL pattern → a view function → a name we can use in templates ({% url 'catalog' %}).
"""

from django.urls import path

from . import status, views

urlpatterns = [
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("status/", status.status, name="status"),      # Week 7: the status page
]
