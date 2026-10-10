# Scarlet Roasters — case-company app (33:136:440, Week 5 starter)

A Django 5.2 project with the company's four public pages — home, catalog, about, contact —
laid out with Bootstrap and ready to deploy on Vercel. This is the starting point of your
individual project; Parts 2 and 3 build on it.

## Run it on your laptop (5 minutes)

```bash
python -m venv .venv
# macOS / Linux:            source .venv/bin/activate
# Windows (PowerShell):     .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py runserver
```

Open http://127.0.0.1:8000/ — then /catalog/, /about/, /contact/.
(The "unapplied migrations" warning is fine this week: nothing here touches the database yet.)

## What is where

| Path | What it is | Chapter |
|---|---|---|
| `manage.py` | Django's command-line tool. Vercel finds the project by this file. | DfB 2 |
| `django_project/settings.py` | Configuration. The three Week-5 edits are marked `# WEEK 5`. | DfB 2 |
| `django_project/urls.py` | Project URLs: `/admin/`, and everything else → `pages.urls`. | DfB 2 |
| `pages/urls.py` | The four page URLs, each with a name. | DfB 3 |
| `pages/views.py` | One function per page: `home`, `catalog`, `about`, `contact`. | DfB 3 |
| `pages/catalog.py` | The catalog as a Python list — a stand-in for the database until Week 6. | — |
| `templates/base.html` | The layout every page extends: navbar, footer, Bootstrap. | DfB 4, 11 |
| `templates/pages/*.html` | The four pages. Each one fills `{% block content %}`. | DfB 4 |
| `static/css/scarlet.css` | Our stylesheet. `{% static %}` finds it; Vercel serves it from a CDN. | DfB 4 |
| `requirements.txt` | `Django==5.2.17`. Vercel installs from this file. | DfB 1 |
| `.python-version` | `3.12` — the Python Vercel uses. | — |
| `.gitignore` | Keeps `.venv/`, `db.sqlite3`, `.env*` and `staticfiles/` out of Git. | — |

## Put it on GitHub, then on Vercel (15 minutes)

1. **GitHub.** In VS Code: Source Control → *Publish to GitHub* → **private** repository named
   `scarlet-app-<netid>`. Then on github.com: Settings → Collaborators → add your instructor.
2. **Vercel.** Sign in at vercel.com **with GitHub** (Hobby plan, free). *Add New → Project* →
   import `scarlet-app-<netid>` → leave every setting as it is → **Deploy**. About a minute later
   you have `https://scarlet-app-<something>.vercel.app`.
3. **Prove push-to-deploy.** Change one line (your name on the About page), commit, push.
   Watch Vercel rebuild. Reload the public URL.

Vercel needs no configuration file for this project: it detects `manage.py`, reads
`WSGI_APPLICATION` from settings, installs `requirements.txt`, runs `collectstatic` because
`STATIC_ROOT` is set, and sets the `VERCEL` environment variable — which is what turns `DEBUG` off.

Two rules of the free plan that shape how we work: the repository must be under **your own**
GitHub account (Hobby cannot deploy private repositories owned by an organization), and Vercel
deploys only commits **you** authored — so `git config user.email` must be an email on your
GitHub account.

## Week 6 preview

`pages/catalog.py` disappears. The catalog view reads `products` from PostgreSQL instead, and
the template does not change — that is the point of separating views from templates.
