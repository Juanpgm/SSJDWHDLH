import csv
import re
from io import BytesIO, StringIO
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pyarrow as pa
import pyarrow.parquet as pq

from api.core.config import settings
from api.core.database import db_cursor, fetch_table_rows, rows_to_dicts, table_exists

APP_TITLE = settings.app_title
APP_VERSION = settings.app_version
TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=(
        "API para explorar tablas y datos de PostgreSQL/PostGIS. "
        "Swagger disponible en /docs y OpenAPI en /openapi.json."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def assert_safe_table_name(table_name: str) -> None:
    if not TABLE_NAME_PATTERN.fullmatch(table_name):
        raise HTTPException(status_code=400, detail="Nombre de tabla no valido")


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
    return {"status": "ok", "version": APP_VERSION}


@app.get("/health/db", tags=["health"])
def db_health() -> dict[str, Any]:
    try:
        with db_cursor() as cur:
            cur.execute("SELECT current_database() AS db, now() AS ts")
            row = cur.fetchone()
            return {"status": "ok", "database": row[0], "timestamp": row[1]}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DB no disponible: {exc}") from exc


@app.get("/tables", tags=["tables"])
def list_tables() -> dict[str, Any]:
    try:
        rows = fetch_tables()
        return {"count": len(rows), "tables": rows}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Error listando tablas: {exc}") from exc


@app.get("/tables/{table_name}/data", tags=["data"])
def get_table_data(
    table_name: str,
    id: str | None = Query(default=None, description="Valor del ID para filtrar"),
    id_column: str = Query(default="id", description="Nombre de columna ID"),
    limit: int = Query(default=100, ge=1),
) -> dict[str, Any]:
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
            return {"table": table_name, "count": len(rows), "rows": rows}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Error consultando datos: {exc}") from exc


@app.get("/tables/{table_name}/download/csv", tags=["data"])
def download_table_csv(
    table_name: str,
    limit: int | None = Query(default=None, ge=1, description="Limite opcional de filas"),
) -> StreamingResponse:
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
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Error descargando CSV: {exc}") from exc


@app.get("/tables/{table_name}/download/parquet", tags=["data"])
def download_table_parquet(
    table_name: str,
    limit: int | None = Query(default=None, ge=1, description="Limite opcional de filas"),
) -> StreamingResponse:
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
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Error descargando Parquet: {exc}") from exc


from api.routers import auth, users

app.include_router(auth.router)
app.include_router(users.router)
