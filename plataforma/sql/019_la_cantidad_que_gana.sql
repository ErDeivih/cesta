-- La hora del ultimo cambio de cantidad, para que no gane la que llega tarde.
--
-- **El defecto, medido.** `almacen.cambia_linea` escribia `cantidad = %s` con el comentario «gana el
-- ultimo, a proposito». *Y ese «ultimo» es **el ultimo que llega**, no **el mas nuevo***: dos personas
-- cambiando la cantidad de la misma linea sin cobertura se pisaban, y **ganaba la que llegaba despues
-- aunque su hora fuera anterior**. *O sea: el orden de los hechos se lo inventaba el servidor.*
--
-- **Y el tachado ya lo hacia bien** -- *tiene `tachado_en` y usa `LEAST(COALESCE(...))`* --, asi que la
-- cantidad solo necesitaba lo mismo: **una columna donde apuntar cuando se cambio.**
--
-- **Por que `GREATEST` y no `LEAST`, que es lo contrario del tachado.** *Y no es un descuido:*
--
--   - **Tachar** es «yo lo hice primero»: si los dos tachais, **gana el primero**, porque el hecho ya
--     ocurrio y deshacerlo seria quitarle la razon a quien la tuvo antes.
--   - **Cambiar la cantidad** es «este es el valor de ahora»: **gana el mas nuevo**, porque una cantidad
--     no es un hecho que ocurrio, es un estado que se decide.
--
-- *La misma linea de codigo, dos reglas opuestas, y cada una con su motivo escrito.*
--
-- **Y es aditiva**: la columna entra a NULL y **no se rellena hacia atras**. *Una linea que nunca cambio
-- de cantidad desde esta migracion tiene `NULL`, y eso significa «no consta»* -- *no «cambio en el
-- origen de los tiempos»*. Al comparar, `COALESCE(cantidad_en, 'epoch')` deja ganar a cualquier cambio
-- con hora, y **entre dos cambios sin hora gana el que llega** -- *que es el comportamiento viejo, y
-- ahora solo para el caso en que de verdad no hay nada con que ordenar.*
--
-- **La tabla es `lista_linea`, no `linea`.** *La primera version de esta migracion decia `linea`
-- y `arranca()` la paro con `UndefinedTable` -- que es la migracion haciendo su trabajo: no dejar
-- el esquema a medias.*
--
-- No toca `facylf-postgres`: esta es la base de Cesta.

ALTER TABLE lista_linea
    ADD COLUMN IF NOT EXISTS cantidad_en TIMESTAMPTZ;

COMMENT ON COLUMN lista_linea.cantidad_en IS
    'Hora del movil del ultimo cambio de cantidad. NULL = no consta desde la migracion 019. '
    'Gana el MAS NUEVO (GREATEST), al contrario que tachado_en, que guarda el PRIMERO (LEAST).';

-- **Y un indice no hace falta**: se consulta siempre por `linea.id`, que es la clave. *Anadir uno seria
-- coste sin lectura que lo aproveche.*
