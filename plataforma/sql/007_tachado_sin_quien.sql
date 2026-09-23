-- Borrarse del todo, de verdad: `tachado_coherente` impedia darse de baja.
--
-- `lista_linea.tachado_por` es `uuid REFERENCES usuario(id) ON DELETE SET NULL`
-- (`001_esquema.sql:95`) y `tachado_coherente` pedia que hubiera "quien" **si y solo si**
-- habia "cuando" (`001_esquema.sql:100`). Las dos cosas juntas no pueden ser:
--
--   alguien se da de baja
--     -> PostgreSQL pone `tachado_por = NULL` y deja `tachado_en`, que es lo correcto
--        (la linea se tacho, y eso paso)
--     -> la fila incumple el CHECK
--     -> **el DELETE falla entero**
--
-- Medido el 23 de septiembre de 2026 con `plataforma/prueba_e2e.py`, que vacia la base
-- de prueba entre pasadas: `psycopg.errors.CheckViolation: new row for relation
-- "lista_linea" violates check constraint "tachado_coherente" ... UPDATE ONLY
-- "public"."lista_linea" SET "tachado_por" = NULL`.
--
-- Es el mismo caso que arreglo `005_borrarse_del_todo.sql` con `anadido_por`, y alli si
-- se vio: se paso de `RESTRICT` a `SET NULL`. Aqui el `SET NULL` ya estaba, pero el
-- CHECK lo dejaba sin efecto. En produccion eso es **un 500 al darse de baja** si esa
-- persona habia tachado algo en una lista que sobrevive -- compartida, o de casa.
--
-- El invariante que de verdad importa es el otro: **no puede haber "quien" sin
-- "cuando"**. Que haya "cuando" sin "quien" no es una incoherencia: es que quien lo tacho
-- ya no esta.
ALTER TABLE lista_linea DROP CONSTRAINT IF EXISTS tachado_coherente;
ALTER TABLE lista_linea ADD CONSTRAINT tachado_coherente CHECK (
    tachado_por IS NULL OR tachado_en IS NOT NULL);
