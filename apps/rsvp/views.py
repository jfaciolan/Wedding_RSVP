from django.conf import settings
from django.shortcuts import redirect, render
from django.views import View

from apps.core.utils import client_ip, is_rate_limited
from apps.wedding.models import WeddingDetail
from apps.wedding.views import render_home

from . import selectors, services
from .forms import RsvpForm
from .models import Invitation, Rsvp, RsvpSettings


class InviteLinkView(View):
    def get(self, request, code):
        invitation = Invitation.objects.filter(code=code, is_revoked=False).first()
        if invitation is None:
            request.session.pop(selectors.SESSION_INVITATION, None)
            return render(
                request,
                "rsvp/invalid_link.html",
                {"wedding": WeddingDetail.load()},
                status=404,
            )
        services.mark_opened(invitation)
        request.session[selectors.SESSION_INVITATION] = invitation.code
        return redirect("wedding:home")


class RsvpSubmitView(View):
    def get(self, request):
        return redirect("/#rsvp")

    def post(self, request):
        rsvp_settings = RsvpSettings.load()
        wedding = WeddingDetail.load()
        if not wedding.is_ready or not selectors.rsvp_is_open(rsvp_settings):
            return render(
                request,
                "rsvp/closed.html",
                {"wedding": wedding, "rsvp_settings": rsvp_settings},
                status=403,
            )
        if is_rate_limited(
            f"rsvp:{client_ip(request)}", settings.RSVP_RATE_LIMIT, settings.RSVP_RATE_WINDOW
        ):
            return render(request, "rsvp/rate_limited.html", {"wedding": wedding}, status=429)

        invitation = selectors.invitation_from_session(request)
        max_guests = selectors.max_guests_for(invitation, rsvp_settings)
        form = RsvpForm(
            request.POST,
            instance=selectors.existing_rsvp_for(invitation),
            max_guests=max_guests,
        )
        if not form.is_valid():
            return render_home(request, form=form, status=400)

        rsvp, _created = services.save_rsvp(form.cleaned_data, invitation=invitation)
        request.session[selectors.SESSION_RSVP] = rsvp.pk
        return redirect("rsvp:thanks")


class RsvpThanksView(View):
    def get(self, request):
        rsvp_id = request.session.get(selectors.SESSION_RSVP)
        rsvp = Rsvp.objects.filter(pk=rsvp_id).first() if rsvp_id else None
        if rsvp is None:
            return redirect("wedding:home")
        return render(
            request,
            "rsvp/thanks.html",
            {
                "rsvp": rsvp,
                "wedding": WeddingDetail.load(),
                "rsvp_settings": RsvpSettings.load(),
                "rsvp_open": selectors.rsvp_is_open(),
            },
        )
