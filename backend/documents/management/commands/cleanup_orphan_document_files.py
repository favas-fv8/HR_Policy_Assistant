"""Report (and optionally remove) uploaded PDF files with no Document row.

Dry-run is the default. Files are only considered inside the Document.file
upload directory, and only files not referenced by any Document are reported.
Use --apply to actually delete the reported orphan files.
"""
from django.core.management.base import BaseCommand

from documents.models import Document


class Command(BaseCommand):
    help = "Report or remove orphaned uploaded document files (dry-run by default)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually delete orphan files. Without this flag, only report them.",
        )

    def handle(self, *args, **options):
        apply = options.get("apply", False)
        field = Document._meta.get_field("file")
        upload_to = str(field.upload_to or "").strip("/")
        storage = field.storage

        referenced = {
            name
            for name in Document.objects.exclude(file="").values_list("file", flat=True)
        }

        try:
            _dirs, files = storage.listdir(upload_to)
        except (NotImplementedError, OSError) as exc:
            self.stderr.write(
                self.style.WARNING(
                    f"Cannot list storage directory {upload_to!r}: {exc}"
                )
            )
            return

        orphans = []
        for entry in files:
            candidate = f"{upload_to}/{entry}" if upload_to else entry
            # Never consider anything outside the upload directory.
            if ".." in entry or entry.startswith("/"):
                continue
            if candidate not in referenced:
                orphans.append(candidate)

        if not orphans:
            self.stdout.write(self.style.SUCCESS("No orphaned document files found."))
            return

        for candidate in orphans:
            action = "DELETE" if apply else "DRY-RUN"
            self.stdout.write(f"[{action}] {candidate}")

        if not apply:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(orphans)} orphan file(s) reported. Re-run with --apply to delete."
                )
            )
            return

        for candidate in orphans:
            if storage.exists(candidate):
                storage.delete(candidate)
        self.stdout.write(self.style.SUCCESS(f"Deleted {len(orphans)} orphan file(s)."))
