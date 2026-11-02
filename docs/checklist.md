# Product Validation Checklist (v1)

Use this to confirm the product works as intended before handover. Each item is a
pass/fail check. Run it on the deployed Wasmer site unless the item says "local".

**Test data:** enter the real wedding details through the Site Admin (section C). Create at
least two invitations: "Test A" (max guests 3) and "Test B" (max guests 1).

_Local validation run on 2026-11-03: items marked [x] were verified locally by the automated
tests and a Playwright walkthrough. Deployed-site checks are still open._

Mark each item: `[x]` pass, `[ ]` not yet, or note a failure inline.

---

## A. Setup and deployment
- [x] A1. `uv sync` installs all dependencies from `uv.lock` on a clean machine (local).
- [x] A2. `uv run python manage.py migrate` runs with no errors (local).
- [x] A3. `uv run pytest` passes with no failures (local).
- [x] A4. `uv run ruff check .` reports no errors (local).
- [x] A5. `python manage.py check --deploy` with production settings reports no warnings.
- [ ] A6. The site is live on Wasmer over HTTPS.
  _Deferred: Wasmer deployment not started (see README)._
- [ ] A7. Data entered in the Site Admin is still there after a redeploy and a restart.
  _Deferred with A6._
- [x] A8. `DEBUG` is off in production; an unknown URL shows the custom 404 page.
- [x] A9. No secrets are committed; `.env.example` lists every required variable.
- [x] A10. README explains setup, running, testing, and Wasmer deployment.

## B. Site Admin access
- [x] B1. `/site-admin/` redirects to the login page when not logged in.
- [x] B2. A staff user can log in and lands on the Dashboard.
- [x] B3. A non-staff user cannot access any `/site-admin/` page.
- [x] B4. Logging out ends the session; pressing Back does not show admin data.
- [x] B5. The Site Admin is a separate area from Django's `/admin/`.

## C. Wedding details entry (all content comes from the Site Admin)
- [x] C1. Before any details are entered, the public page shows the "Coming soon" page.
- [x] C2. Wedding details: names, full names, families line, invitation line, date and
      time, invitation headline and message, and footer message save and appear on the
      public page.
- [x] C3. Ceremony: time, date, venue name, address save and appear in the Ceremony card.
- [x] C4. Reception: time, date, venue name, address save and appear in the Reception card.
- [x] C5. Order of the day: items can be added, edited, deleted, and reordered; the
      public timeline follows the same order.
- [x] C6. Venue: name, address, Google Maps link save; "View on map" opens the link in a
      new tab.
- [x] C7. Attire: heading, tagline, ladies' and gentlemen's guidance save and appear.
- [x] C8. Attire colors: swatches can be added (name + hex), edited, deleted, reordered.
- [x] C9. FAQs: can be added, edited, deleted, reordered; unpublished FAQs do not appear.
- [x] C10. RSVP settings: deadline, open/closed toggle, default max guests, and privacy
      text save and take effect.
- [x] C11. Editing any detail updates the public page immediately, with no code change.
- [x] C12. A section with no content is hidden on the public page, and its nav link is
      removed (test by deleting all FAQs).
- [x] C13. Searching the codebase and templates finds no hardcoded names, dates, venues,
      or addresses.
- [x] C14. Required fields show clear error messages when left blank.

## D. Invitations (personal links)
- [x] D1. The admin can create an invitation with a label and max guests.
- [x] D2. The admin can create several invitations at once on one form.
- [x] D3. Each invitation shows its full link (`/i/<code>/`) and a working copy button.
- [x] D4. Codes are long and random (not sequential or guessable).
- [x] D5. Opening a link marks the invitation "opened" with the date.
- [x] D6. Opening a link takes the guest to the public page with the RSVP tied to that
      invitation.
- [x] D7. After the guest RSVPs, the invitation shows "responded" and the answer.
- [x] D8. A revoked or invalid code shows the friendly invalid-link page.

## E. Public page
- [x] E1. Sticky nav shows the logo, The Day, Attire, Venue, FAQ, and "Kindly RSVP".
- [x] E2. Each nav link scrolls to the correct section.
- [x] E3. Hero shows the monogram, families line, names, full names, invitation line,
      date and time, venue, and both buttons.
- [x] E4. "Kindly RSVP" goes to the RSVP section; "See the details" goes to The Day.
- [x] E5. An Invitation section shows the headline and message.
- [x] E6. The Day shows the Ceremony and Reception cards and the order of the day.
- [x] E7. Attire and Venue appear side by side on desktop and stacked on mobile.
- [x] E8. FAQ items open and close; only one answer's state changes per click.
- [x] E9. Footer shows the monogram, names, date, and footer message.
- [x] E10. Dates and times display in Philippine time (Asia/Manila).
- [x] E11. Pages include a `noindex` tag.

## F. RSVP form
- [x] F1. Fields match the spec: full name, mobile, Messenger, email (optional),
      attending, number of guests, dietary needs, note for the couple.
- [x] F2. Submitting without a full name shows an error.
- [x] F3. Submitting with neither mobile nor Messenger shows an error.
- [x] F4. Submitting with only a mobile number succeeds.
- [x] F5. Submitting with only Messenger succeeds.
- [x] F6. Email can be left blank; an invalid email shows an error.
- [x] F7. Submitting without choosing attending/declining shows an error.
- [x] F8. Via "Test A" link, the stepper goes from 1 to 3 and no further.
- [x] F9. Via "Test B" link, the stepper stays at 1.
- [x] F10. Without a link, the stepper max equals the default max guests in settings.
- [x] F11. Choosing "Regretfully declines" hides the stepper and saves guests as 0.
- [x] F12. A tampered guest count above the max (e.g. edited in the browser) is rejected
      by the server.
- [x] F13. After submitting, the confirmation page thanks the guest and shows their answer.
- [x] F14. Reopening the same invite link and submitting again updates the existing RSVP
      (no second RSVP is created).
- [x] F15. The privacy/consent text from settings appears under the form.
- [x] F16. Filling the hidden honeypot field blocks the submission.
- [x] F17. Many rapid submissions from one IP are rate-limited.
- [x] F18. Error messages appear next to the related field and keep entered values.

## G. RSVP without an invite link
- [x] G1. A visitor without a link can submit an RSVP.
- [x] G2. That RSVP shows a "No invite link" badge in the Site Admin RSVP list.
- [x] G3. The dashboard counts RSVPs without an invite link.
- [x] G4. The RSVP list can be filtered to show only RSVPs without an invite link.
- [x] G5. Submitting again with the same name and same mobile or Messenger updates the
      earlier RSVP.
- [x] G6. Submitting with the same name but different contact creates a new RSVP and the
      dashboard flags it as a possible duplicate.

## H. RSVP deadline and closing
- [x] H1. Before the deadline, the RSVP section shows "Kindly reply by <deadline>" with
      the date from settings.
- [x] H2. After the deadline (test by setting it to a past time), the form is replaced by
      the "RSVPs are now closed" message.
- [x] H3. A direct POST to the RSVP endpoint after the deadline is rejected.
- [x] H4. Turning the RSVP toggle off closes the form even before the deadline.
- [x] H5. The deadline cut-off uses Asia/Manila time.

## I. Dashboard and export
- [x] I1. Invitation counts (total, opened, responded, not yet responded) are correct.
- [x] I2. Attending, declined, and total headcount are correct (headcount = sum of guests
      for attending RSVPs only).
- [x] I3. Days remaining until the deadline is correct.
- [x] I4. The not-yet-responded list shows each invitation with its link.
- [x] I5. The RSVP list can be searched by name, mobile, Messenger, and email.
- [x] I6. The RSVP list can be filtered by attending, declined, and no invite link.
- [x] I7. The admin can open and edit a single RSVP.
- [x] I8. CSV export downloads all RSVPs with name, contact details, attendance, guest
      count, dietary needs, note, invitation label, and "has invite link".
- [ ] I9. The CSV opens correctly in Excel/Google Sheets (names with accents and "ñ"
      display correctly).
  _CSV is UTF-8 with BOM and ñ round-trips in tests; not yet opened in Excel/Sheets._

## J. Design (compare against the PDF)
- [x] J1. Colors, fonts, and spacing follow `design_tokens.md`.
- [x] J2. Desktop (≥1120 px) layout matches the PDF section by section.
- [x] J3. Mobile (360–430 px) shows a clean single-column layout with no horizontal
      scrolling.
- [x] J4. The monogram shows no white or gray box behind it.
- [x] J5. Attire swatches do not leave a single swatch alone on a row on desktop.
- [x] J6. Buttons have hover and focus states as specified.
- [x] J7. Confirmation, invalid-link, 404, and 500 pages use the same style.
- [x] J8. The Site Admin uses the same fonts and colors and is usable on a phone.
- [ ] J9. The page works in current Chrome, Safari (iPhone), and Messenger's in-app
      browser.
  _Checked in desktop Chrome only (headless, 390 px and 1280 px); Safari and Messenger pending._

## K. Accessibility
- [ ] K1. All text meets WCAG AA contrast (check gray text on the gray "The Day" section).
  _Uses the token pairings from design_tokens.md (silver-700 on mist); no automated contrast audit run._
- [x] K2. Every form field has a visible label linked to its input.
- [x] K3. The whole RSVP form can be completed with the keyboard only.
- [x] K4. The stepper and FAQ accordion work with the keyboard and announce their state.
- [x] K5. Focus is clearly visible on every link, button, and field.
- [x] K6. The monogram has alt text; decorative images have empty alt text.
- [x] K7. With reduced motion enabled, there is no smooth scrolling or animation.

## L. Performance and sharing
- [ ] L1. The public page loads in under 3 seconds on a mobile connection.
  _Needs the deployed site._
- [x] L2. Images are compressed; the monogram is served at a sensible size.
- [ ] L3. Sharing the link in Messenger shows a preview with the couple's names and the
      monogram (Open Graph tags).
  _OG tags and og-image.jpg are in place; preview needs a public URL._

## M. End-to-end scenario
- [ ] M1. Admin enters all wedding details, creates invitation "Test A" (max 3), and copies
      its link.
  _M1–M7 steps are covered locally by the automated tests and a Playwright run of the invite → RSVP → dashboard flow; repeat end to end on the deployed site._
- [ ] M2. On a phone, a guest opens the link, reads the page, and accepts for 2 guests with
      a mobile number in under a minute.
- [ ] M3. The dashboard shows "Test A" as responded, attending, headcount +2.
- [ ] M4. The guest reopens the link and changes to "Regretfully declines"; the dashboard
      updates (no duplicate).
- [ ] M5. A visitor without a link RSVPs; the dashboard shows it flagged "No invite link".
- [ ] M6. Admin changes the ceremony time; the public page shows the new time.
- [ ] M7. Admin exports the CSV and finds every guest's contact details for a change notice.
