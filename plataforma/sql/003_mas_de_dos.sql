-- Cesta: lo que hace falta cuando la app deja de ser de dos personas.
--
-- Hasta aqui el esquema asumia a David y su madre. Estas tres cosas son baratas
-- ahora y caras despues, porque la primera se manifiesta como un error de clave
-- duplicada que no entiende nadie, justo el dia que entra la tercera persona.

-- 1. La lista de casa era UNICA EN TODA LA BASE DE DATOS.
--    Con dos personas que viven juntas tenia sentido. Con amigos, cada uno
--    quiere la suya, y el segundo que lo intentara se llevaria un error.
DROP INDEX IF EXISTS lista_de_casa_unica;
CREATE UNIQUE INDEX IF NOT EXISTS lista_de_casa_por_dueno
    ON lista(dueno_id) WHERE es_de_casa;

-- 2. Un tope de invitaciones vivas por lista.
--    No es un ataque: es que un enlace reenviado sin querer mete en la lista a
--    gente que no sabes que esta. Se limita en la API, y esta vista es para
--    poder comprobarlo de un vistazo.
CREATE OR REPLACE VIEW invitaciones_vivas AS
    SELECT lista_id, count(*) AS vivas
      FROM invitacion
     WHERE revocada_en IS NULL AND expira_en > now() AND usos < usos_max
     GROUP BY lista_id;

-- 3. Poder borrarse.
--    Si un amigo pide irse, esto se lleva sus listas propias, sus favoritos,
--    sus sesiones y sus accesos, por las claves ajenas que ya existen. Lo que
--    NO se lleva son las lineas que anadio a listas de otros: esas se quedan,
--    porque borrarlas vaciaria la lista de la compra de otra persona.
CREATE OR REPLACE FUNCTION borrar_usuario(quien uuid)
RETURNS TABLE(listas_borradas integer, lineas_conservadas integer)
LANGUAGE plpgsql AS $$
DECLARE l integer; n integer;
BEGIN
    SELECT count(*) INTO n FROM lista_linea li
      JOIN lista x ON x.id = li.lista_id
     WHERE li.anadido_por = quien AND x.dueno_id <> quien;
    SELECT count(*) INTO l FROM lista WHERE dueno_id = quien;
    -- Las lineas en listas ajenas pierden el autor pero no desaparecen.
    UPDATE lista_linea SET anadido_por = NULL
     WHERE anadido_por = quien
       AND lista_id IN (SELECT id FROM lista WHERE dueno_id <> quien);
    DELETE FROM usuario WHERE id = quien;
    RETURN QUERY SELECT l, n;
END $$;

-- `anadido_por` era NOT NULL porque con dos personas nadie se borra.
ALTER TABLE lista_linea ALTER COLUMN anadido_por DROP NOT NULL;
