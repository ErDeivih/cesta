-- 5. Darse de baja funciona aunque hayas escrito en tu propia lista.
--
-- `lista_linea.anadido_por` era la **unica** clave ajena de todo el esquema con
-- `ON DELETE RESTRICT`. Todas las demas que apuntan a `usuario` son `CASCADE`
-- (`sesion`, `acceso`, `preferencia`, `favorito`, `visita`, `lista.dueno_id`,
-- `invitacion.creada_por`), y `tachado_por` es `SET NULL`. Se escribio asi cuando
-- esto eran dos personas y nadie se borraba; el comentario de `003` lo dice sin
-- rodeos: "`anadido_por` era NOT NULL porque con dos personas nadie se borra".
--
-- Con eso, `DELETE /api/yo` respondia **500** en cuanto la persona habia anadido
-- una linea a una lista suya. `borrar_usuario` anulaba `anadido_por` solo en las
-- listas **ajenas** (003, linea 41), contando con que el `CASCADE` de
-- `lista.dueno_id` se llevaria las propias -- y PostgreSQL comprueba una clave
-- `RESTRICT` **antes** de que el `CASCADE` actue. Es la diferencia entre
-- `RESTRICT` y `NO ACTION`: `RESTRICT` no espera al final de la sentencia, asi
-- que revienta aunque las filas que molestan esten a punto de desaparecer.
--
-- Reproducido contra la API viva antes de arreglarlo: alta, lista propia, una
-- linea dentro, `DELETE /api/yo` -> 500.
--
-- `SET NULL` dice lo mismo que ya dice `tachado_por`, que es lo que se quiere
-- decir: **la linea se queda y se pierde quien la puso**. Borrarla vaciaria la
-- lista de la compra de otra persona, que no ha pedido nada.
--
-- `DROP ... IF EXISTS` + `ADD` y no un `ALTER CONSTRAINT`: en Postgres, cambiar
-- la accion de borrado de una clave ajena no se puede hacer de una vez.
ALTER TABLE lista_linea DROP CONSTRAINT IF EXISTS lista_linea_anadido_por_fkey;
ALTER TABLE lista_linea ADD CONSTRAINT lista_linea_anadido_por_fkey
      FOREIGN KEY (anadido_por) REFERENCES usuario(id) ON DELETE SET NULL;

-- La funcion se puede quedar como esta: anular el autor a mano sigue siendo
-- correcto, y con la clave ya no importa el orden. Se reescribe solo para dejar
-- dicho por que ya no depende de que el CASCADE llegue antes.
CREATE OR REPLACE FUNCTION borrar_usuario(quien uuid)
RETURNS TABLE(listas_borradas integer, lineas_conservadas integer)
LANGUAGE plpgsql AS $$
DECLARE l integer; n integer;
BEGIN
    SELECT count(*) INTO n FROM lista_linea li
      JOIN lista x ON x.id = li.lista_id
     WHERE li.anadido_por = quien AND x.dueno_id <> quien;
    SELECT count(*) INTO l FROM lista WHERE dueno_id = quien;
    -- Las lineas en listas ajenas pierden el autor pero no desaparecen. Las de
    -- las listas propias se van con la lista: `lista.dueno_id` es CASCADE. Las
    -- dos cosas valen con la clave ya en SET NULL; se hace aqui igual porque el
    -- recuento `lineas_conservadas` cuenta exactamente esto.
    UPDATE lista_linea SET anadido_por = NULL
     WHERE anadido_por = quien
       AND lista_id IN (SELECT id FROM lista WHERE dueno_id <> quien);
    DELETE FROM usuario WHERE id = quien;
    RETURN QUERY SELECT l, n;
END $$;
