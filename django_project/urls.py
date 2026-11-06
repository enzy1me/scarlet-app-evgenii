"""
Project URLs. Every request starts here: Django reads urlpatterns from the top and takes the
first line that matches the address.

  /admin/      → Django's admin (Week 6)
  /accounts/   → log in and log out (Week 9)
  /customers/, /orders/
               → the back office (Week 9) — operations/urls.py
  /            → the public pages and /status/ — pages/urls.py
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # WEEK 9 (1) — Django's own log-in and log-out pages: /accounts/login/ and /accounts/logout/.
    #   Nobody writes these views: Django has them built in. We only give the log-in page its look,
    #   templates/registration/login.html. A back-office view sends a visitor who is not logged in here.
    path("accounts/", include("django.contrib.auth.urls")),
    # WEEK 9 (2) — the back office: for any other address, Django also looks in operations/urls.py,
    #   which lists /customers/… and /orders/… (eight addresses). The same include as pages.urls below.
    path("", include("operations.urls")),
    path("", include("pages.urls")),
]
