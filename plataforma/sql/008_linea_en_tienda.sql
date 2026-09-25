-- En que tienda se compra cada linea de la lista.
--
-- Lo pidio el dueno el 25 de septiembre de 2026: *"en la lista poder elegir en que
-- supermercado lo quiero comprar y hacer en una lista que tenga, sublistas
-- dependiendo de donde he puesto que voy a comprar ese producto, con el precio
-- final de la lista entera y de cada sublista"*.
--
-- Hasta hoy la aplicacion calculaba **donde sale mas barata la lista entera**
-- (`/api/listas/{id}/donde`) y no guardaba ninguna decision: cada vez que se abria
-- la pantalla volvia a proponer. Eso esta bien para mirar y no vale para comprar:
-- quien decide "el pan en DIA, que me pilla de camino" tiene que poder dejarlo
-- escrito, y que el total lo tenga en cuenta.
--
-- `cadena_elegida` a NULL es "todavia no lo he decidido", que no es lo mismo que
-- "lo compro donde sea": la pantalla tiene que distinguir las dos cosas, y el
-- total solo cuenta lo decidido mientras lo demas sale aparte como pendiente.

ALTER TABLE lista_linea ADD COLUMN IF NOT EXISTS cadena_elegida text;

-- Las cinco cadenas que hay. Se escribe aqui para que un `cadena_elegida` con una
-- errata ("mercadonna") no se guarde y no deje una linea que nunca aparece en
-- ninguna sublista. El dia que entre una sexta cadena -- Eroski y Ahorramas son
-- las candidatas de `docs/BACKLOG.md` -- se cambia aqui con una migracion nueva,
-- que es como se cambian las reglas del esquema en este proyecto.
ALTER TABLE lista_linea DROP CONSTRAINT IF EXISTS linea_en_tienda_conocida;
ALTER TABLE lista_linea ADD CONSTRAINT linea_en_tienda_conocida CHECK (
    cadena_elegida IS NULL
    OR cadena_elegida IN ('alcampo', 'aldi', 'carrefour', 'dia', 'mercadona'));

-- La lista se puede archivar (que es lo que hace el boton de borrar la lista
-- entera). `archivada_en` ya existia en `001_esquema.sql` y `listas_de` ya filtra
-- por el; lo que faltaba era la migracion que lo deja escrito y el endpoint.
--
-- Archivar y no borrar, por lo mismo que las lineas no se borran de verdad: borrar
-- una lista compartida le quita la compra a otra persona de un toque, y deshacerlo
-- no deberia depender de una copia de seguridad. Si de verdad hay que borrarla,
-- `003_mas_de_dos.sql` y la clave ajena en cascada ya se lo llevan todo cuando se
-- borra la persona.
CREATE INDEX IF NOT EXISTS lista_archivada ON lista(archivada_en) WHERE archivada_en IS NULL;
