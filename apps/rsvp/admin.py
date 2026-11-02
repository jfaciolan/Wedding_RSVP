"""Fallback registrations for Django's /admin/ (superusers only)."""

from django.contrib import admin

from .models import Invitation, Rsvp, RsvpSettings

admin.site.register(RsvpSettings)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["label", "max_guests", "first_opened_at", "is_revoked"]
    readonly_fields = ["code"]


@admin.register(Rsvp)
class RsvpAdmin(admin.ModelAdmin):
    list_display = ["full_name", "attending", "guests", "invitation", "updated_at"]
    search_fields = ["full_name", "mobile", "messenger", "email"]
    list_filter = ["attending"]
