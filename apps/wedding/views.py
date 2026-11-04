from django.shortcuts import render
from django.views import View

from apps.rsvp import selectors as rsvp_selectors
from apps.rsvp.forms import RsvpForm
from apps.rsvp.models import RsvpSettings

from .selectors import public_page_content


def build_rsvp_context(request, form=None):
    rsvp_settings = RsvpSettings.load()
    invitation = rsvp_selectors.invitation_from_session(request)
    max_guests = rsvp_selectors.max_guests_for(invitation, rsvp_settings)
    existing = rsvp_selectors.existing_rsvp_for(invitation)
    if form is None:
        form = RsvpForm(instance=existing, max_guests=max_guests)
    return {
        "slots_updated": bool(existing and existing.over_max),
        "slots_raised": bool(existing and existing.max_raised),
        "rsvp_settings": rsvp_settings,
        "rsvp_open": rsvp_selectors.rsvp_is_open(rsvp_settings),
        "invitation": invitation,
        "max_guests": max_guests,
        "form": form,
    }


def render_home(request, form=None, status=200):
    """Render the public page, or the Coming soon page until names and date are set."""
    content = public_page_content()
    if not content["wedding"].is_ready:
        return render(request, "wedding/coming_soon.html", content, status=status)
    content.update(build_rsvp_context(request, form))
    return render(request, "wedding/home.html", content, status=status)


class HomeView(View):
    def get(self, request):
        return render_home(request)
