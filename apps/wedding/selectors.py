"""Read-only queries for wedding content."""

from .models import Attire, AttireSwatch, Event, Faq, ScheduleItem, Venue, WeddingDetail


def swatch_columns(count, preferred=6):
    """Desktop columns for the swatch grid: as close to 6 as possible without leaving
    a single swatch alone on the last row."""
    for columns in range(preferred, 3, -1):
        if count <= columns or count % columns != 1:
            return columns
    return preferred


def public_page_content():
    """Everything the public page shows, plus a visibility flag per section."""
    wedding = WeddingDetail.load()
    ceremony = Event.load(Event.Kind.CEREMONY)
    reception = Event.load(Event.Kind.RECEPTION)
    schedule = list(ScheduleItem.objects.all())
    venue = Venue.load()
    attire = Attire.load()
    swatches = list(AttireSwatch.objects.all())
    faqs = list(Faq.objects.filter(is_published=True))

    show_ceremony = ceremony.has_content
    show_reception = reception.has_content
    show_attire = bool(
        attire.heading or attire.ladies_guidance or attire.gentlemen_guidance or swatches
    )
    return {
        "wedding": wedding,
        "ceremony": ceremony,
        "reception": reception,
        "schedule": schedule,
        "venue": venue,
        "attire": attire,
        "swatches": swatches,
        "swatch_columns": swatch_columns(len(swatches)),
        "faqs": faqs,
        "show": {
            "invitation": bool(wedding.invitation_headline or wedding.invitation_message),
            "ceremony": show_ceremony,
            "reception": show_reception,
            "day": show_ceremony or show_reception or bool(schedule),
            "schedule": bool(schedule),
            "attire": show_attire,
            "venue": venue.has_content,
            "faq": bool(faqs),
        },
    }
