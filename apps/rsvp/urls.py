from django.urls import path

from . import views

app_name = "rsvp"

urlpatterns = [
    path("i/<str:code>/", views.InviteLinkView.as_view(), name="invite"),
    path("rsvp/", views.RsvpSubmitView.as_view(), name="submit"),
    path("rsvp/thanks/", views.RsvpThanksView.as_view(), name="thanks"),
]
