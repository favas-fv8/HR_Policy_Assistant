import os, sys
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'
import django
django.setup()

from django.core.management import call_command
from django.db import connection
from documents.models import DocumentChunk

print("=== Current DocumentChunk embedding field ===")
embedding_field = DocumentChunk._meta.get_field('embedding')
print(f"Field type: {type(embedding_field)}")
print(f"Field: {embedding_field}")

print("\n=== Checking existing chunks ===")
chunks = DocumentChunk.objects.all()
print(f"Total chunks: {chunks.count()}")

print("\n=== Applying migration 0002 ===")
try:
    call_command('migrate', 'documents', '0002_alter_chunk_embedding_to_vector')
    print("Migration applied successfully!")
except Exception as e:
    print(f"Migration error (may already be applied): {e}")

print("\n=== Checking embedding after migration ===")
chunks = DocumentChunk.objects.all()
print(f"Total chunks: {chunks.count()}")

for c in chunks[:3]:
    emb = c.embedding
    print(f"Chunk {c.chunk_index}: type={type(emb).__name__}, len={len(emb) if emb else 0}, first3={emb[:3] if emb else None}")

print("\n=== Migration test complete ===")