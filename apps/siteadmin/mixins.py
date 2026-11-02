from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


@method_decorator(never_cache, name="dispatch")
class StaffRequiredMixin(AccessMixin):
    """Only active staff users. Everyone else is sent to the Site Admin login page."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_authenticated and user.is_active and user.is_staff):
            return redirect_to_login(request.get_full_path(), self.get_login_url())
        return super().dispatch(request, *args, **kwargs)
