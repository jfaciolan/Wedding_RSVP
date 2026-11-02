# Wedding RSVP Site — Product Specification (v1)

## 1. Goal
A mobile-first wedding invitation and RSVP website built with Django. It matches the
provided PDF design (Variant B, "Gray and Plum").

- **Guests** have no accounts. They open the site through a personal invite link (or the
  general site address), read the wedding details, and RSVP with their contact details so
  the couple can notify them of any changes.
- **Site Admin** provides **all** wedding details through the Site Admin, generates
  personal invite links, and tracks RSVPs on a dashboard.

No wedding content (names, dates, venues, schedule, attire, FAQs) is hardcoded in
templates, code, or seed data. Everything shown on the public page comes from what the
Site Admin enters.

## 2. Sources
| File | Use |
|---|---|
| `variant_b_design.pdf` | Source of truth for layout, section order, copy style, and components. |
| `design_tokens.md` | Colors, typography, spacing, and component styles to implement. |
| `our_monogram.png` | Logo (JM wreath). Must render without a visible background box. |
| `jm_wedding_brand_guidelines.html` | Background reference only. The PDF wins on any conflict. |

## 3. Tech stack
- Django (current LTS) on Python as supported by Wasmer.
- **uv** for environment and dependencies: `pyproject.toml` and a committed `uv.lock`.
- SQLite by default; a `DATABASE_URL` environment variable allows switching later.
- `TIME_ZONE = "Asia/Manila"`, `USE_TZ = True`.
- WhiteNoise for static files; fonts self-hosted.
- ruff (lint and format), pytest + pytest-django.
- **Hosting: Wasmer.** Phase 0 (before feature work): deploy a minimal Django app and
  confirm SQLite data survives a redeploy and restart. If it does not, switch to an
  external database via `DATABASE_URL`. Record the outcome and deploy steps in the README.

## 4. Architecture and conventions
```
project-root/
├── pyproject.toml / uv.lock / .env.example / README.md
├── manage.py
├── config/
│   ├── settings/ (base.py, local.py, production.py)
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/        # shared base models, mixins, utilities
│   ├── wedding/     # wedding content models + public page
│   ├── rsvp/        # invitations, RSVPs, RSVP form
│   └── siteadmin/   # Site Admin: content forms, invitations, dashboard
├── templates/       # base.html, per-app folders, partials per section
└── static/          # css/tokens.css, css/site.css, js/, fonts/, img/
```
- Settings from environment variables: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`,
  `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, `SITE_URL`.
- PEP 8; singular PascalCase model names; snake_case modules.
- Per app: `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, `services.py`
  (business logic), `selectors.py` (queries), `tests/`.
- Thin class-based views; no business logic in templates.
- All styling through CSS variables from `design_tokens.md`; no inline styles.
- Security: CSRF on all forms, secure cookies and HSTS/SSL redirect in production,
  `python manage.py check --deploy` passes.

## 5. Roles
| Role | Access |
|---|---|
| **Site Admin** | Logs in at `/site-admin/login/`. Manages all wedding details, invite links, RSVPs, and the dashboard. Implemented as Django staff users. |
| **Guest** | No account. Views the public page and submits or updates an RSVP. |

Django's built-in `/admin/` stays available to superusers as a fallback only. Day-to-day
management happens in the Site Admin.

## 6. Site Admin (`/site-admin/`)
A custom, staff-only area styled with the same design tokens. Every page requires login;
non-staff users are redirected to the login page.

| Page | What the admin manages |
|---|---|
| **Dashboard** | RSVP summary (see 6.1). Landing page after login. |
| **Wedding details** | Groom and bride short names and full names, "Together with their families" line, invitation line ("invite you to celebrate their wedding"), wedding date and time, invitation headline and message, footer message. |
| **Ceremony & Reception** | For each: time, date, venue name, address lines. |
| **Order of the day** | Schedule items: time, title, subtitle; add, edit, delete, reorder. |
| **Venue** | Venue name, full address, Google Maps link (used by "View on map"). |
| **Attire** | Heading, tagline, guidance for ladies, guidance for gentlemen, color swatches (name + hex, reorderable). |
| **FAQs** | Question, answer, published toggle; add, edit, delete, reorder. |
| **Invitations** | Create invite links (see 7.1), view status, copy links, revoke. |
| **RSVPs** | Searchable, filterable list of all RSVPs; view and edit one; CSV export. |
| **RSVP settings** | RSVP deadline (date and time), RSVP open/closed toggle, default max guests for guests without an invite link, privacy/consent text. |

### 6.1 Dashboard
- Invitations: total, opened, responded, not yet responded.
- Responses: attending, declined, total headcount (sum of guests attending).
- **RSVPs without an invite link**: count, plus a filter and a "No invite link" badge in
  the RSVP table.
- Possible duplicates (same name, or same mobile or Messenger) flagged for review.
- Days remaining until the RSVP deadline.
- List of invitations not yet responded, with their links for follow-up.
- CSV export of RSVPs including contact details (for sending change notices).

## 7. Invitations and RSVP

### 7.1 Invite links
- The Site Admin creates an invitation with a label (e.g. "Santos family") and a maximum
  number of guests. Several can be added at once on one form.
- Each invitation gets an unguessable code (`secrets.token_urlsafe`) and a link:
  `https://<site>/i/<code>/`. The Invitations page shows the full link with a copy button.
- Status per invitation: not opened / opened (first opened date) / responded (attending or
  declined).
- Opening a valid link stores the invitation in the session and takes the guest to the
  public page. The RSVP form is then tied to that invitation and its max guests.
- An invalid or revoked code shows a friendly page and a link to the public page.

### 7.2 RSVP form (fields as in the PDF, plus contact)
| Field | Rule |
|---|---|
| Full name | Required. |
| Mobile number | Required **unless** Messenger is given. |
| Facebook Messenger (username or m.me / profile link) | Required **unless** mobile is given. |
| Email | Optional; validated if given. |
| Will you be attending? | Required: "Joyfully accepts" / "Regretfully declines". |
| Number of guests (including yourself) | Stepper, 1 to max guests. Hidden and stored as 0 when declining. |
| Dietary needs or allergies | Optional. |
| A note for the couple | Optional. |

- **Max guests** comes from the invitation; without one, from the default in RSVP settings.
- **Guests without an invite link may RSVP.** Their RSVP is saved with no invitation and
  flagged "No invite link" in the Site Admin and dashboard.
- **Updating an answer:** a guest with an invite link updates the invitation's existing
  RSVP (one RSVP per invitation). A guest without a link who submits again with the same
  name and the same mobile or Messenger updates their earlier RSVP; otherwise a new RSVP is
  created and possible duplicates are flagged on the dashboard.
- **Deadline:** the form accepts submissions until the deadline set in RSVP settings
  (Asia/Manila time) and while RSVPs are toggled open. After that, the RSVP section shows a
  gracious "RSVPs are now closed" message.
- Spam protection: honeypot field, rate limit per IP, CSRF.
- After submitting: a confirmation page that thanks the guest and summarizes their answer.
- A short privacy/consent line (text set in RSVP settings) is shown under the form.
- Public pages are `noindex`.

## 8. Public page
A single scrolling page; the sticky nav links to sections by anchor.

**Nav:** logo · The Day · Attire · Venue · FAQ · "Kindly RSVP" button.

| # | Section | Content source |
|---|---|---|
| 1 | Hero | Monogram, families line, couple names, full names, invitation line, date/time, ceremony venue, buttons "Kindly RSVP" and "See the details". |
| 2 | An Invitation | Headline and message. |
| 3 | The Day | Ceremony and Reception cards; "The order of the day" timeline. |
| 4 | Attire + Venue | Attire heading, tagline, guidance, swatches; Venue card with "View on map". |
| 5 | RSVP | "Kindly reply by <deadline>", "Will you join us?", form. |
| 6 | FAQ | Accordion of published FAQs. |
| 7 | Footer | Monogram, names, date, footer message. |

Empty content: any section or card the Site Admin has not filled in is hidden (and its nav
link removed). If the couple's names or the wedding date are not yet set, the public page
shows a simple "Coming soon" page with the monogram.

Also required: RSVP confirmation page, invalid-link page, custom 404 and 500 pages in the
same style.

## 9. Design
Implement the PDF using the values in `design_tokens.md`. Requirements:
- Matches the PDF at mobile (360–430 px) and desktop (≥1120 px) widths.
- WCAG AA contrast, visible focus states, labeled form fields, alt text on the monogram,
  keyboard-operable accordion and stepper, `prefers-reduced-motion` respected.
- Minimal JavaScript: stepper, accordion, attending toggle, copy-link button.

## 10. Deliverables
- Working Django project following the structure above.
- `createsuperuser` instructions plus a command to create a Site Admin (staff) user.
- Automated tests covering models, RSVP rules, invite links, deadline, flags, and access
  control.
- README: uv setup, run locally, run tests, Wasmer deployment, Phase 0 result.
- `checklist.md` (product validation checklist) passing in full.

## 11. Out of scope for v1 (iteration 2)
Parents section; Entourage and Sponsors section; additional guest names; RSVP revision
history; bulk CSV import of invitations; email/SMS/Messenger broadcast; multiple languages.

## 12. Working method
1. Phase 0: Wasmer persistence check.
2. Share the folder structure and model list for approval.
3. Build in order: scaffold → models → Site Admin content pages → public page →
   invitations + RSVP → dashboard → tests → deploy docs.
4. Validate against `checklist.md` before handover.
