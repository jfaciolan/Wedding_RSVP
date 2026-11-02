"""RSVP business logic."""

from django.db import transaction
from django.utils import timezone

from apps.core.utils import normalize_messenger, normalize_mobile, normalize_name

from .models import Invitation, Rsvp

RSVP_FIELDS = [
    "full_name",
    "mobile",
    "messenger",
    "email",
    "attending",
    "guests",
    "dietary",
    "note",
]


def mark_opened(invitation: Invitation):
    if invitation.first_opened_at is None:
        invitation.first_opened_at = timezone.now()
        invitation.save(update_fields=["first_opened_at", "updated_at"])


def find_matching_rsvp(full_name, mobile, messenger):
    """An earlier RSVP without an invite link with the same name and mobile or Messenger."""
    name = normalize_name(full_name)
    mobile = normalize_mobile(mobile)
    messenger = normalize_messenger(messenger)
    for rsvp in Rsvp.objects.filter(invitation__isnull=True).order_by("-updated_at"):
        if normalize_name(rsvp.full_name) != name:
            continue
        if mobile and normalize_mobile(rsvp.mobile) == mobile:
            return rsvp
        if messenger and normalize_messenger(rsvp.messenger) == messenger:
            return rsvp
    return None


@transaction.atomic
def save_rsvp(cleaned_data, invitation=None):
    """Create or update an RSVP. Returns (rsvp, created).

    With an invitation, the invitation's single RSVP is updated. Without one, an earlier
    link-less RSVP with the same name and mobile or Messenger is updated; otherwise a new
    RSVP is created.
    """
    values = {field: cleaned_data.get(field) for field in RSVP_FIELDS}
    for field in ("full_name", "mobile", "messenger", "email", "dietary", "note"):
        values[field] = (values[field] or "").strip()
    if not values["attending"]:
        values["guests"] = 0

    if invitation is not None:
        rsvp = Rsvp.objects.select_for_update().filter(invitation=invitation).first()
    else:
        rsvp = find_matching_rsvp(values["full_name"], values["mobile"], values["messenger"])

    created = rsvp is None
    if created:
        rsvp = Rsvp(invitation=invitation)
    for field, value in values.items():
        setattr(rsvp, field, value)
    rsvp.save()
    return rsvp, created
