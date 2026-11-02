class NoIndexMiddleware:
    """Ask search engines not to index any page on the site."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("X-Robots-Tag", "noindex, nofollow")
        return response
