-- ============================================================
-- SYJDWH — Migración 001: Tabla homicidios
-- ============================================================

-- NOTA: La columna geom se define inicialmente como text (WKT).
-- La migración 002_enable_postgis.sql la convierte a geometry(Point,4326)
-- una vez que el servicio PostGIS esté activo en Railway.

-- ============================================================
-- SEQUENCES
-- ============================================================

CREATE SEQUENCE IF NOT EXISTS public.no
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

CREATE SEQUENCE IF NOT EXISTS public.identificador
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

-- ============================================================
-- TABLE: public.homicidios
-- ============================================================

CREATE TABLE IF NOT EXISTS public.homicidios
(
    spoa                            text    COLLATE pg_catalog."default",
    fechao                          integer,
    semana                          double precision,
    spoa_completo                   text    COLLATE pg_catalog."default",
    manera_muerte                   text    COLLATE pg_catalog."default",
    nombre                          text    COLLATE pg_catalog."default",
    apellido1                       text    COLLATE pg_catalog."default",
    apellido2                       text    COLLATE pg_catalog."default",
    nacionalidad                    text    COLLATE pg_catalog."default",
    otra_nacionalidad               text    COLLATE pg_catalog."default",
    tipo_identificacion             text    COLLATE pg_catalog."default",
    num_identificacion              text    COLLATE pg_catalog."default",
    ocupacion                       text    COLLATE pg_catalog."default",
    sexo                            text    COLLATE pg_catalog."default",
    genero                          text    COLLATE pg_catalog."default",
    orientacion                     text    COLLATE pg_catalog."default",
    edad                            integer,
    etnia                           text    COLLATE pg_catalog."default",
    estado_civil                    text    COLLATE pg_catalog."default",
    escolaridad                     text    COLLATE pg_catalog."default",
    direccion                       text    COLLATE pg_catalog."default",
    barrio                          text    COLLATE pg_catalog."default",
    sector                          text    COLLATE pg_catalog."default",
    tipo_de_arma                    text    COLLATE pg_catalog."default",
    cuadrante                       text    COLLATE pg_catalog."default",
    fechah                          date,
    horah                           time without time zone,
    diasem                          text    COLLATE pg_catalog."default",
    nom_lugar_delictivo             text    COLLATE pg_catalog."default",
    lugar_hechos                    text    COLLATE pg_catalog."default",
    resumen                         text    COLLATE pg_catalog."default",
    tipo_violencia                  text    COLLATE pg_catalog."default",
    categoria_movil                 text    COLLATE pg_catalog."default",
    categoria_movil_recategorizada  text    COLLATE pg_catalog."default",
    subcategoria_movil              text    COLLATE pg_catalog."default",
    tipo_agresor                    text    COLLATE pg_catalog."default",
    fec_especial                    text    COLLATE pg_catalog."default",
    feminicidios                    text    COLLATE pg_catalog."default",
    procedimientofuerzapublica      text    COLLATE pg_catalog."default",
    poblacion_lgbtq                 text    COLLATE pg_catalog."default",
    licor                           integer,
    drogas                          integer,
    bandas                          integer,
    lgtbi                           integer,
    pandillas                       integer,
    habitantescalle                 integer,
    barras                          integer,
    direcion_de_residencia          text    COLLATE pg_catalog."default",
    barrio_residencia               text    COLLATE pg_catalog."default",
    comuna_residencia               text    COLLATE pg_catalog."default",
    clasificacion                   text    COLLATE pg_catalog."default",
    multiples                       text    COLLATE pg_catalog."default",
    horam                           time without time zone,
    fecham                          date,
    horai                           time without time zone,
    fechai                          date,
    inspeccion                      text    COLLATE pg_catalog."default",
    levantamiento                   text    COLLATE pg_catalog."default",
    idcombar                        text    COLLATE pg_catalog."default",
    comuna                          text    COLLATE pg_catalog."default",
    com_hecho                       text    COLLATE pg_catalog."default",
    barrioplaneacion                text    COLLATE pg_catalog."default",
    estratoplaneacion               integer,
    x                               double precision,
    y                               double precision,
    semanaexcel                     integer,
    semanalundom                    integer,
    semanaconsecutivoexcel          integer,
    semanaconsecutivolundom         integer,
    finsemanaconsecutivo            integer,
    jornada                         text    COLLATE pg_catalog."default",
    jornadarh8                      text    COLLATE pg_catalog."default",
    est28xrangohora                 integer,
    fh8                             text    COLLATE pg_catalog."default",
    est32xdianoche                  integer,
    diasanio                        integer,
    agresor_en_moto                 text    COLLATE pg_catalog."default",
    anotaciones                     text    COLLATE pg_catalog."default",
    antecedentes                    text    COLLATE pg_catalog."default",
    comparendos                     text    COLLATE pg_catalog."default",
    geom                            text    COLLATE pg_catalog."default", -- WKT; migración 002 lo convierte a geometry(Point,4326)
    coordenadas                     text    COLLATE pg_catalog."default",
    movil                           text    COLLATE pg_catalog."default",
    no                              integer NOT NULL DEFAULT nextval('no'::regclass),
    identificador                   integer NOT NULL DEFAULT nextval('identificador'::regclass),
    sicariato                       text    COLLATE pg_catalog."default",
    relato                          text    COLLATE pg_catalog."default",
    desc_habcalle                   text    COLLATE pg_catalog."default",
    desc_drogas                     text    COLLATE pg_catalog."default"
);
