import csv
import datetime as dt
import io

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.rsvp.models import Invitation, Rsvp, RsvpSettings
from apps.wedding.models import AttireSwatch, Event, Faq, ScheduleItem, WeddingDetail

pytestmark = pytest.mark.django_db

ADMIN_PAGES = [
    "/site-admin/",
    "/site-admin/wedding/",
    "/site-admin/events/",
    "/site-admin/venue/",
    "/site-admin/attire/",
    "/site-admin/rsvp-settings/",
    "/site-admin/invitations/",
    "/site-admin/rsvps/",
    "/site-admin/rsvps/export.csv",
    "/site-admin/content/schedule/",
    "/site-admin/content/faqs/",
    "/site-admin/content/swatches/add/",
]


# ----- Access control -----


@pytest.mark.parametrize("url", ADMIN_PAGES)
def test_anonymous_redirected_to_login(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith("/site-admin/login/")


@pytest.mark.parametrize("url", ADMIN_PAGES)
def test_non_staff_redirected(client, django_user_model, url):
    user = django_user_model.objects.create_user("guest", password="pw-123456!")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 302 and "/site-admin/login/" in response.url


@pytest.mark.parametrize("url", ADMIN_PAGES)
def test_staff_can_open_every_page(staff_client, url):
    response = staff_client.get(url)
    assert response.status_code == 200
    assert (
        "no-store" in response.headers["Cache-Control"]
        or "no-cache" in response.headers["Cache-Control"]
    )


def test_login_lands_on_dashboard(client, django_user_model):
    django_user_model.objects.create_user("staff", password="pw-123456!", is_staff=True)
    response = client.post("/site-admin/login/", {"username": "staff", "password": "pw-123456!"})
    assert response.status_code == 302 and response.url == reverse("siteadmin:dashboard")


def test_login_rejects_non_staff(client, django_user_model):
    django_user_model.objects.create_user("guest", password="pw-123456!")
    response = client.post("/site-admin/login/", {"username": "guest", "password": "pw-123456!"})
    assert response.status_code == 200
    assert b"does not have Site Admin access" in response.content


def test_logout_ends_session(staff_client):
    response = staff_client.post("/site-admin/logout/")
    assert response.status_code == 302
    assert staff_client.get("/site-admin/").status_code == 302


def test_site_admin_separate_from_django_admin(staff_client):
    # A staff user without model permissions sees no content in /admin/, and the
    # Site Admin uses its own templates.
    assert b"Site Admin" in staff_client.get("/site-admin/").content
    assert staff_client.get("/admin/").status_code == 200


def test_create_site_admin_command(django_user_model):
    call_command("create_site_admin", "planner", password="a-Strong-pass-42")
    user = django_user_model.objects.get(username="planner")
    assert user.is_staff and not user.is_superuser


# ----- Content entry -----


def test_wedding_details_save_and_show(staff_client, client):
    data = {
        "groom_short_name": "G",
        "bride_short_name": "B",
        "groom_full_name": "G Full",
        "bride_full_name": "B Full",
        "families_line": "Families",
        "invitation_line": "invite",
        "wedding_datetime": "2031-02-03T14:00",
        "invitation_headline": "Headline here",
        "invitation_message": "Message here",
        "footer_message": "Footer here",
    }
    assert staff_client.post("/site-admin/wedding/", data).status_code == 302
    detail = WeddingDetail.load()
    assert timezone.localtime(detail.wedding_datetime).hour == 14
    html = client.get("/").content.decode()
    assert "Headline here" in html and "Footer here" in html


def test_wedding_details_required_errors(staff_client):
    response = staff_client.post("/site-admin/wedding/", {})
    assert response.status_code == 200
    assert b"This field is required." in response.content


def test_events_save(staff_client):
    data = {
        "ceremony-time": "14:00",
        "ceremony-date": "2031-02-03",
        "ceremony-venue_name": "Chapel",
        "ceremony-address": "A\nB",
        "ceremony-city": "Town",
        "reception-time": "18:00",
        "reception-date": "",
        "reception-venue_name": "Hall",
        "reception-address": "",
        "reception-city": "",
    }
    assert staff_client.post("/site-admin/events/", data).status_code == 302
    assert Event.load("ceremony").time == dt.time(14, 0)
    assert Event.load("reception").venue_name == "Hall"


def test_ordered_crud_and_reorder(staff_client):
    staff_client.post("/site-admin/content/schedule/add/", {"title": "One", "time": "13:00"})
    staff_client.post("/site-admin/content/schedule/add/", {"title": "Two", "time": ""})
    one, two = ScheduleItem.objects.all()
    staff_client.post(f"/site-admin/content/schedule/{two.pk}/move/up/")
    assert [i.title for i in ScheduleItem.objects.all()] == ["Two", "One"]
    staff_client.post(f"/site-admin/content/schedule/{one.pk}/edit/", {"title": "Uno", "time": ""})
    assert ScheduleItem.objects.get(pk=one.pk).title == "Uno"
    staff_client.post(f"/site-admin/content/schedule/{one.pk}/delete/")
    assert ScheduleItem.objects.count() == 1


def test_swatch_hex_validated(staff_client):
    response = staff_client.post("/site-admin/content/swatches/add/", {"name": "X", "hex": "red"})
    assert response.status_code == 400
    staff_client.post("/site-admin/content/swatches/add/", {"name": "Lilac", "hex": "#b9a2d4"})
    assert AttireSwatch.objects.get().hex == "#B9A2D4"


def test_faq_publish_toggle(staff_client):
    staff_client.post("/site-admin/content/faqs/add/", {"question": "Q", "answer": "A"})
    assert Faq.objects.get().is_published is False  # unchecked box
    staff_client.post(
        f"/site-admin/content/faqs/{Faq.objects.get().pk}/edit/",
        {"question": "Q", "answer": "A", "is_published": "on"},
    )
    assert Faq.objects.get().is_published is True


def test_unknown_ordered_kind_404(staff_client):
    assert staff_client.get("/site-admin/content/nope/").status_code == 404


def test_rsvp_settings_save(staff_client):
    data = {"deadline": "2031-01-01T23:59", "default_max_guests": "4", "privacy_text": "P"}
    staff_client.post("/site-admin/rsvp-settings/", data)
    rsvp_settings = RsvpSettings.load()
    assert rsvp_settings.is_open is False  # unchecked
    assert rsvp_settings.default_max_guests == 4
    assert timezone.localtime(rsvp_settings.deadline).hour == 23


# ----- Invitations -----


def test_create_several_invitations(staff_client):
    data = {
        "form-TOTAL_FORMS": "5",
        "form-INITIAL_FORMS": "0",
        "form-0-label": "Test A",
        "form-0-max_guests": "3",
        "form-1-label": "Test B",
        "form-1-max_guests": "1",
    }
    for i in range(2, 5):
        data[f"form-{i}-label"] = ""
        data[f"form-{i}-max_guests"] = "1"
    response = staff_client.post("/site-admin/invitations/", data)
    assert response.status_code == 302
    assert set(Invitation.objects.values_list("label", flat=True)) == {"Test A", "Test B"}
    html = staff_client.get("/site-admin/invitations/").content.decode()
    code = Invitation.objects.get(label="Test A").code
    assert f"https://wedding.example/i/{code}/" in html
    assert "data-copy" in html


def test_revoke_and_restore(staff_client, invitation_a):
    staff_client.post(f"/site-admin/invitations/{invitation_a.pk}/revoke/")
    invitation_a.refresh_from_db()
    assert invitation_a.is_revoked
    staff_client.post(f"/site-admin/invitations/{invitation_a.pk}/revoke/")
    invitation_a.refresh_from_db()
    assert not invitation_a.is_revoked


# ----- Dashboard -----


def test_dashboard_counts(staff_client, rsvp_settings, invitation_a, invitation_b):
    Invitation.objects.create(label="Unopened")
    invitation_a.first_opened_at = timezone.now()
    invitation_a.save()
    invitation_b.first_opened_at = timezone.now()
    invitation_b.save()
    Rsvp.objects.create(
        invitation=invitation_a, full_name="A", mobile="1", attending=True, guests=2
    )
    Rsvp.objects.create(
        invitation=invitation_b, full_name="B", mobile="2", attending=False, guests=0
    )
    Rsvp.objects.create(full_name="C", messenger="c", attending=True, guests=1)
    context = staff_client.get("/site-admin/").context
    assert context["invitations"] == {"total": 3, "opened": 2, "responded": 2, "not_responded": 1}
    assert context["responses"]["attending"] == 2
    assert context["responses"]["declined"] == 1
    assert context["responses"]["headcount"] == 3
    assert context["responses"]["no_invite_link"] == 1
    assert context["days_remaining"] == 30
    counts = {s["key"]: s["count"] for s in context["invitee_chart"]["slices"]}
    assert counts == {"attending": 2, "declined": 1, "opened": 0, "not_opened": 1}
    assert context["invitee_chart"]["total"] == 4
    assert context["invitee_chart"]["no_link"] == 1


def _dashboard_names(client, query=""):
    return [row["name"] for row in client.get("/site-admin/" + query).context["invitees"]]


def test_dashboard_invitee_filters(staff_client, invitation_a, invitation_b):
    revoked = Invitation.objects.create(label="Gone Family", is_revoked=True)
    unopened = Invitation.objects.create(label="Santos family")
    invitation_b.first_opened_at = timezone.now()
    invitation_b.save()
    Rsvp.objects.create(
        invitation=invitation_a, full_name="Ana Reyes", mobile="0917", attending=True, guests=2
    )
    Rsvp.objects.create(full_name="Ben Cruz", email="ben@example.com", attending=False)

    assert _dashboard_names(staff_client) == ["Ana Reyes", "Ben Cruz", unopened.label, "Test B"]
    assert _dashboard_names(staff_client, "?status=attending") == ["Ana Reyes"]
    assert _dashboard_names(staff_client, "?status=declined") == ["Ben Cruz"]
    assert _dashboard_names(staff_client, "?status=opened") == ["Test B"]
    assert _dashboard_names(staff_client, "?status=not_opened") == ["Santos family"]
    assert _dashboard_names(staff_client, "?status=no_link") == ["Ben Cruz"]
    assert _dashboard_names(staff_client, "?status=revoked") == [revoked.label]
    assert _dashboard_names(staff_client, "?q=santos") == ["Santos family"]
    assert _dashboard_names(staff_client, "?q=test+a") == ["Ana Reyes"]  # invitation label
    assert _dashboard_names(staff_client, "?q=ben@example") == ["Ben Cruz"]
    assert _dashboard_names(staff_client, "?status=bogus") == _dashboard_names(staff_client)
    chart = staff_client.get("/site-admin/").context["invitee_chart"]
    assert chart["total"] == 4  # revoked left out
    html = staff_client.get("/site-admin/").content.decode()
    assert "conic-gradient(" in html and "Invitee status" in html


def test_revoke_then_restore_retabulates(staff_client, invitation_a):
    rsvp = Rsvp.objects.create(
        invitation=invitation_a, full_name="Ana", mobile="1", attending=True, guests=2
    )

    def attending():
        context = staff_client.get("/site-admin/").context
        slices = {s["key"]: s["count"] for s in context["invitee_chart"]["slices"]}
        return slices["attending"], context["responses"]["headcount"]

    assert attending() == (1, 2)
    response = staff_client.post(
        f"/site-admin/invitations/{invitation_a.pk}/revoke/", {"next": "/site-admin/?q=x"}
    )
    assert response.url == "/site-admin/?q=x"
    assert attending() == (0, 0)
    assert Rsvp.objects.filter(pk=rsvp.pk, invitation=invitation_a).exists()
    assert _dashboard_names(staff_client, "?status=revoked") == ["Ana"]
    staff_client.post(f"/site-admin/invitations/{invitation_a.pk}/revoke/")
    assert attending() == (1, 2)


def test_revoke_ignores_offsite_next(staff_client, invitation_a):
    response = staff_client.post(
        f"/site-admin/invitations/{invitation_a.pk}/revoke/", {"next": "https://evil.example/"}
    )
    assert response.url == reverse("siteadmin:invitations")


def test_delete_invitation_keeps_rsvp(staff_client, invitation_a):
    code = invitation_a.code
    rsvp = Rsvp.objects.create(
        invitation=invitation_a, full_name="Ana", mobile="1", attending=True, guests=1
    )
    url = f"/site-admin/invitations/{invitation_a.pk}/delete/"
    page = staff_client.get(url)
    assert page.status_code == 200 and b"cannot be undone" in page.content
    assert b"is kept" in page.content
    response = staff_client.post(url, {"next": "/site-admin/"})
    assert response.status_code == 302 and response.url == "/site-admin/"
    assert not Invitation.objects.filter(pk=invitation_a.pk).exists()
    rsvp.refresh_from_db()
    assert rsvp.invitation is None
    assert _dashboard_names(staff_client, "?status=no_link") == ["Ana"]
    assert staff_client.get(f"/i/{code}/").status_code == 404


def test_delete_invitation_requires_staff(client, django_user_model, invitation_a):
    user = django_user_model.objects.create_user("guest", password="pw-123456!")
    client.force_login(user)
    response = client.post(f"/site-admin/invitations/{invitation_a.pk}/delete/")
    assert response.status_code == 302 and "/site-admin/login/" in response.url
    assert Invitation.objects.filter(pk=invitation_a.pk).exists()


def test_rsvp_search_and_filters(staff_client, invitation_a):
    Rsvp.objects.create(
        invitation=invitation_a, full_name="Ana Reyes", mobile="0917", attending=True, guests=1
    )
    Rsvp.objects.create(
        full_name="Ben Cruz", messenger="bencruz", email="ben@example.com", attending=False
    )

    def names(query):
        return [
            r.full_name for r in staff_client.get("/site-admin/rsvps/" + query).context["rsvps"]
        ]

    assert names("?q=ana") == ["Ana Reyes"]
    assert names("?q=0917") == ["Ana Reyes"]
    assert names("?q=bencruz") == ["Ben Cruz"]
    assert names("?q=ben@example") == ["Ben Cruz"]
    assert names("?status=attending") == ["Ana Reyes"]
    assert names("?status=declined") == ["Ben Cruz"]
    assert names("?status=no_link") == ["Ben Cruz"]
    assert b"No invite link" in staff_client.get("/site-admin/rsvps/").content


def test_rsvp_edit(staff_client):
    rsvp = Rsvp.objects.create(full_name="Old", mobile="1", attending=True, guests=1)
    data = {
        "full_name": "New",
        "mobile": "1",
        "messenger": "",
        "email": "",
        "attending": "no",
        "guests": "3",
        "dietary": "",
        "note": "",
        "invitation": "",
    }
    assert staff_client.post(f"/site-admin/rsvps/{rsvp.pk}/", data).status_code == 302
    rsvp.refresh_from_db()
    assert rsvp.full_name == "New" and rsvp.guests == 0


def test_csv_export(staff_client, invitation_a):
    Rsvp.objects.create(
        invitation=invitation_a,
        full_name="José Peña",
        mobile="0917",
        email="j@example.com",
        attending=True,
        guests=2,
        dietary="Vegan",
        note="Hi",
    )
    Rsvp.objects.create(full_name="Walk In", messenger="walkin", attending=False)
    response = staff_client.get("/site-admin/rsvps/export.csv")
    assert response["Content-Type"].startswith("text/csv")
    body = response.content.decode("utf-8")
    assert body.startswith("﻿")
    rows = list(csv.reader(io.StringIO(body.lstrip("﻿"))))
    assert rows[0][:4] == ["Full name", "Mobile", "Messenger", "Email"]
    jose = next(r for r in rows if r[0] == "José Peña")
    assert jose[4:10] == ["Yes", "2", "Vegan", "Hi", "Test A", "Yes"]
    walk = next(r for r in rows if r[0] == "Walk In")
    assert walk[2] == "walkin" and walk[9] == "No"


def test_edit_invitation_keeps_link(staff_client, invitation_a):
    code = invitation_a.code
    url = f"/site-admin/invitations/{invitation_a.pk}/edit/"
    assert staff_client.get(url).status_code == 200
    response = staff_client.post(
        url + "?next=/site-admin/%23invitees", {"label": "Reyes family", "max_guests": "5"}
    )
    assert response.status_code == 302 and response.url == "/site-admin/#invitees"
    invitation_a.refresh_from_db()
    assert invitation_a.label == "Reyes family"
    assert invitation_a.code == code and invitation_a.max_guests == 5
    assert staff_client.post(url, {"label": "", "max_guests": "5"}).status_code == 200  # required
    invitation_a.refresh_from_db()
    assert invitation_a.label == "Reyes family"


@pytest.mark.parametrize("value", ["0", "21", ""])
def test_edit_invitation_rejects_bad_max(staff_client, invitation_a, value):
    url = f"/site-admin/invitations/{invitation_a.pk}/edit/"
    assert staff_client.post(url, {"label": "Test A", "max_guests": value}).status_code == 200
    invitation_a.refresh_from_db()
    assert invitation_a.max_guests == 3


def test_edit_invitation_warns_when_max_below_rsvp(staff_client, invitation_a):
    Rsvp.objects.create(
        invitation=invitation_a, full_name="Ana", mobile="1", attending=True, guests=3
    )
    url = f"/site-admin/invitations/{invitation_a.pk}/edit/"
    response = staff_client.post(url, {"label": "Test A", "max_guests": "2"}, follow=True)
    invitation_a.refresh_from_db()
    assert invitation_a.max_guests == 2
    assert "already RSVP&#x27;d for 3 guests" in response.content.decode()


def test_edit_invitation_requires_staff(client, invitation_a):
    response = client.post(f"/site-admin/invitations/{invitation_a.pk}/edit/", {"label": "X"})
    assert response.status_code == 302 and "/site-admin/login/" in response.url
    invitation_a.refresh_from_db()
    assert invitation_a.label == "Test A"


def test_dashboard_flags_rsvp_over_lowered_max(staff_client, invitation_a, invitation_b):
    Rsvp.objects.create(
        invitation=invitation_a, full_name="Ana", mobile="1", attending=True, guests=3
    )
    Rsvp.objects.create(
        invitation=invitation_b, full_name="Ben", mobile="2", attending=True, guests=1
    )
    invitation_a.max_guests = 2
    invitation_a.save()
    response = staff_client.get("/site-admin/")
    body = response.content.decode()
    assert response.context["responses"]["headcount"] == 3  # Ana capped at 2 + Ben 1
    assert response.context["responses"]["over_max"] == 1
    assert "Over max" in body
    flagged = staff_client.get("/site-admin/?status=over_max").context["invitees"]
    assert [row["name"] for row in flagged] == ["Ana"]
    assert "Over max" in staff_client.get("/site-admin/invitations/").content.decode()


def test_dashboard_flags_raised_max(staff_client, invitation_a):
    Rsvp.objects.create(
        invitation=invitation_a, full_name="Ana", mobile="1", attending=True, guests=2,
        reply_max_guests=3,
    )
    url = f"/site-admin/invitations/{invitation_a.pk}/edit/"
    saved = staff_client.post(url, {"label": "Test A", "max_guests": "5"}, follow=True)
    assert "can now bring up to 5 guests" in saved.content.decode()
    response = staff_client.get("/site-admin/")
    assert response.context["responses"]["max_raised"] == 1
    assert "Max raised" in response.content.decode()
    flagged = staff_client.get("/site-admin/?status=max_raised").context["invitees"]
    assert [row["name"] for row in flagged] == ["Ana"]
