from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        # Note: Vector column type change (JSONB -> vector(3072)) is only applicable
        # when using pgvector-enabled PostgreSQL (Docker pgvector/pgvector:pg18).
        # On system PostgreSQL, the embedding column remains JSONB, which is
        # compatible with the VectorField model (a JSONField subclass).
        #
        # The following operations are conditional and would be applied when
        # migrating to the pgvector Docker container:
        # - CREATE EXTENSION IF NOT EXISTS vector
        # - ALTER TABLE documents_documentchunk ALTER COLUMN embedding TYPE vector(3072)
        # - CREATE INDEX ON documents_documentchunk USING hnsw (embedding vector_cosine_ops)
        #
        # For now, this migration is a no-op on system PostgreSQL, and the
        # VectorField (JSONField subclass) handles 3072-dimensional embedments
        # stored as JSONB.
    ]