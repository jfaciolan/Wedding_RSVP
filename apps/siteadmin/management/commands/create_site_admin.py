import getpass
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a Site Admin (staff, non-superuser) account for /site-admin/."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--email", default="")
        parser.add_argument(
            "--password",
            help="Avoid on shared machines; omit to be prompted. "
            "Also read from SITE_ADMIN_PASSWORD.",
        )

    def handle(self, *args, username, email, password, **options):
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise CommandError(f"User '{username}' already exists.")
        password = password or os.environ.get("SITE_ADMIN_PASSWORD")
        if not password:
            password = getpass.getpass("Password: ")
            if password != getpass.getpass("Password (again): "):
                raise CommandError("Passwords do not match.")
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc
        User.objects.create_user(username=username, email=email, password=password, is_staff=True)
        self.stdout.write(self.style.SUCCESS(f"Site Admin '{username}' created."))
