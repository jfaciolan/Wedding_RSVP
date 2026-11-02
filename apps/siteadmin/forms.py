from django import forms
from django.contrib.auth.forms import AuthenticationForm

from apps.rsvp.models import Invitation, Rsvp, RsvpSettings
from apps.wedding.models import Attire, AttireSwatch, Event, Faq, ScheduleItem, Venue, WeddingDetail


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%d")


class TimeInput(forms.TimeInput):
    input_type = "time"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%H:%M")


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%dT%H:%M")


class StaffAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError(
                "This account does not have Site Admin access.", code="not_staff"
            )


class WeddingDetailForm(forms.ModelForm):
    class Meta:
        model = WeddingDetail
        fields = [
            "groom_short_name",
            "bride_short_name",
            "groom_full_name",
            "bride_full_name",
            "families_line",
            "invitation_line",
            "wedding_datetime",
            "invitation_headline",
            "invitation_message",
            "footer_message",
        ]
        widgets = {
            "wedding_datetime": DateTimeInput(),
            "invitation_message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Names and date are what the public page needs to leave "Coming soon".
        for name in ("groom_short_name", "bride_short_name", "wedding_datetime"):
            self.fields[name].required = True


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["time", "date", "venue_name", "address", "city"]
        widgets = {
            "time": TimeInput(),
            "date": DateInput(),
            "address": forms.Textarea(attrs={"rows": 3}),
        }


class ScheduleItemForm(forms.ModelForm):
    class Meta:
        model = ScheduleItem
        fields = ["time", "title", "subtitle"]
        widgets = {"time": TimeInput()}


class VenueForm(forms.ModelForm):
    map_url = forms.URLField(
        label="Google Maps link", max_length=500, required=False, assume_scheme="https"
    )

    class Meta:
        model = Venue
        fields = ["name", "address", "map_url"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class AttireForm(forms.ModelForm):
    class Meta:
        model = Attire
        fields = ["heading", "tagline", "ladies_guidance", "gentlemen_guidance"]
        widgets = {
            "ladies_guidance": forms.Textarea(attrs={"rows": 4}),
            "gentlemen_guidance": forms.Textarea(attrs={"rows": 3}),
        }


class AttireSwatchForm(forms.ModelForm):
    class Meta:
        model = AttireSwatch
        fields = ["name", "hex"]
        widgets = {"hex": forms.TextInput(attrs={"placeholder": "#CBB8DC", "maxlength": 7})}


class FaqForm(forms.ModelForm):
    class Meta:
        model = Faq
        fields = ["question", "answer", "is_published"]
        widgets = {"answer": forms.Textarea(attrs={"rows": 4})}


class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ["label", "max_guests"]
        help_texts = {"label": ""}
        widgets = {"label": forms.TextInput(attrs={"placeholder": "e.g. Santos family"})}


class InvitationLabelForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ["label"]
        widgets = {"label": forms.TextInput(attrs={"placeholder": "e.g. Santos family"})}


InvitationFormSet = forms.modelformset_factory(
    Invitation, form=InvitationForm, extra=5, can_delete=False
)


class RsvpAdminForm(forms.ModelForm):
    attending = forms.TypedChoiceField(
        choices=[("yes", "Attending"), ("no", "Declined")],
        coerce=lambda value: value == "yes",
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Rsvp
        fields = [
            "full_name",
            "mobile",
            "messenger",
            "email",
            "attending",
            "guests",
            "dietary",
            "note",
            "invitation",
        ]
        widgets = {
            "dietary": forms.Textarea(attrs={"rows": 2}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["attending"] = "yes" if self.instance.attending else "no"
        self.fields["invitation"].required = False
        taken = Rsvp.objects.exclude(pk=self.instance.pk).exclude(invitation=None)
        self.fields["invitation"].queryset = Invitation.objects.exclude(
            pk__in=taken.values("invitation")
        )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("mobile") and not cleaned.get("messenger"):
            self.add_error("mobile", "Give a mobile number or a Messenger username.")
        if cleaned.get("attending") is False:
            cleaned["guests"] = 0
        elif cleaned.get("attending") is True and not cleaned.get("guests"):
            self.add_error("guests", "Attending RSVPs need at least 1 guest.")
        return cleaned


class RsvpSettingsForm(forms.ModelForm):
    class Meta:
        model = RsvpSettings
        fields = ["deadline", "is_open", "default_max_guests", "privacy_text"]
        widgets = {
            "deadline": DateTimeInput(),
            "privacy_text": forms.Textarea(attrs={"rows": 3}),
        }
