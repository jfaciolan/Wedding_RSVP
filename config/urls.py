from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("site-admin/", include("apps.siteadmin.urls")),
    path("", include("apps.rsvp.urls")),
    path("", include("apps.wedding.urls")),
]

handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"
