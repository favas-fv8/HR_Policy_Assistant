import sys, os
sys.path.insert(0, r'D:\web projects\HR_Policy_Assistant\backend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrproject.settings'
import django
django.setup()
from django.db import connection
from documents.models import DocumentChunk, Document

cursor = connection.cursor()

# Check DocumentChunk count and embedding data
cursor.execute("SELECT COUNT(*) FROM documents_documentchunk")
chunk_count = cursor.fetchone()[0]
print(f'DocumentChunk total count: {chunk_count}')

if chunk_count > 0:
    cursor.execute("SELECT id, document_id, chunk_index, page_number, embedding FROM documents_documentchunk LIMIT 3")
    rows = cursor.fetchall()
    for row in rows:
        chunk_id, doc_id, chunk_idx, page, emb = row
        emb_type = type(emb).__name__
        emb_len = len(emb) if emb else 0
        print(f'  Chunk {chunk_id}: doc={doc_id}, idx={chunk_idx}, p={page}, type={emb_type}, len={emb_len}')
        if emb and isinstance(emb, list):
            print(f'    First 3 values: {emb[:3]}')
else:
    print('  No chunks found in database')

# Check Document count
cursor.execute("SELECT COUNT(*) FROM documents_document")
doc_count = cursor.fetchone()[0]
print(f'\nDocument total count: {doc_count}')

# Check if any documents have been processed
if doc_count > 0:
    cursor.execute("SELECT id, title, status, page_count FROM documents_document LIMIT 5")
    for row in cursor.fetchall():
        print(f'  Doc {row[0]}: {row[1]}, status={row[2]}, pages={row[3]}')