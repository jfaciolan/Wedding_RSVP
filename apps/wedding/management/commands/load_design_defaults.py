"""Fill empty Site Admin content with the values shown in the design."""

import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.utils.dateparse import parse_date, parse_datetime, parse_time

from apps.wedding.models import Attire, AttireSwatch, Event, Faq, ScheduleItem, Venue, WeddingDetail

STILL_TO_FILL = [
    "Reception time and venue (Ceremony & Reception)",
    "Times for the order of the day items",
    "Google Maps link (Venue)",
    "FAQ answers, then tick Published (FAQs)",
    "RSVP deadline, default max guests and privacy text (RSVP settings)",
]


def _convert(field, value):
    """Turn a JSON value into what the model field expects."""
    if value is None:
        return None
    if isinstance(field, models.DateTimeField):
        return parse_datetime(value)
    if isinstance(field, models.DateField):
        return parse_date(value)
    if isinstance(field, models.TimeField):
        return parse_time(value)
    return value


def _is_empty(value):
    return value is None or value == ""


class Command(BaseCommand):
    help = (
        "Fill empty wedding content with the defaults from the design "
        "(assets/design_defaults.json). Existing values are kept unless --force is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", default=str(settings.BASE_DIR / "assets" / "design_defaults.json")
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing values and replace the schedule, swatches and FAQs.",
        )

    def handle(self, *args, file, force, **options):
        path = Path(file)
        if not path.exists():
            raise CommandError(f"Defaults file not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.force = force
        try:
            with transaction.atomic():
                self.fill_object("Wedding details", WeddingDetail.load(), data.get("wedding"))
                for kind, values in (data.get("events") or {}).items():
                    event = Event.load(Event.Kind(kind))
                    self.fill_object(event.get_kind_display(), event, values)
                self.fill_object("Venue", Venue.load(), data.get("venue"))
                self.fill_object("Attire", Attire.load(), data.get("attire"))
                self.fill_list("Order of the day", ScheduleItem, data.get("schedule"))
                self.fill_list("Attire colors", AttireSwatch, data.get("swatches"))
                self.fill_list("FAQs", Faq, data.get("faqs"), exclude=["answer"])
        except ValidationError as exc:
            raise CommandError(f"Invalid default value: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("Design defaults loaded."))
        self.stdout.write("Still to fill in the Site Admin:")
        for item in STILL_TO_FILL:
            self.stdout.write(f"  - {item}")

    def fill_object(self, label, obj, values):
        if not values:
            return
        filled = []
        for name, raw in values.items():
            field = obj._meta.get_field(name)
            value = _convert(field, raw)
            if _is_empty(value):
                continue
            if self.force or _is_empty(getattr(obj, name)):
                setattr(obj, name, value)
                filled.append(name)
        if filled:
            obj.full_clean()
            obj.save()
        self.stdout.write(f"{label}: filled {len(filled)} field(s)")

    def fill_list(self, label, model, rows, exclude=None):
        if not rows:
            return
        if model.objects.exists():
            if not self.force:
                self.stdout.write(f"{label}: kept existing {model.objects.count()} item(s)")
                return
            model.objects.all().delete()
        for row in rows:
            obj = model(
                **{
                    name: _convert(model._meta.get_field(name), value)
                    for name, value in row.items()
                }
            )
            obj.full_clean(exclude=exclude)
            obj.save()
        self.stdout.write(f"{label}: added {len(rows)} item(s)")
