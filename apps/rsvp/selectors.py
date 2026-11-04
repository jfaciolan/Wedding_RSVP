"""Read-only RSVP queries."""

import math
from collections import defaultdict

from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce, Least
from django.utils import timezone

from apps.core.utils import normalize_messenger, normalize_mobile, normalize_name

from .models import Invitation, Rsvp, RsvpSettings

SESSION_INVITATION = "invitation_code"
SESSION_RSVP = "rsvp_id"


def rsvp_is_open(rsvp_settings=None, now=None):
    rsvp_settings = rsvp_settings or RsvpSettings.load()
    now = now or timezone.now()
    if not rsvp_settings.is_open:
        return False
    return rsvp_settings.deadline is None or now < rsvp_settings.deadline


def invitation_from_session(request):
    code = request.session.get(SESSION_INVITATION)
    if not code:
        return None
    return Invitation.objects.filter(code=code, is_revoked=False).first()


def max_guests_for(invitation, rsvp_settings=None):
    if invitation is not None:
        return invitation.max_guests
    return (rsvp_settings or RsvpSettings.load()).default_max_guests


def existing_rsvp_for(invitation):
    if invitation is None:
        return None
    return Rsvp.objects.filter(invitation=invitation).first()


def days_remaining(deadline, now=None):
    if deadline is None:
        return None
    now = now or timezone.now()
    seconds = (deadline - now).total_seconds()
    return max(0, math.ceil(seconds / 86400))


def invitation_stats():
    invitations = Invitation.objects.filter(is_revoked=False)
    total = invitations.count()
    responded = invitations.filter(rsvp__isnull=False).count()
    return {
        "total": total,
        "opened": invitations.filter(first_opened_at__isnull=False).count(),
        "responded": responded,
        "not_responded": total - responded,
    }


def response_stats():
    # RSVPs tied to a revoked invitation are kept but not counted until it is restored.
    # Guests over a lowered invitation max only count up to that max.
    rsvps = Rsvp.objects.exclude(invitation__is_revoked=True)
    attending = rsvps.filter(attending=True)
    allowed = Least("guests", Coalesce("invitation__max_guests", "guests"))
    return {
        "attending": attending.count(),
        "declined": rsvps.filter(attending=False).count(),
        "headcount": attending.aggregate(n=Sum(allowed))["n"] or 0,
        "over_max": attending.filter(guests__gt=F("invitation__max_guests")).count(),
        "max_raised": attending.filter(
            reply_max_guests__isnull=False, invitation__max_guests__gt=F("reply_max_guests")
        ).count(),
        "no_invite_link": rsvps.filter(invitation__isnull=True).count(),
        "total": rsvps.count(),
    }


def possible_duplicates():
    """RSVPs sharing a name, mobile or Messenger with another RSVP, keyed by RSVP id.

    Returns {rsvp_id: set of reasons}.
    """
    groups = defaultdict(list)
    for rsvp in Rsvp.objects.only("id", "full_name", "mobile", "messenger"):
        groups[("name", normalize_name(rsvp.full_name))].append(rsvp.pk)
        if mobile := normalize_mobile(rsvp.mobile):
            groups[("mobile", mobile)].append(rsvp.pk)
        if messenger := normalize_messenger(rsvp.messenger):
            groups[("messenger", messenger)].append(rsvp.pk)
    flagged = defaultdict(set)
    for (reason, _value), ids in groups.items():
        if len(ids) > 1:
            for pk in ids:
                flagged[pk].add(reason)
    return dict(flagged)


def search_rsvps(query="", status=""):
    rsvps = Rsvp.objects.select_related("invitation")
    if query:
        rsvps = rsvps.filter(
            Q(full_name__icontains=query)
            | Q(mobile__icontains=query)
            | Q(messenger__icontains=query)
            | Q(email__icontains=query)
        )
    if status == "attending":
        rsvps = rsvps.filter(attending=True)
    elif status == "declined":
        rsvps = rsvps.filter(attending=False)
    elif status == "no_link":
        rsvps = rsvps.filter(invitation__isnull=True)
    elif status == "duplicates":
        rsvps = rsvps.filter(pk__in=possible_duplicates().keys())
    return rsvps.order_by("full_name", "pk")


INVITEE_STATUSES = [
    ("attending", "Attending"),
    ("declined", "Declined"),
    ("opened", "Opened, no reply"),
    ("not_opened", "Not opened"),
]
INVITEE_FILTERS = [
    ("", "All"),
    *INVITEE_STATUSES,
    ("over_max", "Over max guests"),
    ("max_raised", "Max guests raised"),
    ("no_link", "No invite link"),
    ("revoked", "Revoked"),
]


def _invitee_row(invitation, rsvp):
    if rsvp is not None:
        status = "attending" if rsvp.attending else "declined"
    elif invitation.first_opened_at:
        status = "opened"
    else:
        status = "not_opened"
    return {
        "name": rsvp.full_name if rsvp else invitation.label,
        "invitation": invitation,
        "rsvp": rsvp,
        "status": status,
        "over_max": bool(rsvp and rsvp.over_max),
        "max_raised": bool(rsvp and rsvp.max_raised),
        "revoked": bool(invitation and invitation.is_revoked),
        "updated": rsvp.updated_at if rsvp else invitation.first_opened_at,
    }


def invitee_rows():
    """Every invitation (revoked ones flagged) plus every RSVP made without an invite link."""
    rows = []
    for invitation in Invitation.objects.select_related("rsvp"):
        try:
            rsvp = invitation.rsvp
        except Rsvp.DoesNotExist:
            rsvp = None
        rows.append(_invitee_row(invitation, rsvp))
    for rsvp in Rsvp.objects.filter(invitation__isnull=True):
        rows.append(_invitee_row(None, rsvp))
    rows.sort(key=lambda row: (row["name"].casefold(), row["name"]))
    return rows


def _matches(row, query):
    rsvp, invitation = row["rsvp"], row["invitation"]
    haystack = [row["name"]]
    if invitation:
        haystack.append(invitation.label)
    if rsvp:
        haystack += [rsvp.mobile, rsvp.messenger, rsvp.email]
    query = query.casefold()
    return any(query in value.casefold() for value in haystack if value)


def filter_invitees(rows, query="", status=""):
    if status == "revoked":
        rows = [row for row in rows if row["revoked"]]
    else:
        rows = [row for row in rows if not row["revoked"]]
        if status == "no_link":
            rows = [row for row in rows if row["invitation"] is None]
        elif status in ("over_max", "max_raised"):
            rows = [row for row in rows if row[status]]
        elif status in dict(INVITEE_STATUSES):
            rows = [row for row in rows if row["status"] == status]
    if query:
        rows = [row for row in rows if _matches(row, query)]
    return rows


def invitee_status_breakdown(rows):
    """Slices for the status chart. Revoked invitations are left out."""
    active = [row for row in rows if not row["revoked"]]
    total = len(active)
    slices, start = [], 0.0
    for key, label in INVITEE_STATUSES:
        count = sum(1 for row in active if row["status"] == key)
        percent = count * 100 / total if total else 0
        slices.append(
            {
                "key": key,
                "label": label,
                "count": count,
                "percent": round(percent),
                "start": round(start, 2),
                "end": round(start + percent, 2),
            }
        )
        start += percent
    return {
        "slices": slices,
        "total": total,
        "no_link": sum(1 for row in active if row["invitation"] is None),
    }
