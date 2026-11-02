import datetime as dt

import pytest
from django.utils import timezone

from apps.wedding.models import Attire, AttireSwatch, Event, Faq, ScheduleItem, Venue, WeddingDetail
from apps.wedding.selectors import swatch_columns

pytestmark = pytest.mark.django_db


def test_coming_soon_until_names_and_date(client):
    response = client.get("/")
    assert b"Coming soon" in response.content
    detail = WeddingDetail.load()
    detail.groom_short_name, detail.bride_short_name = "A", "B"
    detail.save()
    assert b"Coming soon" in client.get("/").content


def test_hero_shows_entered_details(client, wedding, ceremony):
    wedding.families_line = "Together with their families"
    wedding.invitation_line = "invite you to celebrate"
    wedding.footer_message = "Footer message test"
    wedding.save()
    html = client.get("/").content.decode()
    assert "Groomtest" in html and "Bridetest" in html
    assert "Groomtest A. Lastname &amp; Bridetest B. Lastname" in html
    assert "Together with their families" in html
    assert "Test Chapel" in html
    assert "Footer message test" in html
    assert 'name="robots" content="noindex' in html
    assert 'property="og:title"' in html


def test_wedding_time_shown_in_manila(client, wedding):
    # 06:00 UTC is 2:00 PM in Asia/Manila (UTC+8).
    wedding.wedding_datetime = dt.datetime(2027, 1, 5, 6, 0, tzinfo=dt.UTC)
    wedding.save()
    html = client.get("/").content.decode()
    assert "Tuesday, January 5, 2027 · 2:00 PM" in html


def test_empty_sections_and_nav_links_hidden(client, wedding):
    html = client.get("/").content.decode()
    for anchor in ('href="#the-day"', 'href="#attire"', 'href="#venue"', 'href="#faq"'):
        assert anchor not in html
    assert 'id="rsvp"' in html  # RSVP always present


def test_sections_appear_with_content(client, wedding, ceremony):
    ScheduleItem.objects.create(title="Guests arrive", time=dt.time(13, 30))
    venue = Venue.load()
    venue.name, venue.map_url = "Test Venue", "https://maps.example/x"
    venue.save()
    attire = Attire.load()
    attire.heading = "Attire heading"
    attire.save()
    AttireSwatch.objects.create(name="Lavender", hex="#cbb8dc")
    Faq.objects.create(question="Visible?", answer="Yes")
    Faq.objects.create(question="Secret?", answer="No", is_published=False)
    html = client.get("/").content.decode()
    for anchor in ('href="#the-day"', 'href="#attire"', 'href="#venue"', 'href="#faq"'):
        assert anchor in html
    assert "Guests arrive" in html and "1:30 PM" in html
    assert 'target="_blank"' in html and "https://maps.example/x" in html
    assert 'fill="#CBB8DC"' in html
    assert "Visible?" in html and "Secret?" not in html


def test_deleting_all_faqs_hides_section(client, wedding):
    faq = Faq.objects.create(question="Q?", answer="A")
    assert 'href="#faq"' in client.get("/").content.decode()
    faq.delete()
    assert 'href="#faq"' not in client.get("/").content.decode()


def test_timeline_follows_admin_order(client, wedding):
    first = ScheduleItem.objects.create(title="First item")
    ScheduleItem.objects.create(title="Second item")
    first.position = 99
    first.save()
    html = client.get("/").content.decode()
    assert html.index("Second item") < html.index("First item")


def test_reception_card_hidden_without_content(client, wedding, ceremony):
    html = client.get("/").content.decode()
    assert 'id="event-ceremony"' in html
    assert 'id="event-reception"' not in html
    reception = Event.load(Event.Kind.RECEPTION)
    reception.venue_name = "Hall"
    reception.save()
    assert 'id="event-reception"' in client.get("/").content.decode()


@pytest.mark.parametrize("count, columns", [(6, 6), (7, 5), (12, 6), (13, 5), (5, 6), (1, 6)])
def test_swatch_columns_never_leave_one_alone(count, columns):
    assert swatch_columns(count) == columns
    if count > columns:
        assert count % columns != 1


def test_no_hardcoded_content_in_templates():
    # Checklist C13: the couple's real details must not appear in code or templates.
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    banned = ["John Rey", "Marian", "Faciolan", "De La Torre", "Sagay", "Open Door", "2027"]
    for folder in ("templates", "apps", "static/js", "static/css", "config"):
        for path in (root / folder).rglob("*"):
            if path.suffix not in {".html", ".py", ".js", ".css"} or "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for word in banned:
                assert word not in text, f"{word!r} hardcoded in {path}"


def test_wedding_date_in_future_fixture(wedding):
    assert wedding.wedding_datetime > timezone.now()
