from django.shortcuts import render


def page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    # Rendered without the database-backed context, so it works even if the DB is down.
    return render(request, "errors/500.html", status=500)
