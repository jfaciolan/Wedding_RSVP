from django.urls import path

from . import views

app_name = "siteadmin"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("wedding/", views.WeddingDetailView.as_view(), name="wedding"),
    path("events/", views.EventsView.as_view(), name="events"),
    path("venue/", views.VenueView.as_view(), name="venue"),
    path("attire/", views.AttireView.as_view(), name="attire"),
    path("rsvp-settings/", views.RsvpSettingsView.as_view(), name="rsvp_settings"),
    path("invitations/", views.InvitationListView.as_view(), name="invitations"),
    path(
        "invitations/<int:pk>/revoke/",
        views.InvitationRevokeView.as_view(),
        name="invitation_revoke",
    ),
    path(
        "invitations/<int:pk>/edit/",
        views.InvitationEditView.as_view(),
        name="invitation_edit",
    ),
    path(
        "invitations/<int:pk>/delete/",
        views.InvitationDeleteView.as_view(),
        name="invitation_delete",
    ),
    path("rsvps/", views.RsvpListView.as_view(), name="rsvps"),
    path("rsvps/export.csv", views.RsvpExportView.as_view(), name="rsvp_export"),
    path("rsvps/<int:pk>/", views.RsvpEditView.as_view(), name="rsvp_edit"),
    path("content/<slug:kind>/", views.OrderedListView.as_view(), name="ordered_list"),
    path("content/<slug:kind>/add/", views.OrderedEditView.as_view(), name="ordered_add"),
    path(
        "content/<slug:kind>/<int:pk>/edit/",
        views.OrderedEditView.as_view(),
        name="ordered_edit",
    ),
    path(
        "content/<slug:kind>/<int:pk>/delete/",
        views.OrderedDeleteView.as_view(),
        name="ordered_delete",
    ),
    path(
        "content/<slug:kind>/<int:pk>/move/<str:direction>/",
        views.OrderedMoveView.as_view(),
        name="ordered_move",
    ),
]
