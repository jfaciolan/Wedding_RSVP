import json
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command

from apps.wedding.models import AttireSwatch, Event, Faq, ScheduleItem, WeddingDetail

pytestmark = pytest.mark.django_db
DEFAULTS = json.loads(
    (settings.BASE_DIR / "assets" / "design_defaults.json").read_text(encoding="utf-8")
)


def load(*args):
    call_command("load_design_defaults", *args, stdout=StringIO())


def test_defaults_fill_an_empty_site(client):
    assert b"Coming soon" in client.get("/").content
    load()
    html = client.get("/").content.decode()
    assert "Coming soon" not in html
    assert DEFAULTS["wedding"]["groom_short_name"] in html
    assert DEFAULTS["attire"]["heading"].replace("&", "&amp;") in html
    assert 'id="event-ceremony"' in html
    assert 'id="event-reception"' not in html  # time and venue are placeholders
    assert 'href="#faq"' not in html  # FAQs wait for answers
    assert list(AttireSwatch.objects.values_list("hex", flat=True)) == [
        s["hex"] for s in DEFAULTS["swatches"]
    ]
    assert [i.title for i in ScheduleItem.objects.all()] == [
        s["title"] for s in DEFAULTS["schedule"]
    ]
    assert Faq.objects.filter(is_published=False).count() == len(DEFAULTS["faqs"])
    assert Event.load(Event.Kind.RECEPTION).date is not None


def test_running_twice_adds_no_duplicates():
    load()
    load()
    assert ScheduleItem.objects.count() == len(DEFAULTS["schedule"])
    assert AttireSwatch.objects.count() == len(DEFAULTS["swatches"])
    assert Faq.objects.count() == len(DEFAULTS["faqs"])


def test_existing_values_are_kept_unless_forced():
    load()
    detail = WeddingDetail.load()
    detail.footer_message = "Edited by the couple"
    detail.save()
    ScheduleItem.objects.first().delete()
    load()
    assert WeddingDetail.load().footer_message == "Edited by the couple"
    assert ScheduleItem.objects.count() == len(DEFAULTS["schedule"]) - 1
    load("--force")
    assert WeddingDetail.load().footer_message == DEFAULTS["wedding"]["footer_message"]
    assert ScheduleItem.objects.count() == len(DEFAULTS["schedule"])


def test_missing_file_is_an_error(tmp_path):
    with pytest.raises(CommandError):
        load("--file", str(tmp_path / "missing.json"))
