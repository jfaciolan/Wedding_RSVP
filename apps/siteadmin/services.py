"""Site Admin actions: CSV export."""

import csv

from django.utils import timezone

CSV_HEADER = [
    "Full name",
    "Mobile",
    "Messenger",
    "Email",
    "Attending",
    "Guests",
    "Dietary needs",
    "Note for the couple",
    "Invitation",
    "Has invite link",
    "Last updated (Asia/Manila)",
]


def write_rsvps_csv(rsvps, stream):
    """Write RSVPs as UTF-8 CSV with a BOM, so Excel shows accents and ñ correctly."""
    stream.write("﻿")
    writer = csv.writer(stream)
    writer.writerow(CSV_HEADER)
    for rsvp in rsvps:
        writer.writerow(
            [
                rsvp.full_name,
                rsvp.mobile,
                rsvp.messenger,
                rsvp.email,
                "Yes" if rsvp.attending else "No",
                rsvp.guests,
                rsvp.dietary,
                rsvp.note,
                rsvp.invitation.label if rsvp.invitation else "",
                "Yes" if rsvp.has_invite_link else "No",
                timezone.localtime(rsvp.updated_at).strftime("%Y-%m-%d %H:%M"),
            ]
        )
