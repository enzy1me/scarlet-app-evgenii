"""
Django settings for the Scarlet Roasters case-company app — 33:136:440.

Week 5 starter. Three things here are different from what `startproject` gives you,
and each one is marked with  # WEEK 5  so you can find it:

  1. SECRET_KEY and DEBUG come from the environment, not from this file.
  2. ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS include *.vercel.app.
  3. STATIC_ROOT is set, so Vercel runs collectstatic for you.

Everything else is Django's default. Read it once; you will edit it in Week 6.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# WEEK 5 — secrets stay out of the repository.
# Locally the fallback is used. On Vercel, set SECRET_KEY in Project → Settings → Environment Variables.
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-only-not-secret-change-me-in-production-8f2k1",
)

# WEEK 5 — DEBUG is on on your laptop and off on Vercel (Vercel sets the VERCEL variable).
DEBUG = "VERCEL" not in os.environ

# WEEK 5 — who may serve this site.
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".vercel.app"]
CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pages",  # WEEK 5 — our app
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "django_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # WEEK 5 — project-level templates (base.html lives here)
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "django_project.wsgi.application"  # Vercel reads this line to find the app

# Database — untouched this week. Week 6 replaces this block with PostgreSQL (local + Neon).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

# WEEK 5 — static files. STATIC_ROOT is what makes Vercel run collectstatic and serve /static/ from its CDN.
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
