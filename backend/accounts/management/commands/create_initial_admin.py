"""Django management command to create the initial HR Admin account."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Create the initial HR Admin account (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            type=str,
            default="admin123",
            help='Initial password for the admin account (default: "admin123"). '
                 "Set via HR_INITIAL_ADMIN_PASSWORD env var for security.",
        )

    def handle(self, *args, **options):
        password = options["password"]
        username = "admin"

        # Check if an admin account already exists with username "admin"
        existing = User.objects.filter(username=username).first()

        if existing is not None:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Admin account already exists: "{username}" '
                    f'(role={existing.role}, is_staff={existing.is_staff}, '
                    f'is_superuser={existing.is_superuser}, is_active={existing.is_active})'
                )
            )
            # Report state without overwriting
            if not (existing.is_staff and existing.is_superuser and existing.role == "hr_admin"):
                self.stdout.write(
                    self.style.WARNING(
                        'Existing admin account does not have the expected '
                        'hr_admin/is_staff/is_superuser flags. '
                        'This may need manual attention.'
                    )
                )
            return

        # Create the initial HR Admin account
        with transaction.atomic():
            user = User.objects.create_superuser(
                username=username,
                password=password,
                email="",
            )
            user.role = "hr_admin"
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created initial HR Admin account: "{username}"'
            )
        )
        self.stdout.write(
            self.style.NOTICE(
                'Initial password set to: "%s"\n'
                'Change this securely after initial setup via the management command '
                'or Django admin."' % password
            )
        )