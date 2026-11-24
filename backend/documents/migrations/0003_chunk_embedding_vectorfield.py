from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_alter_chunk_embedding_to_vector'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # No-op: column type remains JSONB since pgvector not available
                # in the system PostgreSQL. The model uses VectorField (JSONField subclass)
                # which is compatible with JSONB storage.
            ],
            reverse_sql=[
                # Reverse: also a no-op
            ],
        ),
    ]