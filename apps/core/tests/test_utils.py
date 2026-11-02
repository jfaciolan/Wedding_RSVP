import pytest

from apps.core.services import move
from apps.core.utils import (
    client_ip,
    is_rate_limited,
    normalize_messenger,
    normalize_mobile,
    normalize_name,
)
from apps.wedding.models import Faq


@pytest.mark.parametrize(
    "raw, expected",
    [("0917 123 4567", "09171234567"), ("+63 917-123-4567", "09171234567"), ("", "")],
)
def test_normalize_mobile(raw, expected):
    assert normalize_mobile(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "juan.dc",
        "https://m.me/juan.dc",
        "m.me/Juan.DC/",
        "https://www.facebook.com/juan.dc?x=1",
        "@juan.dc",
    ],
)
def test_normalize_messenger(raw):
    assert normalize_messenger(raw) == "juan.dc"


def test_normalize_name():
    assert normalize_name("  Juan   Dela Cruz ") == normalize_name("juan dela cruz")
    assert normalize_name("Peña") == "peña"


def test_rate_limit_counts_hits():
    assert not any(is_rate_limited("k", 3, 60) for _ in range(3))
    assert is_rate_limited("k", 3, 60)


def test_client_ip_prefers_forwarded(rf):
    request = rf.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 10.0.0.1", REMOTE_ADDR="10.0.0.2")
    assert client_ip(request) == "1.2.3.4"


@pytest.mark.django_db
def test_ordered_model_appends_and_moves():
    a = Faq.objects.create(question="A", answer="a")
    b = Faq.objects.create(question="B", answer="b")
    c = Faq.objects.create(question="C", answer="c")
    assert [f.question for f in Faq.objects.all()] == ["A", "B", "C"]
    move(c, "up")
    assert [f.question for f in Faq.objects.all()] == ["A", "C", "B"]
    move(Faq.objects.get(pk=a.pk), "up")  # already first: no change
    move(Faq.objects.get(pk=a.pk), "down")
    assert [f.question for f in Faq.objects.all()] == ["C", "A", "B"]
    assert b.pk


@pytest.mark.django_db
def test_noindex_header(client):
    assert client.get("/").headers["X-Robots-Tag"] == "noindex, nofollow"


@pytest.mark.django_db
def test_custom_404(client):
    response = client.get("/no-such-page/")
    assert response.status_code == 404
    assert b"This page wandered off" in response.content
