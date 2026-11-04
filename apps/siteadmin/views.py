from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView, UpdateView

from apps.core.services import move
from apps.rsvp import selectors as rsvp_selectors
from apps.rsvp.models import Invitation, Rsvp, RsvpSettings
from apps.wedding.models import Attire, AttireSwatch, Event, Faq, ScheduleItem, Venue, WeddingDetail

from . import forms, services
from .mixins import StaffRequiredMixin
from .selectors import dashboard_data


@method_decorator(never_cache, name="dispatch")
class LoginView(auth_views.LoginView):
    template_name = "siteadmin/login.html"
    authentication_form = forms.StaffAuthenticationForm
    redirect_authenticated_user = False


class LogoutView(auth_views.LogoutView):
    pass


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = "siteadmin/dashboard.html"

    def get_context_data(self, **kwargs):
        data = dashboard_data(
            query=self.request.GET.get("q", "").strip(),
            status=self.request.GET.get("status", ""),
        )
        return super().get_context_data(**kwargs, **data, nav="dashboard")


class SingletonEditView(StaffRequiredMixin, UpdateView):
    """Edit a one-row content model (wedding details, venue, attire, RSVP settings)."""

    template_name = "siteadmin/form_page.html"
    nav = ""
    title = ""
    intro = ""

    def get_object(self, queryset=None):
        return self.model.load()

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        messages.success(self.request, f"{self.title} saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, nav=self.nav, title=self.title, intro=self.intro)


class WeddingDetailView(SingletonEditView):
    model = WeddingDetail
    form_class = forms.WeddingDetailForm
    nav = "wedding"
    title = "Wedding details"
    intro = (
        "Names, date and the words on the invitation. The public page stays on "
        "“Coming soon” until both short names and the date are set."
    )


class VenueView(SingletonEditView):
    model = Venue
    form_class = forms.VenueForm
    nav = "venue"
    title = "Venue"
    intro = "Shown in the Venue card. “View on map” opens the Google Maps link."


class AttireView(SingletonEditView):
    model = Attire
    form_class = forms.AttireForm
    nav = "attire"
    title = "Attire"
    template_name = "siteadmin/attire.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            kind="swatches",
            config=ORDERED["swatches"],
            items=AttireSwatch.objects.all(),
        )


class RsvpSettingsView(SingletonEditView):
    model = RsvpSettings
    form_class = forms.RsvpSettingsForm
    nav = "rsvp_settings"
    title = "RSVP settings"
    intro = "Times are Philippine time (Asia/Manila)."


class EventsView(StaffRequiredMixin, View):
    """Ceremony and Reception edited side by side."""

    template_name = "siteadmin/events.html"

    def get_forms(self, data=None):
        return [
            (kind.label, forms.EventForm(data, instance=Event.load(kind), prefix=kind.value))
            for kind in Event.Kind
        ]

    def render(self, event_forms, status=200):
        return render(
            self.request,
            self.template_name,
            {"event_forms": event_forms, "nav": "events", "title": "Ceremony & Reception"},
            status=status,
        )

    def get(self, request):
        return self.render(self.get_forms())

    def post(self, request):
        event_forms = self.get_forms(request.POST)
        if all(form.is_valid() for _label, form in event_forms):
            for _label, form in event_forms:
                form.save()
            messages.success(request, "Ceremony & Reception saved.")
            return redirect("siteadmin:events")
        return self.render(event_forms, status=400)


# Reorderable lists sharing one set of views.
ORDERED = {
    "schedule": {
        "model": ScheduleItem,
        "form": forms.ScheduleItemForm,
        "title": "Order of the day",
        "singular": "item",
        "nav": "schedule",
        "back": "siteadmin:ordered_list",
        "intro": "The public timeline follows this order.",
    },
    "swatches": {
        "model": AttireSwatch,
        "form": forms.AttireSwatchForm,
        "title": "Attire colors",
        "singular": "color",
        "nav": "attire",
        "back": "siteadmin:attire",
        "intro": "",
    },
    "faqs": {
        "model": Faq,
        "form": forms.FaqForm,
        "title": "FAQs",
        "singular": "FAQ",
        "nav": "faqs",
        "back": "siteadmin:ordered_list",
        "intro": "Only published FAQs appear on the public page.",
    },
}


class OrderedMixin(StaffRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if kwargs["kind"] not in ORDERED:
            raise Http404
        self.kind = kwargs["kind"]
        self.config = ORDERED[self.kind]
        return super().dispatch(request, *args, **kwargs)

    def back_url(self):
        if self.config["back"] == "siteadmin:ordered_list":
            return reverse("siteadmin:ordered_list", args=[self.kind])
        return reverse(self.config["back"])

    def context(self, **extra):
        return {
            "kind": self.kind,
            "config": self.config,
            "nav": self.config["nav"],
            "title": self.config["title"],
            "back_url": self.back_url(),
            **extra,
        }


class OrderedListView(OrderedMixin, View):
    def get(self, request, kind):
        items = self.config["model"].objects.all()
        return render(request, "siteadmin/ordered_list.html", self.context(items=items))


class OrderedEditView(OrderedMixin, View):
    def get_object(self, pk):
        if pk is None:
            return None
        return get_object_or_404(self.config["model"], pk=pk)

    def get(self, request, kind, pk=None):
        form = self.config["form"](instance=self.get_object(pk))
        return render(request, "siteadmin/ordered_form.html", self.context(form=form, pk=pk))

    def post(self, request, kind, pk=None):
        form = self.config["form"](request.POST, instance=self.get_object(pk))
        if form.is_valid():
            form.save()
            messages.success(request, f"{self.config['singular'].capitalize()} saved.")
            return redirect(self.back_url())
        return render(
            request, "siteadmin/ordered_form.html", self.context(form=form, pk=pk), status=400
        )


class OrderedDeleteView(OrderedMixin, View):
    def get(self, request, kind, pk):
        obj = get_object_or_404(self.config["model"], pk=pk)
        return render(request, "siteadmin/confirm_delete.html", self.context(object=obj))

    def post(self, request, kind, pk):
        obj = get_object_or_404(self.config["model"], pk=pk)
        obj.delete()
        messages.success(request, f"{self.config['singular'].capitalize()} deleted.")
        return redirect(self.back_url())


class OrderedMoveView(OrderedMixin, View):
    def post(self, request, kind, pk, direction):
        if direction not in ("up", "down"):
            raise Http404
        move(get_object_or_404(self.config["model"], pk=pk), direction)
        return redirect(self.back_url())


class InvitationListView(StaffRequiredMixin, View):
    template_name = "siteadmin/invitations.html"

    def render(self, formset, status=200):
        invitations = Invitation.objects.select_related("rsvp").order_by("is_revoked", "label")
        return render(
            self.request,
            self.template_name,
            {
                "invitations": invitations,
                "formset": formset,
                "nav": "invitations",
                "title": "Invitations",
            },
            status=status,
        )

    def get(self, request):
        return self.render(forms.InvitationFormSet(queryset=Invitation.objects.none()))

    def post(self, request):
        formset = forms.InvitationFormSet(request.POST, queryset=Invitation.objects.none())
        if formset.is_valid():
            created = [obj for obj in formset.save()]
            messages.success(request, f"{len(created)} invitation(s) created.")
            return redirect("siteadmin:invitations")
        return self.render(formset, status=400)


def safe_next(request, default="siteadmin:invitations"):
    """The ?next= / POST next target if it stays on this site, else the default page."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return reverse(default)


class InvitationRevokeView(StaffRequiredMixin, View):
    """Revoking only hides the invitation; its RSVP is kept and counts again on restore."""

    def post(self, request, pk):
        invitation = get_object_or_404(Invitation, pk=pk)
        invitation.is_revoked = not invitation.is_revoked
        invitation.save(update_fields=["is_revoked", "updated_at"])
        state = "revoked" if invitation.is_revoked else "restored"
        messages.success(request, f"Invitation “{invitation.label}” {state}.")
        return redirect(safe_next(request))


class InvitationEditView(StaffRequiredMixin, UpdateView):
    """Edit an invitation's label and max guests. The link (code) stays the same."""

    model = Invitation
    form_class = forms.InvitationEditForm
    template_name = "siteadmin/form_page.html"

    def get_success_url(self):
        return safe_next(self.request)

    def form_valid(self, form):
        response = super().form_valid(form)
        invitation = self.object
        messages.success(self.request, f"Invitation “{invitation.label}” saved.")
        rsvp = Rsvp.objects.filter(invitation=invitation, attending=True).first()
        if rsvp and rsvp.guests > invitation.max_guests:
            messages.warning(
                self.request,
                f"“{invitation.label}” already RSVP'd for {rsvp.guests} guests, more than "
                f"the new max of {invitation.max_guests}. Only {invitation.max_guests} count, and "
                "they'll be asked to resubmit on their invite page.",
            )
        elif rsvp and rsvp.max_raised:
            messages.info(
                self.request,
                f"“{invitation.label}” will be told on their invite page that they can "
                f"now bring up to {invitation.max_guests} guests.",
            )
        return response

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            nav="invitations",
            title="Edit invitation",
            intro="The invite link stays the same, so links already sent keep working.",
            back_url=safe_next(self.request),
        )


class InvitationDeleteView(StaffRequiredMixin, View):
    """Delete an invite link for good. Any RSVP is kept as a "No invite link" response."""

    template_name = "siteadmin/confirm_delete_invitation.html"

    def get(self, request, pk):
        invitation = get_object_or_404(Invitation, pk=pk)
        rsvp = Rsvp.objects.filter(invitation=invitation).first()
        return render(
            request,
            self.template_name,
            {
                "invitation": invitation,
                "rsvp": rsvp,
                "next": safe_next(request),
                "nav": "invitations",
                "title": "Delete invite link",
            },
        )

    def post(self, request, pk):
        invitation = get_object_or_404(Invitation, pk=pk)
        had_rsvp = Rsvp.objects.filter(invitation=invitation).exists()
        label = invitation.label
        invitation.delete()
        kept = " Their RSVP was kept." if had_rsvp else ""
        messages.success(request, f"Invite link for “{label}” deleted.{kept}")
        return redirect(safe_next(request))


RSVP_FILTERS = [
    ("", "All"),
    ("attending", "Attending"),
    ("declined", "Declined"),
    ("no_link", "No invite link"),
    ("duplicates", "Possible duplicates"),
]


class RsvpListView(StaffRequiredMixin, View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        status = request.GET.get("status", "")
        rsvps = rsvp_selectors.search_rsvps(query, status)
        return render(
            request,
            "siteadmin/rsvps.html",
            {
                "rsvps": rsvps,
                "query": query,
                "status": status,
                "filters": RSVP_FILTERS,
                "duplicates": rsvp_selectors.possible_duplicates(),
                "nav": "rsvps",
                "title": "RSVPs",
            },
        )


class RsvpEditView(StaffRequiredMixin, UpdateView):
    model = Rsvp
    form_class = forms.RsvpAdminForm
    template_name = "siteadmin/form_page.html"

    def get_success_url(self):
        return reverse("siteadmin:rsvps")

    def form_valid(self, form):
        messages.success(self.request, f"RSVP for {form.instance.full_name} saved.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            nav="rsvps",
            title=f"RSVP: {self.object.full_name}",
            back_url=reverse("siteadmin:rsvps"),
        )


class RsvpExportView(StaffRequiredMixin, View):
    def get(self, request):
        stamp = timezone.localtime().strftime("%Y%m%d-%H%M")
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="rsvps-{stamp}.csv"'
        rsvps = Rsvp.objects.select_related("invitation").order_by("full_name", "pk")
        services.write_rsvps_csv(rsvps, response)
        return response
