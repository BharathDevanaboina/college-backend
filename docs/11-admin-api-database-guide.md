# 11. Admin, API and database guide

This is the operational map of the backend: what an administrator can manage,
which API owns each action, and where the data is stored. It complements the
field-by-field [API reference](09-api-reference.md).

## Access and authorization

There are three access levels:

| Caller | Authentication | What it can access |
|---|---|---|
| Public website | No sign-in for read-only content | `GET /api/v1/public/site`, registration choices and exam availability |
| Student | Firebase Phone Auth token + Firebase App Check | Brochure download and exam start after a fresh OTP |
| Administrator | Verified Firebase email/password ID token and an active database allow-list entry | Every `/api/v1/admin/**` endpoint |
| Cloud Scheduler | Google OIDC token from an allowed service account | `/internal/lead-sync/flush` only |

The backend does **not** accept a Firebase API key as authorization. The web
client sends Firebase-issued tokens. `require_admin` verifies the ID token,
checks email verification, then looks up the email in `admin_users`.
`require_app_check` protects the two public submission endpoints.

### Admin accounts

An operator creates an allow-list entry and Firebase account with:

```bash
./scripts/run-cli.sh production create-admin --email person@example.com --name "Person Name"
```

The Firebase account contains the password. The database
only contains the email allow-list, display name, active state and last-login
time. Deactivating an entry blocks backend access immediately, even if the
Firebase user still exists.

## What an admin can do

| Area | Admin operations | API prefix | Database / file location |
|---|---|---|---|
| Account | Check their own access/profile | `/admin/me` | `admin_users` |
| Site settings | Edit phone, WhatsApp, email, address, inquiry-form URL and social links | `/admin/site-settings` | `site_settings` |
| Courses | View and edit the three fixed course records, fee and fee breakup | `/admin/courses` | `courses` |
| Batches | Create, edit and remove course batches | `/admin/batches` | `batches` |
| Brochures | Upload, replace, preview and remove PDFs | `/admin/brochures` | Metadata: `brochures`; file: private Firebase Storage |
| Banners | Upload, reorder, activate, edit or delete website banners | `/admin/banners` | Metadata: `banners`; images/thumbnails: Firebase Storage |
| Announcements | Create, edit, schedule, activate and remove notices | `/admin/announcements` | `announcements` |
| Gallery | Upload, reorder, activate, caption and remove photos | `/admin/gallery` | Metadata: `gallery_images`; images/thumbnails: Firebase Storage |
| Videos | Add, edit, reorder, activate or delete supported YouTube/Instagram links | `/admin/videos` | `videos` |
| Mock exam | Download template, validate, upload and delete one of three question sets | `/admin/exam` | `exam_sets`, `exam_passages`, `exam_questions`, `exam_options` |
| Lead delivery | See queued Google Sheets rows and retry their delivery | `/admin/lead-sync` | `pending_sheet_rows` while waiting; final lead data goes to Google Sheets |

All admin routes require the same Firebase/MFA/allow-list check. There is no
role hierarchy in this version: every active administrator has the same access.

## API inventory

All paths below are relative to `/api/v1`. Request and response fields are in
the [API reference](09-api-reference.md); FastAPI also publishes `/docs` and
`/openapi.json` outside production.

### Public and student APIs

| Method | Path | Purpose | Required protection |
|---|---|---|---|
| `GET` | `/public/site` | One homepage payload: settings, courses, batches, media, announcements and exam availability | None |
| `GET` | `/registration/options` | Qualification, year and state dropdown choices | None |
| `POST` | `/brochures/{course_code}/download` | Verify OTP, record a lead and return a brochure PDF | Firebase Phone Auth token in body + App Check |
| `GET` | `/exam/info` | Exam availability, duration and section counts | None |
| `POST` | `/exam/start` | Verify OTP, record a lead and return a shuffled paper and signed attempt token | Firebase Phone Auth token in body + App Check |
| `POST` | `/exam/submit` | Grade answers for a signed attempt token | Signed attempt token |

### Administrator APIs

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/admin/me` | Current admin profile and access check |
| `GET`, `PUT` | `/admin/site-settings` | Read or replace website contact/settings |
| `GET`, `GET /{code}`, `PATCH /{code}` | `/admin/courses` | List, inspect or update fixed courses |
| `GET`, `POST`, `PATCH /{id}`, `DELETE /{id}` | `/admin/batches` | Manage batches |
| `GET`, `PUT /{course_code}`, `GET /{course_code}/file`, `DELETE /{course_code}` | `/admin/brochures` | Manage course PDFs |
| `GET`, `POST`, `PATCH /{id}`, `PUT /{id}/image`, `DELETE /{id}` | `/admin/banners` | Manage banners and their images |
| `GET`, `POST`, `PUT /{id}`, `DELETE /{id}` | `/admin/announcements` | Manage announcements |
| `GET`, `POST`, `PATCH /{id}`, `DELETE /{id}` | `/admin/gallery` | Manage gallery images |
| `GET`, `POST`, `PUT /{id}`, `DELETE /{id}` | `/admin/videos` | Manage video links |
| `GET /sets`, `GET /template`, `POST /sets/validate`, `POST /sets/{slot}`, `DELETE /sets/{slot}` | `/admin/exam` | Manage the three exam-set slots |
| `GET /status`, `POST /flush` | `/admin/lead-sync` | Inspect and retry queued Google Sheets rows |

The scheduler-only route is outside `/api/v1`: `POST /internal/lead-sync/flush`.
It must use an allowed Google OIDC service account; it is not an admin-browser
endpoint.

## Database and service ownership

PostgreSQL is accessed through SQLAlchemy sessions from `app/core/database.py`.
Each request receives one session via `get_db`; successful service methods call
`commit()`, and failed requests are rolled back. Alembic is the source of truth
for schema changes: apply them with `alembic upgrade head`. `db/schema.sql` is
a reviewable generated copy, not the normal migration mechanism.

| Table | Owned by | Contents |
|---|---|---|
| `admin_users` | `admin_auth` | Admin allow-list and last login |
| `site_settings` | `site_settings` | One website-wide settings row |
| `courses` | `courses` | The three course records and fee details |
| `batches` | `batches` | Course schedule entries; references `courses` |
| `brochures` | `brochures` | Private PDF metadata; references `courses` |
| `banners` | `banners` | Banner metadata and optional course relationship |
| `announcements` | `announcements` | Time-bound website notices |
| `gallery_images` | `gallery` | Gallery image metadata |
| `videos` | `videos` | Validated embedded-video metadata |
| `exam_sets` | `exam` | One record per exam slot/upload |
| `exam_passages` | `exam` | Shared reading passages for a set |
| `exam_questions` | `exam` | Questions for a set or passage |
| `exam_options` | `exam` | Options and correct-answer flags |
| `pending_sheet_rows` | `lead_sync` | Temporary retry queue when Google Sheets is unavailable |

### Data that is intentionally not in PostgreSQL

- Firebase passwords, phone OTP codes, MFA secrets and Firebase tokens: Firebase
  Authentication owns them.
- Images and PDFs: Firebase Storage owns the binary files; PostgreSQL stores
  only their paths, URLs and metadata.
- Student leads: Google Sheets is the long-term destination. If a write fails,
  the minimal row waits in `pending_sheet_rows` until Cloud Scheduler retries it.
- Exam attempts and answers: not persisted by design. The signed attempt token
  carries the selected set and time limit; grading happens on submit.

## Local fake mode versus production

Local Docker development uses `AUTH_MODE=fake`, fake tokens and fake Sheets so
developers do not need a Firebase project. `FakeIdentityVerifier` is selected
only when that explicit setting is used. Cloud environments call
`Settings.validate_for_environment()`, which rejects `AUTH_MODE=fake` and
requires Firebase storage/auth configuration. Production and staging therefore
use Firebase verification, not fake accounts.

## Adding or changing data

1. Update the SQLAlchemy model in the owning module.
2. Generate and review an Alembic migration.
3. Update its Pydantic schema, service and API documentation.
4. Add or update an endpoint only behind the appropriate public/admin/internal
   router and dependency.
5. Regenerate `db/schema.sql` for reviewers after the migration is final.
