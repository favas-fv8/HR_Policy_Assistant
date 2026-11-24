import psycopg2

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="sql@321",
    host="localhost",
    port=5432
)
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT * FROM pg_available_extensions WHERE name = 'vector'")
result = cur.fetchall()
print("pgvector available extensions:", result)

cur.close()
conn.close()