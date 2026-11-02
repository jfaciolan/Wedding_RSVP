import datetime as dt

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.rsvp.models import Invitation, Rsvp
from apps.rsvp.selectors import days_remaining, possible_duplicates, rsvp_is_open

pytestmark = pytest.mark.django_db
SUBMIT = "/rsvp/"


def open_link(client, invitation):
    return client.get(reverse("rsvp:invite", args=[invitation.code]))


# ----- Invite links -----


def test_invite_codes_are_long_and_random(db):
    codes = {Invitation.objects.create(label=f"L{i}").code for i in range(20)}
    assert len(codes) == 20
    assert all(len(code) >= 20 for code in codes)


def test_opening_link_marks_opened_and_redirects(client, wedding, invitation_a):
    response = open_link(client, invitation_a)
    assert response.status_code == 302 and response.url == "/"
    invitation_a.refresh_from_db()
    first = invitation_a.first_opened_at
    assert first is not None
    open_link(client, invitation_a)
    invitation_a.refresh_from_db()
    assert invitation_a.first_opened_at == first  # first open is kept
    assert client.session["invitation_code"] == invitation_a.code


def test_invalid_and_revoked_links(client, wedding, invitation_a):
    response = client.get("/i/not-a-real-code/")
    assert response.status_code == 404
    assert b"find that invitation" in response.content
    invitation_a.is_revoked = True
    invitation_a.save()
    assert open_link(client, invitation_a).status_code == 404


def test_invitation_link_sets_max_guests(client, wedding, rsvp_settings, invitation_a):
    open_link(client, invitation_a)
    html = client.get("/").content.decode()
    assert 'max="3"' in html and "Test A" in html


def test_no_link_uses_default_max(client, wedding, rsvp_settings):
    html = client.get("/").content.decode()
    assert 'max="2"' in html
    assert "Privacy test line." in html


# ----- Form rules -----


def test_full_name_required(client, wedding, rsvp_settings, rsvp_post):
    response = client.post(SUBMIT, rsvp_post(full_name=""))
    assert response.status_code == 400
    assert b"Please enter your full name." in response.content
    assert Rsvp.objects.count() == 0


def test_mobile_or_messenger_required(client, wedding, rsvp_settings, rsvp_post):
    response = client.post(SUBMIT, rsvp_post(mobile="", messenger=""))
    assert response.status_code == 400
    assert b"mobile number or a Messenger" in response.content


@pytest.mark.parametrize(
    "contact", [{"mobile": "09171234567"}, {"mobile": "", "messenger": "m.me/juan"}]
)
def test_either_contact_is_enough(client, wedding, rsvp_settings, rsvp_post, contact):
    response = client.post(SUBMIT, rsvp_post(**contact))
    assert response.status_code == 302 and response.url == "/rsvp/thanks/"
    assert Rsvp.objects.count() == 1


def test_email_optional_but_validated(client, wedding, rsvp_settings, rsvp_post):
    assert client.post(SUBMIT, rsvp_post(email="not-an-email")).status_code == 400
    assert client.post(SUBMIT, rsvp_post(email="")).status_code == 302


def test_attending_required(client, wedding, rsvp_settings, rsvp_post):
    response = client.post(SUBMIT, rsvp_post(attending=""))
    assert response.status_code == 400
    assert b"Please let us know if you can attend." in response.content


def test_errors_keep_entered_values(client, wedding, rsvp_settings, rsvp_post):
    response = client.post(SUBMIT, rsvp_post(mobile="", messenger="", note="Keep me"))
    assert b"Juan Dela Cruz" in response.content and b"Keep me" in response.content


def test_guest_count_limited_by_invitation(client, wedding, rsvp_settings, invitation_a, rsvp_post):
    open_link(client, invitation_a)
    assert client.post(SUBMIT, rsvp_post(guests="4")).status_code == 400  # tampered
    assert client.post(SUBMIT, rsvp_post(guests="0")).status_code == 400
    assert client.post(SUBMIT, rsvp_post(guests="3")).status_code == 302
    assert Rsvp.objects.get().guests == 3


def test_single_guest_invitation(client, wedding, rsvp_settings, invitation_b, rsvp_post):
    open_link(client, invitation_b)
    assert 'max="1"' in client.get("/").content.decode()
    assert client.post(SUBMIT, rsvp_post(guests="2")).status_code == 400


def test_default_max_without_link(client, wedding, rsvp_settings, rsvp_post):
    assert client.post(SUBMIT, rsvp_post(guests="3")).status_code == 400
    assert client.post(SUBMIT, rsvp_post(guests="2")).status_code == 302


def test_declining_saves_zero_guests(client, wedding, rsvp_settings, rsvp_post):
    client.post(SUBMIT, rsvp_post(attending="no", guests="99"))
    rsvp = Rsvp.objects.get()
    assert rsvp.attending is False and rsvp.guests == 0


def test_honeypot_blocks(client, wedding, rsvp_settings, rsvp_post):
    response = client.post(SUBMIT, rsvp_post(website="http://spam"))
    assert response.status_code == 400
    assert Rsvp.objects.count() == 0


@override_settings(RSVP_RATE_LIMIT=3)
def test_rate_limited(client, wedding, rsvp_settings, rsvp_post):
    for _ in range(3):
        assert client.post(SUBMIT, rsvp_post()).status_code == 302
    assert client.post(SUBMIT, rsvp_post()).status_code == 429


def test_csrf_enforced(wedding, rsvp_settings, rsvp_post):
    from django.test import Client

    strict = Client(enforce_csrf_checks=True)
    assert strict.post(SUBMIT, rsvp_post()).status_code == 403


def test_confirmation_page_summarises(client, wedding, rsvp_settings, rsvp_post):
    response = client.post(SUBMIT, rsvp_post(guests="2", dietary="No nuts"), follow=True)
    html = response.content.decode()
    assert "Thank you, Juan Dela Cruz" in html
    assert "Joyfully accepts" in html and "No nuts" in html


def test_thanks_without_rsvp_redirects(client, wedding):
    assert client.get("/rsvp/thanks/").status_code == 302


# ----- Updating answers -----


def test_invite_link_updates_existing_rsvp(client, wedding, rsvp_settings, invitation_a, rsvp_post):
    open_link(client, invitation_a)
    client.post(SUBMIT, rsvp_post(guests="2"))
    client.post(SUBMIT, rsvp_post(attending="no"))
    rsvp = Rsvp.objects.get()
    assert rsvp.invitation == invitation_a and rsvp.attending is False and rsvp.guests == 0
    # The form is pre-filled for the returning guest.
    assert "Juan Dela Cruz" in client.get("/").content.decode()


def test_no_link_same_name_and_contact_updates(client, wedding, rsvp_settings, rsvp_post):
    client.post(SUBMIT, rsvp_post(mobile="0917 123 4567"))
    client.post(
        SUBMIT, rsvp_post(full_name="juan  dela cruz", mobile="+63 917 123 4567", attending="no")
    )
    rsvp = Rsvp.objects.get()
    assert rsvp.attending is False and rsvp.invitation is None


def test_no_link_messenger_match_updates(client, wedding, rsvp_settings, rsvp_post):
    client.post(SUBMIT, rsvp_post(mobile="", messenger="juan.dc"))
    client.post(SUBMIT, rsvp_post(mobile="", messenger="https://m.me/juan.dc"))
    assert Rsvp.objects.count() == 1


def test_same_name_different_contact_creates_and_flags(client, wedding, rsvp_settings, rsvp_post):
    client.post(SUBMIT, rsvp_post(mobile="09170000001"))
    client.post(SUBMIT, rsvp_post(mobile="09170000002"))
    assert Rsvp.objects.count() == 2
    flagged = possible_duplicates()
    assert len(flagged) == 2 and all("name" in reasons for reasons in flagged.values())


def test_no_link_rsvp_is_not_tied_to_invitation(client, wedding, rsvp_settings, rsvp_post):
    client.post(SUBMIT, rsvp_post())
    assert Rsvp.objects.get().has_invite_link is False


# ----- Deadline and closing -----


def test_kindly_reply_by_shows_deadline(client, wedding, rsvp_settings):
    rsvp_settings.deadline = dt.datetime(2030, 12, 1, 15, 59, tzinfo=dt.UTC)  # 11:59 PM Manila
    rsvp_settings.save()
    html = client.get("/").content.decode()
    assert "Kindly reply by December 1, 2030" in html
    assert "11:59 PM" in html


def test_past_deadline_closes_form(client, wedding, rsvp_settings, rsvp_post):
    rsvp_settings.deadline = timezone.now() - dt.timedelta(minutes=1)
    rsvp_settings.save()
    html = client.get("/").content.decode()
    assert "RSVPs are now closed" in html and "Send my reply" not in html
    response = client.post(SUBMIT, rsvp_post())
    assert response.status_code == 403
    assert Rsvp.objects.count() == 0


def test_toggle_off_closes_before_deadline(client, wedding, rsvp_settings, rsvp_post):
    rsvp_settings.is_open = False
    rsvp_settings.save()
    assert "RSVPs are now closed" in client.get("/").content.decode()
    assert client.post(SUBMIT, rsvp_post()).status_code == 403


def test_deadline_cutoff_uses_manila_time(rsvp_settings):
    # Deadline 2030-12-01 23:59 Manila == 15:59 UTC.
    rsvp_settings.deadline = dt.datetime(2030, 12, 1, 15, 59, tzinfo=dt.UTC)
    before = dt.datetime(2030, 12, 1, 15, 58, tzinfo=dt.UTC)
    after = dt.datetime(2030, 12, 1, 16, 0, tzinfo=dt.UTC)  # Dec 2, 00:00 Manila
    assert rsvp_is_open(rsvp_settings, now=before)
    assert not rsvp_is_open(rsvp_settings, now=after)


def test_days_remaining():
    now = timezone.now()
    assert days_remaining(now + dt.timedelta(days=10), now=now) == 10
    assert days_remaining(now + dt.timedelta(days=9, hours=1), now=now) == 10
    assert days_remaining(now - dt.timedelta(days=1), now=now) == 0
    assert days_remaining(None) is None
