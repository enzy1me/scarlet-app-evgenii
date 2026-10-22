"""
Django settings for the Scarlet Roasters case-company app — 33:136:440.

Week 5 starter + the Week 6 edits. Everything that differs from what `startproject`
gives you is marked  # WEEK 5  or  # WEEK 6  so you can find it:

  WEEK 5  1. SECRET_KEY and DEBUG come from the environment, not from this file.
          2. ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS include *.vercel.app.
          3. STATIC_ROOT is set, so Vercel runs collectstatic for you.
  WEEK 6  4. The database is PostgreSQL, found through DATABASE_URL in the environment
             (your .env file on the laptop, Vercel's environment variables in production).
          5. The `operations` app: the eleven tables of schema v1.0 as models (managed = False:
             the tables exist already; Django maps them, it does not create them).

Everything else is Django's default.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# WEEK 6 — read .env (git-ignored) into the environment, if it exists. On Vercel there is no
# .env file; the variables are set in Project → Settings → Environment Variables.
load_dotenv(BASE_DIR / ".env")

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
    "pages",  # WEEK 5 — the public pages
    "operations",  # WEEK 6 — the business: schema v1.0 as models
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

# WEEK 6 — the database. One connection string, DATABASE_URL, tells Django where it is:
#   postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require        (your Neon project — the v1.0 database)
# dj_database_url.config() reads it from the environment and turns it into the dictionary
# Django wants. The same code runs on your laptop (.env) and on Vercel (environment variables):
# configuration in the environment, code in the repository, secrets in neither.
# If DATABASE_URL is not set, Django falls back to SQLite so the project still starts —
# but then every table is empty and the catalog page is blank. Set it.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0,            # one connection per request: right for Vercel's serverless functions
    )
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
