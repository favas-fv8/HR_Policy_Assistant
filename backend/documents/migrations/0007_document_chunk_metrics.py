from django.db import migrations, models


def backfill_chunk_metrics(apps, schema_editor):
    DocumentChunk = apps.get_model("documents", "DocumentChunk")
    for chunk in DocumentChunk.objects.all().only("id", "page_number", "chunk_text", "page_start", "page_end", "char_count"):
        text = chunk.chunk_text or ""
        changed = False
        if not chunk.page_start:
            chunk.page_start = chunk.page_number or 1
            changed = True
        if not chunk.page_end:
            chunk.page_end = chunk.page_number or chunk.page_start or 1
            changed = True
        if not chunk.char_count:
            chunk.char_count = len(text)
            changed = True
        # token_count left 0 for legacy rows (unknown tokenizer); new processing fills it.
        if changed:
            chunk.save(update_fields=["page_start", "page_end", "char_count"])


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0006_add_processing_attempt_tracking"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="extracted_characters",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="document",
            name="extracted_tokens",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="documentchunk",
            name="page_start",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="documentchunk",
            name="page_end",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="documentchunk",
            name="char_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="documentchunk",
            name="token_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="documentchunk",
            name="section_heading",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="documentchunk",
            name="embedding_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("embedded", "Embedded"), ("failed", "Failed")],
                default="embedded",
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_chunk_metrics, migrations.RunPython.noop),
    ]
