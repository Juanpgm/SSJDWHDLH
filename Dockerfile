# PostgreSQL 18 + PostGIS 3
# Usar como servicio custom en Railway en lugar del plugin Postgres estándar.
FROM postgres:18-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-18-postgis-3 \
        postgresql-18-postgis-3-scripts \
    && rm -rf /var/lib/apt/lists/*

# Script de inicialización: habilita PostGIS en la base de datos al arrancar
COPY docker/init-postgis.sh /docker-entrypoint-initdb.d/10_init-postgis.sh
RUN chmod +x /docker-entrypoint-initdb.d/10_init-postgis.sh
