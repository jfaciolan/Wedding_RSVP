from .local import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-only"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SITE_URL = "https://wedding.example"
