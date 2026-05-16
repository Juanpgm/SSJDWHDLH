import os
import re
import ssl
import csv
from io import BytesIO, StringIO
from contextlib import contextmanager
from typing import Any
from urllib.parse import parse_qsl, quote, unquote, urlsplit, urlunsplit

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
import pg8000
import pyarrow as pa
import pyarrow.parquet as pq

APP_TITLE = "SyJDWH Data API"
APP_VERSION = "1.0.0"
TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SURROUNDING_QUOTES = " \t\r\n\"'`“”‘’«»"


def normalize_token(value: str) -> str:
    return value.strip(SURROUNDING_QUOTES)


def build_database_url() -> str:
    """Build DATABASE_URL from environment when not explicitly provided."""
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        return sanitize_database_url(direct_url)

    user = os.getenv("POSTGRES_USER", os.getenv("PGUSER", "postgres"))
    password = os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", "postgres"))
    host = os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "localhost"))
    port = os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432"))
    database = os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "railway"))

    user = normalize_token(user)
    password = normalize_token(password)
    host = normalize_token(host)
    port = normalize_token(port)
    database = normalize_token(database)

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def sanitize_database_url(database_url: str) -> str:
    """Normalize URL user/password to avoid libpq UTF-8 decode failures."""
    if not database_url.startswith(("postgresql://", "postgres://")):
        return database_url

    parsed = urlsplit(database_url)
    if parsed.username is None:
        return database_url

    safe_user = quote(unquote(parsed.username), safe="")
    safe_pass = ""
    if parsed.password is not None:
        safe_pass = quote(unquote(parsed.password), safe="")

    host = parsed.hostname or ""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"

    host_port = f"{host}:{parsed.port}" if parsed.port else host
    user_info = safe_user
    if parsed.password is not None:
        user_info = f"{user_info}:{safe_pass}"

    netloc = f"{user_info}@{host_port}"

    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def database_url_to_connect_kwargs(database_url: str) -> dict[str, Any]:
    """Parse PostgreSQL URL into explicit pg8000 kwargs."""
    parsed = urlsplit(database_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        return {}

    kwargs: dict[str, Any] = {}
    if parsed.username is not None:
        kwargs["user"] = normalize_token(
            unquote(parsed.username, encoding="latin-1", errors="strict")
        )
    if parsed.password is not None:
        kwargs["password"] = normalize_token(
            unquote(parsed.password, encoding="latin-1", errors="strict")
        )
    if parsed.hostname:
        kwargs["host"] = parsed.hostname
    if parsed.port:
        kwargs["port"] = parsed.port

    dbname = parsed.path.lstrip("/")
    if dbname:
        kwargs["database"] = normalize_token(
            unquote(dbname, encoding="latin-1", errors="strict")
        )

    sslmode = None
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "sslmode":
            sslmode = value

    if sslmode in {"require", "verify-ca", "verify-full"}:
        kwargs["ssl_context"] = ssl.create_default_context()

    return kwargs


def connect_db():
    """Create a DB connection, preferring explicit kwargs over DSN parsing."""
    connect_kwargs = database_url_to_connect_kwargs(DATABASE_URL)
    if not connect_kwargs:
        raise ValueError("DATABASE_URL invalida para PostgreSQL")

    try:
        conn = pg8000.connect(**connect_kwargs)
    except Exception as exc:
        details = exc.args[0] if exc.args else None
        sql_state = details.get("C") if isinstance(details, dict) else None
        if sql_state == "3D000" and connect_kwargs.get("database") == "railway":
            fallback_kwargs = dict(connect_kwargs)
            fallback_kwargs["database"] = "postgres"
            conn = pg8000.connect(**fallback_kwargs)
        else:
            raise

    return conn


DATABASE_URL = build_database_url()

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=(
        "API para explorar tablas y datos de PostgreSQL/PostGIS. "
        "Swagger disponible en /docs y OpenAPI en /openapi.json."
    ),
)


@contextmanager
def db_cursor() -> Any:
    """Yield a DB cursor and always close DB resources safely."""
    conn = None
    cur = None
    try:
        conn = connect_db()
        cur = conn.cursor()
        yield cur
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def assert_safe_table_name(table_name: str) -> None:
    if not TABLE_NAME_PATTERN.fullmatch(table_name):
        raise HTTPException(status_code=400, detail="Nombre de tabla no valido")


def table_exists(cur: Any, table_name: str) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = %s
        ) AS exists
        """,
        (table_name,),
    )
    row = cur.fetchone()
    return bool(row and row[0])


def rows_to_dicts(cur: Any, rows: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in rows]


def fetch_table_rows(cur: Any, table_name: str, limit: int | None = None) -> tuple[list[str], list[tuple[Any, ...]]]:
    quoted_table = f'"{table_name}"'
    if limit is None:
        query = f"SELECT * FROM {quoted_table}"
        cur.execute(query)
    else:
        query = f"SELECT * FROM {quoted_table} LIMIT %s"
        cur.execute(query, (limit,))

    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return columns, rows


def fetch_tables() -> list[dict[str, Any]]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_type, table_name
            """
        )
        rows = cur.fetchall()
        return rows_to_dicts(cur, rows)


@app.get("/health", tags=["health"])
def health() -> dict[str, Any]:
    """Simple liveness check — no DB required."""
    return {"status": "ok", "version": APP_VERSION}


@app.get("/health/db", tags=["health"])
def db_health() -> dict[str, Any]:
    """Check if database is reachable and report basic metadata."""
    try:
        with db_cursor() as cur:
            cur.execute("SELECT current_database() AS db, now() AS ts")
            row = cur.fetchone()
            return {
                "status": "ok",
                "database": row[0],
                "timestamp": row[1],
            }
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"DB no disponible: {exc}") from exc


@app.get("/tables", tags=["tables"])
def list_tables() -> dict[str, Any]:
    """List public tables and views from the database."""
    try:
        rows = fetch_tables()
        return {"count": len(rows), "tables": rows}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Error listando tablas: {exc}") from exc


@app.get("/tables/{table_name}/data", tags=["data"])
def get_table_data(
    table_name: str,
    id: str | None = Query(default=None, description="Valor del ID para filtrar"),
    id_column: str = Query(default="id", description="Nombre de columna ID"),
    limit: int = Query(default=100, ge=1),
) -> dict[str, Any]:
    """
    Return rows from a table.

    - Sin `id`: retorna hasta `limit` filas.
    - Con `id`: filtra por la columna indicada en `id_column`.
    """
    assert_safe_table_name(table_name)
    assert_safe_table_name(id_column)

    try:
        with db_cursor() as cur:
            if not table_exists(cur, table_name):
                raise HTTPException(status_code=404, detail="Tabla no encontrada")

            quoted_table = f'"{table_name}"'
            if id is None:
                query = f"SELECT * FROM {quoted_table} LIMIT %s"
                cur.execute(query, (limit,))
            else:
                quoted_column = f'"{id_column}"'
                query = f"SELECT * FROM {quoted_table} WHERE {quoted_column} = %s LIMIT %s"
                cur.execute(query, (id, limit))

            rows = rows_to_dicts(cur, cur.fetchall())
            return {
                "table": table_name,
                "count": len(rows),
                "rows": rows,
            }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Error consultando datos: {exc}") from exc


@app.get("/tables/{table_name}/download/csv", tags=["data"])
def download_table_csv(
    table_name: str,
    limit: int | None = Query(default=None, ge=1, description="Limite opcional de filas"),
) -> StreamingResponse:
    """Download any public table as CSV."""
    assert_safe_table_name(table_name)

    try:
        with db_cursor() as cur:
            if not table_exists(cur, table_name):
                raise HTTPException(status_code=404, detail="Tabla no encontrada")

            columns, rows = fetch_table_rows(cur, table_name, limit=limit)

        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(columns)
        writer.writerows(rows)

        payload = BytesIO(csv_buffer.getvalue().encode("utf-8"))
        filename = f"{table_name}.csv"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(payload, media_type="text/csv; charset=utf-8", headers=headers)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Error descargando CSV: {exc}") from exc


@app.get("/tables/{table_name}/download/parquet", tags=["data"])
def download_table_parquet(
    table_name: str,
    limit: int | None = Query(default=None, ge=1, description="Limite opcional de filas"),
) -> StreamingResponse:
    """Download any public table as Parquet."""
    assert_safe_table_name(table_name)

    try:
        with db_cursor() as cur:
            if not table_exists(cur, table_name):
                raise HTTPException(status_code=404, detail="Tabla no encontrada")

            columns, rows = fetch_table_rows(cur, table_name, limit=limit)

        data = {column: [row[idx] for row in rows] for idx, column in enumerate(columns)}
        table = pa.table(data)
        parquet_buffer = BytesIO()
        pq.write_table(table, parquet_buffer)
        parquet_buffer.seek(0)

        filename = f"{table_name}.parquet"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(
            parquet_buffer,
            media_type="application/x-parquet",
            headers=headers,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Error descargando Parquet: {exc}") from exc
