import psycopg2

conn = psycopg2.connect(
    dbname="hr_assistant",
    user="postgres",
    password="sql@321",
    host="localhost",
    port=5432
)
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    print("pgvector extension created successfully")
except Exception as e:
    print(f"Could not create vector extension: {e}")

cur.close()
conn.close()
print("Done")