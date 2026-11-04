import secrets

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from apps.core.models import SingletonModel, TimeStampedModel


class RsvpSettings(SingletonModel, TimeStampedModel):
    deadline = models.DateTimeField(
        "RSVP deadline", null=True, blank=True, help_text="Philippine time (Asia/Manila)."
    )
    is_open = models.BooleanField(
        "RSVPs open", default=True, help_text="Turn off to close the form before the deadline."
    )
    default_max_guests = models.PositiveSmallIntegerField(
        "Default max guests",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="For guests who RSVP without an invite link.",
    )
    privacy_text = models.TextField(
        "Privacy / consent text", blank=True, help_text="Shown under the RSVP form."
    )

    class Meta:
        verbose_name = "RSVP settings"
        verbose_name_plural = "RSVP settings"

    def __str__(self):
        return "RSVP settings"


def generate_code():
    return secrets.token_urlsafe(16)


class Invitation(TimeStampedModel):
    label = models.CharField(max_length=160, help_text='e.g. "Santos family"')
    max_guests = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    code = models.CharField(max_length=64, unique=True, default=generate_code, editable=False)
    is_revoked = models.BooleanField(default=False)
    first_opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["label", "pk"]

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse("rsvp:invite", args=[self.code])

    @property
    def full_link(self):
        return f"{settings.SITE_URL}{self.get_absolute_url()}"


class Rsvp(TimeStampedModel):
    invitation = models.OneToOneField(
        Invitation, null=True, blank=True, on_delete=models.SET_NULL, related_name="rsvp"
    )
    full_name = models.CharField(max_length=160)
    mobile = models.CharField("Mobile number", max_length=40, blank=True)
    messenger = models.CharField("Facebook Messenger", max_length=200, blank=True)
    email = models.EmailField(blank=True)
    attending = models.BooleanField()
    guests = models.PositiveSmallIntegerField(default=0)
    dietary = models.TextField("Dietary needs or allergies", blank=True)
    note = models.TextField("A note for the couple", blank=True)
    reply_max_guests = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        editable=False,
        help_text="The invitation's max guests when the guest last replied.",
    )

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "RSVP"

    def __str__(self):
        return self.full_name

    @property
    def has_invite_link(self):
        return self.invitation_id is not None

    @property
    def over_max(self):
        """Attending with more guests than the invitation now allows (max was lowered)."""
        return bool(
            self.attending and self.invitation_id and self.guests > self.invitation.max_guests
        )

    @property
    def max_raised(self):
        """Attending, and the invitation's max went up since the guest last replied."""
        return bool(
            self.attending
            and self.invitation_id
            and self.reply_max_guests is not None
            and self.invitation.max_guests > self.reply_max_guests
        )

    @property
    def allowed_guests(self):
        """Guests that count: capped at the invitation's current max."""
        if self.invitation_id:
            return min(self.guests, self.invitation.max_guests)
        return self.guests
