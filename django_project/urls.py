"""
Project URLs. Every request starts here.

  /admin/   → Django's admin (Week 6)
  /         → the pages app, which has its own urls.py
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pages.urls")),
]
