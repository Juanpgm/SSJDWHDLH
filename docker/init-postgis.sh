#!/bin/bash
set -e

# Se ejecuta automáticamente al inicializar el contenedor por primera vez.
# Habilita la extensión PostGIS en la base de datos de destino.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;
    CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
    CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
    SELECT PostGIS_Full_Version();
EOSQL
