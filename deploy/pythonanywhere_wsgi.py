"""WSGI entry point for PythonAnywhere.

Paste this into the Web tab's "WSGI configuration file"
(/var/www/jrfaciolan_pythonanywhere_com_wsgi.py). Environment variables are read from
/home/jrfaciolan/Wedding_RSVP/.env by config/settings/base.py.
"""

import os
import sys

PROJECT_DIR = "/home/jrfaciolan/Wedding_RSVP"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
