import datetime as dt

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.rsvp.models import Invitation, RsvpSettings
from apps.wedding.models import Event, WeddingDetail


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def wedding(db):
    """Minimal content so the public page leaves "Coming soon". Test data only."""
    detail = WeddingDetail.load()
    detail.groom_short_name = "Groomtest"
    detail.bride_short_name = "Bridetest"
    detail.groom_full_name = "Groomtest A. Lastname"
    detail.bride_full_name = "Bridetest B. Lastname"
    detail.wedding_datetime = timezone.now() + dt.timedelta(days=90)
    detail.save()
    return detail


@pytest.fixture
def rsvp_settings(db):
    settings_obj = RsvpSettings.load()
    settings_obj.deadline = timezone.now() + dt.timedelta(days=30)
    settings_obj.default_max_guests = 2
    settings_obj.privacy_text = "Privacy test line."
    settings_obj.save()
    return settings_obj


@pytest.fixture
def invitation_a(db):
    return Invitation.objects.create(label="Test A", max_guests=3)


@pytest.fixture
def invitation_b(db):
    return Invitation.objects.create(label="Test B", max_guests=1)


@pytest.fixture
def ceremony(db):
    event = Event.load(Event.Kind.CEREMONY)
    event.time = dt.time(14, 0)
    event.venue_name = "Test Chapel"
    event.address = "Line one\nLine two"
    event.save()
    return event


@pytest.fixture
def staff_client(client, django_user_model):
    user = django_user_model.objects.create_user("staff", password="pw-123456!", is_staff=True)
    client.force_login(user)
    return client


@pytest.fixture
def rsvp_post():
    def make(**overrides):
        data = {
            "full_name": "Juan Dela Cruz",
            "mobile": "0917 123 4567",
            "messenger": "",
            "email": "",
            "attending": "yes",
            "guests": "1",
            "dietary": "",
            "note": "",
            "website": "",
        }
        data.update(overrides)
        return data

    return make
