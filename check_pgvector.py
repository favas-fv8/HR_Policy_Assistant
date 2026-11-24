import psycopg2
conn = psycopg2.connect(
    dbname='hr_assistant',
    user='postgres',
    password='sql@321',
    host='localhost',
    port=5432
)
conn.autocommit = True
cur = conn.cursor()

# Check current DocumentChunk table structure
cur.execute('''
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'documents_documentchunk'
    ORDER BY ordinal_position
''')
print('DocumentChunk columns:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check if pgvector extension is available
try:
    cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
    print('pgvector extension created successfully')
except Exception as e:
    print(f'Could not create pgvector extension: {e}')

# Check current embeddings sample
cur.execute('SELECT embedding FROM documents_documentchunk LIMIT 1')
row = cur.fetchone()
if row:
    embedding = row[0]
    print(f'Sample embedding type: {type(embedding)}')
    print(f'Sample embedding length: {len(embedding) if hasattr(embedding, "__len__") else "N/A"}')
    if isinstance(embedding, str):
        import json
        data = json.loads(embedding)
        print(f'Parsed as JSON list, length: {len(data)}')

cur.close()
conn.close()
print('Done')