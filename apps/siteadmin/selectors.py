"""Queries behind the Site Admin dashboard."""

from apps.rsvp import selectors as rsvp_selectors
from apps.rsvp.models import Rsvp, RsvpSettings


def dashboard_data(query="", status=""):
    rsvp_settings = RsvpSettings.load()
    duplicates = rsvp_selectors.possible_duplicates()
    if status not in dict(rsvp_selectors.INVITEE_FILTERS):
        status = ""
    invitees = rsvp_selectors.invitee_rows()
    duplicate_rsvps = Rsvp.objects.filter(pk__in=duplicates.keys()).order_by("full_name", "pk")
    return {
        "invitations": rsvp_selectors.invitation_stats(),
        "responses": rsvp_selectors.response_stats(),
        "rsvp_settings": rsvp_settings,
        "rsvp_open": rsvp_selectors.rsvp_is_open(rsvp_settings),
        "days_remaining": rsvp_selectors.days_remaining(rsvp_settings.deadline),
        "invitee_chart": rsvp_selectors.invitee_status_breakdown(invitees),
        "invitees": rsvp_selectors.filter_invitees(invitees, query, status),
        "invitee_query": query,
        "invitee_status": status,
        "invitee_filters": rsvp_selectors.INVITEE_FILTERS,
        "duplicates": [(rsvp, sorted(duplicates[rsvp.pk])) for rsvp in duplicate_rsvps],
    }
