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
cur.execute("SELECT 1")
print("Connection works:", cur.fetchall())
cur.close()
conn.close()