"""Small helpers shared across apps."""

import re

from django.core.cache import cache

_MESSENGER_PREFIX = re.compile(
    r"^(https?://)?(www\.)?(m\.me/|(m\.)?facebook\.com/|messenger\.com/t/|fb\.com/)",
    re.IGNORECASE,
)


def normalize_name(value):
    return " ".join((value or "").split()).casefold()


def normalize_mobile(value):
    """Reduce a phone number to digits; +63 / 63 prefixes become a leading 0."""
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("63") and len(digits) == 12:
        digits = "0" + digits[2:]
    return digits


def normalize_messenger(value):
    """Reduce a Messenger username or m.me / profile link to a comparable handle."""
    value = (value or "").strip()
    value = _MESSENGER_PREFIX.sub("", value)
    value = value.split("?")[0].strip("/@ ")
    return value.casefold()


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def is_rate_limited(key, limit, window):
    """Count one hit for `key`; return True once more than `limit` hits fall in `window`."""
    cache_key = f"ratelimit:{key}"
    cache.add(cache_key, 0, window)
    try:
        count = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, window)
        count = 1
    return count > limit
