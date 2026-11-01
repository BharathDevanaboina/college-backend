# College Website Backend

The backend API for the college website, built with **Python 3.12 + FastAPI** and **PostgreSQL**.
It runs on **Google Cloud Run**, stores files in **Cloud Storage for Firebase**, uses
**Firebase Authentication** for the admin login and the students' phone OTP, and writes student
submissions to **Google Sheets**.

The frontend (website and admin portal) is a separate project. It talks to this API.

## What it does

| Area | What the admin can do | What a student sees |
|---|---|---|
| Site settings | Phone, WhatsApp, email, address, Google Form link, social links | Contact details, "Contact management" button |
| Courses & fees | Edit the 3 fixed courses (IBFAP, Advance B.Com, PGDM), fees and yearly breakup | Course details, total fee and yearly breakup |
| Batches | Add/edit/remove batches (start, end, timeline, online/offline) | Upcoming and running batches |
| Brochures | Upload/replace one PDF per course | Fill the form, verify OTP, download the PDF |
| Banners | Image, title, optional brochure button, order, show/hide | Banner slider |
| Announcements | Text, optional link, optional start/end dates | Announcement strip |
| Gallery | Photos with optional caption and order | Photo gallery |
| Videos | YouTube video, YouTube Shorts and Instagram Reel links | Embedded videos |
| Mock exam | Keep 3 question sets (Excel upload, 200 questions each) | Form + OTP, then a shuffled 150-minute exam with score and review |
| Leads | (Read them in Google Sheets) | Every brochure download and exam registration lands in Google Sheets |

The general inquiry form is a Google Form (its link is in Site settings). It is not handled by this backend.

## Quick start (on your computer, about 5 minutes)

You need **Docker Desktop** (or Docker Engine with Compose).

```bash
docker compose up --build
```

Then open <http://localhost:8000/docs>. That is the interactive API page.

Locally everything Google-related is faked:
- Admin token: `Bearer fake-admin:admin@college.com:mfa`.
- Phone OTP token: `fake-phone:+919876543210`.
- Files go to a Docker volume.
- Google Sheets rows go to CSV files.

Give the fake admin access once:

```bash
docker compose exec api python -m app.cli create-admin --email admin@college.com --name "College Admin"
```

Running without Docker, running the tests and more: [docs/02-local-development.md](docs/02-local-development.md).

## Documentation

Read them in this order the first time:

| # | Document | When you need it |
|---|---|---|
| 1 | [Architecture](docs/01-architecture.md) | Understand the modules and how a request flows |
| 2 | [Local development and tests](docs/02-local-development.md) | Run and change the code on your computer |
| 3 | [Configuration](docs/03-configuration.md) | Every setting, and where to change it |
| 4 | [Firebase setup](docs/04-firebase-setup.md) | Admin login, Google Authenticator, phone OTP, App Check, Storage |
| 5 | [Google Sheets setup](docs/05-google-sheets-setup.md) | The spreadsheet that receives student submissions |
| 6 | [Google Cloud setup (one time)](docs/06-google-cloud-setup.md) | Projects, database, secrets, service accounts, scheduler |
| 7 | [Deployment and CI/CD](docs/07-deployment.md) | Deploy to staging and production, roll back |
| 8 | [Operations and maintenance](docs/08-operations.md) | Backups, restores, updates, admin tasks, troubleshooting |
| 9 | [API reference for the frontend](docs/09-api-reference.md) | Every endpoint and the OTP, brochure and exam flows |
| 10 | [Exam question Excel format](docs/10-exam-question-format.md) | Preparing question sets |

## Project layout

```text
app/
  core/                 shared code: config, database, errors, logging, storage, Google Sheets, security
  modules/              one folder per feature (routes, logic, database models)
    admin_auth/  site_settings/  courses/  batches/  brochures/  banners/
    announcements/  gallery/  videos/  registration/  lead_sync/
    brochure_download/  exam/  public_site/
  main.py               builds the FastAPI app from the enabled modules
cli.py                  operator commands (create admin, flush Sheets queue, exam template, ...)
migrations/             Alembic database migrations
db/schema.sql           the full schema as plain SQL (generated from the migrations)
templates/              the Excel template for exam question sets
tests/                  automated tests, one file per module
config/                 staging and production settings for Cloud Run
scripts/                deploy.sh (deploy) and run-cli.sh (run operator commands in the cloud)
.github/workflows/      ci.yml (checks every change) and deploy.yml (deploys)
docs/                   the guides listed above
```

## Everyday commands

| Task | Command |
|---|---|
| Run locally | `docker compose up --build` |
| Run tests | `pytest` |
| Check code style | `ruff check . && ruff format --check .` |
| New database migration | `alembic revision --autogenerate -m "describe change"` |
| Deploy to staging | Push to `main` (automatic), or `./scripts/deploy.sh staging` |
| Deploy to production | GitHub → Actions → Deploy → Run workflow → "production", or `./scripts/deploy.sh production` |
| Add an admin (cloud) | `./scripts/run-cli.sh production create-admin --email someone@college.com` |
