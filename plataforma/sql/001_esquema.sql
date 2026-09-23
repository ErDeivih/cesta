-- Cesta: todo lo que escriben las personas.
--
-- Lo que se LEE (catalogo, precios, grupos) no esta aqui: vive en parquet y lo
-- consulta DuckDB sin copiarlo. Aqui solo hay cuentas, listas y favoritos: unos
-- pocos miles de filas con muchas escrituras a la vez, que es justo lo que
-- PostgreSQL hace bien y DuckDB hace mal.
--
-- No hay integridad referencial contra el catalogo a proposito: `grupo_id` es
-- una referencia a algo que vive en otro sitio. Si manana se rehace el
-- emparejador y cambian los identificadores, las listas se migran con una
-- consulta en vez de reconstruir una base de datos.

-- Antes aqui se creaba la extension `pgcrypto`, y no hacia ninguna falta: lo
-- unico que se usaba de ella era `gen_random_uuid()`, que **es parte del nucleo
-- de PostgreSQL desde la version 13**.
--
-- Se vio al levantar la plataforma por primera vez, el 18 de septiembre de 2026,
-- contra un PostgreSQL 16 sin extensiones: el arranque fallaba entero con
-- "extension pgcrypto is not available". La imagen oficial de Docker si la trae,
-- asi que nunca se habria notado ahi, pero era una dependencia de despliegue
-- que no aportaba nada: ataba la base de datos a una imagen concreta a cambio de
-- una funcion que ya viene puesta.
--
-- La version minima se comprueba en `almacen.migra()`, que avisa con una frase
-- entendible en vez de dejar reventar una consulta mas adelante.

-- --------------------------------------------------------------- personas ---

CREATE TABLE IF NOT EXISTS usuario (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario     text NOT NULL UNIQUE,
    nombre      text NOT NULL,
    clave_hash  text NOT NULL,              -- Argon2id
    creado_en   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT usuario_minusculas CHECK (usuario = lower(usuario)),
    CONSTRAINT usuario_no_vacio   CHECK (length(trim(usuario)) >= 3)
);

CREATE TABLE IF NOT EXISTS sesion (
    token       text PRIMARY KEY,           -- hash del token, nunca el token
    usuario_id  uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    dispositivo text,
    creada_en   timestamptz NOT NULL DEFAULT now(),
    expira_en   timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS sesion_por_usuario ON sesion(usuario_id);
CREATE INDEX IF NOT EXISTS sesion_por_caducidad ON sesion(expira_en);

CREATE TABLE IF NOT EXISTS preferencia (
    usuario_id  uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    clave       text NOT NULL,
    valor       jsonb NOT NULL,
    PRIMARY KEY (usuario_id, clave)
);

-- ----------------------------------------------------------------- listas ---

CREATE TABLE IF NOT EXISTS lista (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre      text NOT NULL,
    dueno_id    uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    es_de_casa  boolean NOT NULL DEFAULT false,
    creada_en   timestamptz NOT NULL DEFAULT now(),
    archivada_en timestamptz
);
CREATE INDEX IF NOT EXISTS lista_por_dueno ON lista(dueno_id);
-- Aqui habia un indice unico de "una sola lista de casa en todo el sistema"
-- (`lista_de_casa_unica`, sobre `es_de_casa` a secas). **Ya no se crea, y el motivo
-- importa**: `almacen.migra()` aplica TODOS los ficheros .sql **en cada arranque**, y
-- `003_mas_de_dos.sql` borra ese indice porque con mas de una persona cada una quiere la
-- suya. Con las dos cosas, el segundo arranque lo resucitaba:
--
--     psycopg.errors.UniqueViolation: could not create unique index "lista_de_casa_unica"
--     DETAIL: Key (es_de_casa)=(t) is duplicated.
--
-- O sea que **la API no arrancaba** en cuanto habia dos listas de casa (medido el 23 de
-- septiembre de 2026 en `plataforma/prueba_e2e.py`), y ese es el estado normal de esta
-- aplicacion: una lista de casa por persona. El indice bueno es el de `003`, por dueno.
-- Un fichero viejo que se reaplica no puede contradecir a uno nuevo que lo corrige.

CREATE TABLE IF NOT EXISTS lista_acceso (
    lista_id     uuid NOT NULL REFERENCES lista(id) ON DELETE CASCADE,
    usuario_id   uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    papel        text NOT NULL CHECK (papel IN ('dueno', 'escribe', 'mira')),
    invitado_por uuid REFERENCES usuario(id) ON DELETE SET NULL,
    invitado_en  timestamptz NOT NULL DEFAULT now(),
    aceptado_en  timestamptz,
    PRIMARY KEY (lista_id, usuario_id)
);
CREATE INDEX IF NOT EXISTS acceso_por_usuario ON lista_acceso(usuario_id);

-- El identificador lo genera el MOVIL, no la base de datos: asi se puede anadir
-- un producto sin cobertura y subirlo despues con la identidad con la que
-- nacio. Si se sube dos veces, el ON CONFLICT lo reconoce y no lo duplica.
CREATE TABLE IF NOT EXISTS lista_linea (
    id           uuid PRIMARY KEY,
    lista_id     uuid NOT NULL REFERENCES lista(id) ON DELETE CASCADE,
    grupo_id     bigint,
    producto_id  text,                      -- solo si se fijo una cadena a mano
    nombre_visto text NOT NULL,             -- como se llamaba al anadirlo
    cantidad     integer NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    nota         text,
    anadido_por  uuid NOT NULL REFERENCES usuario(id) ON DELETE RESTRICT,
    anadido_en   timestamptz NOT NULL DEFAULT now(),
    tachado_por  uuid REFERENCES usuario(id) ON DELETE SET NULL,
    tachado_en   timestamptz,
    borrado_en   timestamptz,               -- no se borra de verdad: ver abajo
    tocado_en    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT linea_con_destino CHECK (grupo_id IS NOT NULL OR producto_id IS NOT NULL),
    CONSTRAINT tachado_coherente CHECK (
        (tachado_por IS NULL) = (tachado_en IS NULL))
);
CREATE INDEX IF NOT EXISTS linea_por_lista ON lista_linea(lista_id) WHERE borrado_en IS NULL;

-- Por que no se borra de verdad:
--   1. Si dos moviles borran y anaden a la vez, una fila borrada reaparece
--      cuando el otro sincroniza. Con una marca, no.
--   2. Deshacer. Borrar media lista sin querer en el pasillo del supermercado
--      tiene que ser reversible sin una llamada de telefono.
-- Se limpian de verdad a los 30 dias (ver 'limpiar_lineas_borradas').

-- -------------------------------------------------------------- favoritos ---

CREATE TABLE IF NOT EXISTS favorito (
    usuario_id  uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    grupo_id    bigint,
    producto_id text,
    anadido_en  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT favorito_con_destino CHECK (grupo_id IS NOT NULL OR producto_id IS NOT NULL)
);
CREATE UNIQUE INDEX IF NOT EXISTS favorito_unico_grupo
    ON favorito(usuario_id, grupo_id) WHERE grupo_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS favorito_unico_producto
    ON favorito(usuario_id, producto_id) WHERE producto_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS alerta (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id  uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    grupo_id    bigint NOT NULL,
    tipo        text NOT NULL CHECK (tipo IN ('baja_de', 'minimo_90d', 'cualquier_bajada')),
    umbral_cent integer,
    creada_en   timestamptz NOT NULL DEFAULT now(),
    vista_en    timestamptz
);
CREATE INDEX IF NOT EXISTS alerta_por_usuario ON alerta(usuario_id);

-- ------------------------------------------------------------ mantenimiento --

CREATE OR REPLACE FUNCTION limpiar_lineas_borradas(dias integer DEFAULT 30)
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE borradas integer;
BEGIN
    DELETE FROM lista_linea
     WHERE borrado_en IS NOT NULL
       AND borrado_en < now() - (dias || ' days')::interval;
    GET DIAGNOSTICS borradas = ROW_COUNT;
    RETURN borradas;
END $$;

CREATE OR REPLACE FUNCTION limpiar_sesiones_caducadas()
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE borradas integer;
BEGIN
    DELETE FROM sesion WHERE expira_en < now();
    GET DIAGNOSTICS borradas = ROW_COUNT;
    RETURN borradas;
END $$;
