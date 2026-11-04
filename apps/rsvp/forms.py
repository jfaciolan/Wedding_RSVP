from django import forms

from .models import Rsvp

ATTENDING_CHOICES = [("yes", "Joyfully accepts"), ("no", "Regretfully declines")]


class RsvpForm(forms.ModelForm):
    attending = forms.TypedChoiceField(
        label="Will you be attending?",
        choices=ATTENDING_CHOICES,
        coerce=lambda value: value == "yes",
        widget=forms.RadioSelect,
        error_messages={"required": "Please let us know if you can attend."},
    )
    guests = forms.IntegerField(
        label="Number of guests", required=False, initial=1, widget=forms.NumberInput
    )
    # Honeypot: hidden from people, tempting to bots. Must stay empty.
    website = forms.CharField(required=False, label="Leave this field empty")

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
        ]
        labels = {
            "full_name": "Your full name",
            "messenger": "Facebook Messenger",
        }
        widgets = {
            "full_name": forms.TextInput(
                attrs={"placeholder": "As it appears on your invitation", "autocomplete": "name"}
            ),
            "mobile": forms.TextInput(
                attrs={
                    "placeholder": "e.g. 0917 123 4567",
                    "autocomplete": "tel",
                    "inputmode": "tel",
                }
            ),
            "messenger": forms.TextInput(
                attrs={"placeholder": "Username or m.me link", "autocapitalize": "off"}
            ),
            "email": forms.EmailInput(attrs={"placeholder": "Optional", "autocomplete": "email"}),
            "dietary": forms.TextInput(attrs={"placeholder": "Optional"}),
            "note": forms.Textarea(attrs={"placeholder": "Optional", "rows": 3}),
        }
        error_messages = {"full_name": {"required": "Please enter your full name."}}

    def __init__(self, *args, max_guests=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_guests = max_guests
        self.fields["guests"].widget.attrs.update({"min": 1, "max": max_guests})
        self.fields["website"].widget.attrs.update({"tabindex": "-1", "autocomplete": "off"})
        if self.instance.pk:
            self.initial["attending"] = "yes" if self.instance.attending else "no"
            if not self.instance.attending:
                self.initial["guests"] = 1
            elif self.instance.guests > max_guests:
                self.initial["guests"] = max_guests

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Your reply could not be sent.")
        return ""

    def clean(self):
        cleaned = super().clean()
        mobile = (cleaned.get("mobile") or "").strip()
        messenger = (cleaned.get("messenger") or "").strip()
        if not mobile and not messenger and "mobile" not in self.errors:
            message = "Please give a mobile number or a Messenger username."
            self.add_error("mobile", message)
            self.add_error("messenger", message)

        attending = cleaned.get("attending")
        if attending is True:
            guests = cleaned.get("guests")
            if guests is None:
                self.add_error("guests", "Please choose the number of guests.")
            elif not 1 <= guests <= self.max_guests:
                self.add_error("guests", f"Please choose between 1 and {self.max_guests} guests.")
        elif attending is False:
            cleaned["guests"] = 0
        return cleaned
