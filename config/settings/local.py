from .base import *  # noqa: F403
from .base import env_list

DEBUG = True
SECRET_KEY = SECRET_KEY or "local-dev-only-not-secret"  # noqa: F405
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
}
