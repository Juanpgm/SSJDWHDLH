"""
apply_migrations.py
Aplica las migraciones SQL en orden sobre la base de datos objetivo.
Uso:
    python scripts/apply_migrations.py
    DATABASE_URL=postgresql://... python scripts/apply_migrations.py
"""
import os
import sys
import glob
import psycopg2

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:hXSlvTgoalbvIKhKDhHLFYPiXbjgNzyM@interchange.proxy.rlwy.net:14181/railway",
)

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")


def get_applied_migrations(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id          SERIAL PRIMARY KEY,
            filename    TEXT NOT NULL UNIQUE,
            applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    cur.execute("SELECT filename FROM _migrations ORDER BY filename")
    return {row[0] for row in cur.fetchall()}


def apply_migrations(conn):
    cur = conn.cursor()
    applied = get_applied_migrations(cur)
    conn.commit()

    migration_files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
    if not migration_files:
        print("No se encontraron archivos .sql en migrations/")
        return

    for filepath in migration_files:
        filename = os.path.basename(filepath)
        if filename in applied:
            print(f"  [skip]  {filename}")
            continue

        print(f"  [apply] {filename} ...", end=" ", flush=True)
        with open(filepath, "r", encoding="utf-8") as f:
            sql = f.read()

        try:
            cur.execute(sql)
            cur.execute("INSERT INTO _migrations (filename) VALUES (%s)", (filename,))
            conn.commit()
            print("OK")
        except Exception as exc:
            conn.rollback()
            print(f"ERROR\n    {exc}")
            sys.exit(1)

    cur.close()


def main():
    print(f"Conectando a: {DATABASE_URL.split('@')[1]}")
    try:
        conn = psycopg2.connect(DATABASE_URL)
    except psycopg2.OperationalError as exc:
        print(f"No se pudo conectar: {exc}")
        sys.exit(1)

    print("Aplicando migraciones...\n")
    apply_migrations(conn)
    conn.close()
    print("\nListo.")


if __name__ == "__main__":
    main()
