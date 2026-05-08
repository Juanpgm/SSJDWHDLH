import psycopg2

DB_URL = "postgresql://postgres:hXSlvTgoalbvIKhKDhHLFYPiXbjgNzyM@interchange.proxy.rlwy.net:14181/railway"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

cur.execute("SELECT version()")
print("Version:", cur.fetchone()[0])

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
print("Tablas:", cur.fetchall())

cur.execute("SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables")
print("Filas por tabla:", cur.fetchall())

cur.close()
conn.close()
