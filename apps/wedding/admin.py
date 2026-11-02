"""Fallback registrations for Django's /admin/ (superusers only)."""

from django.contrib import admin

from .models import Attire, AttireSwatch, Event, Faq, ScheduleItem, Venue, WeddingDetail

admin.site.register([WeddingDetail, Event, Venue, Attire])


@admin.register(ScheduleItem)
class ScheduleItemAdmin(admin.ModelAdmin):
    list_display = ["title", "time", "position"]


@admin.register(AttireSwatch)
class AttireSwatchAdmin(admin.ModelAdmin):
    list_display = ["name", "hex", "position"]


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ["question", "is_published", "position"]
