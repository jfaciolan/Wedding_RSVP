# Wedding RSVP

A mobile-first wedding invitation and RSVP site built with Django 5.2 LTS. Guests open a
personal invite link (or the main address), read the details and RSVP. The couple enters
**all** content and manages invitations and RSVPs in the Site Admin at `/site-admin/`.

Specs: `docs/specs.md` · Design tokens: `docs/design_tokens.md` · Design:
`assets/Web Page.pdf` · Validation: `docs/checklist.md`

## Requirements

- [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 automatically from `.python-version`)

## Set up and run locally

```bash
uv sync                                  # install from uv.lock
cp .env.example .env                     # then edit SECRET_KEY etc. (optional for local)
uv run python manage.py migrate
uv run python manage.py create_site_admin <username>   # staff account for /site-admin/
uv run python manage.py load_design_defaults           # optional: pre-fill content from the design
uv run python manage.py runserver
```

- Public page: http://localhost:8000/ (shows "Coming soon" until the couple's names and the
  wedding date are entered)
- Site Admin: http://localhost:8000/site-admin/
- Django admin (superuser fallback only): http://localhost:8000/admin/ — create a superuser
  with `uv run python manage.py createsuperuser`

`manage.py` uses `config.settings.local` (DEBUG on). Production uses
`config.settings.production` (set `DJANGO_SETTINGS_MODULE`; `wsgi.py` defaults to it).

## Tests and linting

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Production deploy check (needs real values):

```bash
SECRET_KEY=... ALLOWED_HOSTS=example.com DJANGO_SETTINGS_MODULE=config.settings.production \
  uv run python manage.py check --deploy
```

## Environment variables

See `.env.example`. All are read in `config/settings/base.py`.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Required in production. |
| `DEBUG` | `False` in production. |
| `ALLOWED_HOSTS` | Comma-separated host names. |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins, e.g. `https://example.com`. |
| `DATABASE_URL` | Optional. Defaults to SQLite (`db.sqlite3`). Any `dj-database-url` URL works (Postgres, MySQL). |
| `SITE_URL` | Absolute site address used for invite links and Open Graph tags. |
| `RSVP_RATE_LIMIT`, `RSVP_RATE_WINDOW` | RSVP posts allowed per IP per window (default 10 per 600 s). |

## Design defaults

`assets/design_defaults.json` holds the content shown in the design (`assets/Web Page.pdf`):
names, date, ceremony, order of the day, venue, attire with its six colors, and the four FAQ
questions. Load it with:

```bash
uv run python manage.py load_design_defaults            # fills only empty fields
uv run python manage.py load_design_defaults --force    # overwrite, and replace the lists
```

The command never overwrites what you have entered unless you pass `--force`. Lists (order
of the day, attire colors, FAQs) are only added when they are empty. The design's bracketed
placeholders are left blank, so those parts stay hidden until you fill them in the Site Admin:

- reception time and venue
- times for the order of the day items
- the Google Maps link
- FAQ answers (the FAQs are added unpublished; answer them and tick Published)
- the RSVP deadline, default max guests and privacy text

The content is kept in this data file rather than in code or migrations, so a fresh install
still shows "Coming soon" until details are entered or loaded.

## Monogram

The JM monogram source is `assets/our_monogram.png` (white background). The web versions in
`static/img/` (transparent `monogram.png/.webp`, `monogram-sm.png/.webp`, and
`og-image.jpg` for link previews) are generated with:

```bash
uv run python manage.py process_monogram            # optional: --source path/to/file.png
```

Run it again if the source image changes.

## How it works

- **Content:** every public text, date, venue, schedule item, attire color and FAQ comes
  from the Site Admin. Sections with no content are hidden, and so are their nav links.
- **Invite links:** `/i/<code>/` (a 22-character `secrets.token_urlsafe` code) records the
  first time the link is opened, stores the invitation in the session, and redirects to the
  public page. The RSVP is then tied to that invitation and its max guests.
- **RSVPs:**
  - One RSVP per invitation; resubmitting updates it.
  - Guests without a link can RSVP. A repeat submission with the same name plus the same
    mobile or Messenger updates their earlier RSVP; otherwise a new RSVP is created, and any
    name, mobile or Messenger shared with another RSVP is flagged on the dashboard as a
    possible duplicate.
  - The deadline and the open/closed toggle are enforced on the server (Asia/Manila time).
  - Spam protection: a honeypot field, a per-IP rate limit, and CSRF.
- **Dashboard and export:** invitation and response counts, headcount, days until the
  deadline, the list of invitations with no response yet, possible duplicates, and a
  UTF-8 CSV export (with BOM, so names with ñ display correctly in Excel).

## Deployment (Wasmer) — deferred

Phase 0 (the Wasmer persistence check) has **not been run yet**. We agreed to build and
verify locally first.

Notes for when it is picked up:

- Wasmer Edge detects Django projects automatically and can run migrations after a deploy.
- SQLite needs a persistent **volume** declared in `app.yaml`. Wasmer's docs warn that
  volumes are limited to a region and that "databases and other more complex use-cases
  will not work well just yet". Expect to use Wasmer's managed **PostgreSQL/MySQL**
  instead, by setting `DATABASE_URL`. No code changes are needed.
- Static files are served by WhiteNoise. Run `python manage.py collectstatic` as part of
  the build.
- Set `DJANGO_SETTINGS_MODULE=config.settings.production`, plus `SECRET_KEY`,
  `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` and `SITE_URL`.
- Then confirm that data entered in the Site Admin survives a redeploy and a restart
  (checklist A7), and record the result here.
