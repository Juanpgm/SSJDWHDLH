# PostgreSQL 16 + PostGIS 3.5 — imagen oficial con PostGIS preinstalado
FROM postgis/postgis:16-3.5

# Script de inicialización: habilita PostGIS en la base de datos al arrancar
COPY docker/init-postgis.sh /docker-entrypoint-initdb.d/10_init-postgis.sh
RUN chmod +x /docker-entrypoint-initdb.d/10_init-postgis.sh
