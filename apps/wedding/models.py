"""Wedding content. Every value is entered in the Site Admin; nothing is hardcoded."""

from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import OrderedModel, SingletonModel, TimeStampedModel


class WeddingDetail(SingletonModel, TimeStampedModel):
    groom_short_name = models.CharField("Groom's short name", max_length=80, blank=True)
    bride_short_name = models.CharField("Bride's short name", max_length=80, blank=True)
    groom_full_name = models.CharField("Groom's full name", max_length=160, blank=True)
    bride_full_name = models.CharField("Bride's full name", max_length=160, blank=True)
    families_line = models.CharField(
        max_length=160, blank=True, help_text='e.g. "Together with their families"'
    )
    invitation_line = models.CharField(
        max_length=160, blank=True, help_text='e.g. "invite you to celebrate their wedding"'
    )
    wedding_datetime = models.DateTimeField(
        "Wedding date and time", null=True, blank=True, help_text="Philippine time."
    )
    invitation_headline = models.CharField(max_length=240, blank=True)
    invitation_message = models.TextField(blank=True)
    footer_message = models.CharField(max_length=240, blank=True)

    class Meta:
        verbose_name = "wedding details"
        verbose_name_plural = "wedding details"

    def __str__(self):
        return self.couple_names or "Wedding details"

    @property
    def is_ready(self):
        """The public page needs at least the couple's names and the date."""
        return bool(self.groom_short_name and self.bride_short_name and self.wedding_datetime)

    @property
    def couple_names(self):
        if self.groom_short_name and self.bride_short_name:
            return f"{self.groom_short_name} & {self.bride_short_name}"
        return ""

    @property
    def full_names(self):
        return " & ".join(n for n in (self.groom_full_name, self.bride_full_name) if n)


class Event(TimeStampedModel):
    class Kind(models.TextChoices):
        CEREMONY = "ceremony", "Ceremony"
        RECEPTION = "reception", "Reception"

    kind = models.CharField(max_length=20, choices=Kind.choices, unique=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    venue_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True, help_text="One address line per row.")
    city = models.CharField(
        max_length=120, blank=True, help_text="Short place name shown in the hero (ceremony)."
    )

    class Meta:
        ordering = ["kind"]

    def __str__(self):
        return self.get_kind_display()

    @classmethod
    def load(cls, kind):
        obj, _ = cls.objects.get_or_create(kind=kind)
        return obj

    @property
    def has_content(self):
        return bool(self.time or self.venue_name)

    @property
    def address_lines(self):
        return [line.strip() for line in self.address.splitlines() if line.strip()]


class ScheduleItem(OrderedModel, TimeStampedModel):
    time = models.TimeField(null=True, blank=True)
    title = models.CharField(max_length=160)
    subtitle = models.CharField(max_length=240, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "order of the day item"

    def __str__(self):
        return self.title


class Venue(SingletonModel, TimeStampedModel):
    name = models.CharField("Venue name", max_length=200, blank=True)
    address = models.TextField("Full address", blank=True, help_text="One line per row.")
    map_url = models.URLField("Google Maps link", max_length=500, blank=True)

    def __str__(self):
        return self.name or "Venue"

    @property
    def has_content(self):
        return bool(self.name)

    @property
    def address_lines(self):
        return [line.strip() for line in self.address.splitlines() if line.strip()]


class Attire(SingletonModel, TimeStampedModel):
    heading = models.CharField(max_length=160, blank=True)
    tagline = models.CharField(max_length=160, blank=True)
    ladies_guidance = models.TextField("Guidance for ladies", blank=True)
    gentlemen_guidance = models.TextField("Guidance for gentlemen", blank=True)

    def __str__(self):
        return self.heading or "Attire"


hex_validator = RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Enter a hex color like #CBB8DC.")


class AttireSwatch(OrderedModel, TimeStampedModel):
    name = models.CharField(max_length=60)
    hex = models.CharField("Hex color", max_length=7, validators=[hex_validator])

    class Meta(OrderedModel.Meta):
        verbose_name = "attire color"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.hex = self.hex.upper()
        super().save(*args, **kwargs)


class Faq(OrderedModel, TimeStampedModel):
    question = models.CharField(max_length=240)
    answer = models.TextField()
    is_published = models.BooleanField("Published", default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
