-- ============================================================
-- SYJDWH — Migración 002: Habilitar PostGIS y actualizar geom
-- Requiere que el servidor tenga instalado postgresql-XX-postgis-3
-- ============================================================

-- 1. Extensiones PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- 2. Verificar instalación
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
        RAISE EXCEPTION 'PostGIS no se pudo instalar. Verifique que el servidor tiene postgresql-postgis-3.';
    END IF;
    RAISE NOTICE 'PostGIS % instalado correctamente.', PostGIS_Lib_Version();
END;
$$;

-- 3. Migrar columna geom: TEXT (WKT) → GEOMETRY(Point, 4326)
--    La tabla ya existe desde la migración 001.
--    Si la columna tiene datos WKT, se convierten con ST_GeomFromText.
ALTER TABLE public.homicidios
    ALTER COLUMN geom TYPE geometry(Point, 4326)
    USING CASE
        WHEN geom IS NOT NULL AND geom <> ''
            THEN ST_SetSRID(ST_GeomFromText(geom), 4326)
        ELSE NULL
    END;

-- 4. Índice espacial GIST para consultas geoespaciales
CREATE INDEX IF NOT EXISTS idx_homicidios_geom
    ON public.homicidios USING GIST (geom);

-- 5. Comentario en columna
COMMENT ON COLUMN public.homicidios.geom
    IS 'Punto geográfico WGS84 (EPSG:4326). Generado desde columnas x, y.';
