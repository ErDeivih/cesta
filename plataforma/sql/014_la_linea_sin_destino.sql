-- 014: una linea de la lista puede no tener destino todavia.
--
-- **Por que hace falta.** Hasta ahora `linea_con_destino` exigia grupo o producto, y con razon: una
-- linea sin destino no se puede comparar con nada, y sin la restriccion una linea vacia entraba en la
-- base y reventaba mas tarde, lejos de quien la escribio.
--
-- **Pero eso convertia en imposible apuntar «papel de cocina» o «lo que sea del mercado»**, que es la
-- mitad de una lista de la compra de verdad. La restriccion protegia la comparacion y prohibia la
-- lista: quien no encontraba el producto en el catalogo no podia apuntarlo, y acababa apuntandolo en
-- otro sitio.
--
-- **Lo que la sustituye, y por que es mas debil a proposito.** Se sigue exigiendo **el nombre**: asi la
-- linea existe, se lee en la pantalla y **se puede identificar despues**, que es el vinculo posterior
-- explicito. Lo que ya no se exige es el destino **en el momento de apuntarla**.
--
-- **Lo que NO cambia, y es la parte que importa.** Una linea sin destino:
--   * se presenta como **«Pendiente de identificar»**, no como un producto;
--   * **no entra en ninguna comparacion de precios ni de nutricion**;
--   * y **no se le inventa precio, ni importe, ni equivalencia**: su `precio_cent` y su
--     `importe_cent` se quedan NULL, que es la verdad -- no se sabe.
-- Identificarla es un acto explicito y posterior; hasta entonces la lista la enseña y los totales la
-- dejan fuera, que es distinto de contarla como cero.
--
-- **Los registros que ya existen no cambian**: todos tienen destino, asi que siguen cumpliendo la
-- restriccion nueva.
--
-- **`favorito` se queda como esta.** Un favorito es, por definicion, un producto del catalogo: no hay
-- nada que apuntar «a medias», y su restriccion no estorba a nadie. Cambiarla por simetria seria
-- quitar una red sin que nadie la haya pedido.
ALTER TABLE lista_linea DROP CONSTRAINT IF EXISTS linea_con_destino;

-- **La columna se llama `nombre_visto`, no `nombre`.** La API la llama `nombre` en su modelo
-- (`NuevaLinea`) y el almacen la guarda como `nombre_visto`, que es mas exacto: es **lo que se vio
-- escrito**, no un nombre de producto. La primera version de esta migracion uso el nombre de la API
-- y `arranca()` fallaba con `UndefinedColumn` -- sin aplicar nada, porque las migraciones van en
-- transaccion: `linea_con_destino` seguia puesta y la base quedo intacta.
-- **Repetible, y esto no es un detalle.** La primera version solo tenia el `ADD`, y el SEGUNDO
-- arranque del almacen fallaba con `DuplicateObject: constraint "linea_con_nombre" already exists`
-- -- o sea que **reiniciar la API dos veces la mataba**. PostgreSQL no tiene `ADD CONSTRAINT IF NOT
-- EXISTS`, asi que el idioma es quitarla y volver a ponerla; el `DROP` de arriba ya es `IF EXISTS`
-- por el mismo motivo. `tests/test_g02_texto_libre.py` arranca el almacen **una vez por modulo**, y
-- fue lo que lo cazo: con un arranque por prueba el fallo era invisible.
ALTER TABLE lista_linea DROP CONSTRAINT IF EXISTS linea_con_nombre;

ALTER TABLE lista_linea
    ADD CONSTRAINT linea_con_nombre CHECK (length(btrim(nombre_visto)) > 0);

COMMENT ON CONSTRAINT linea_con_nombre ON lista_linea IS
    'La linea necesita nombre, no destino. Sin destino queda «pendiente de identificar»: se lee, no se compara y no se le inventa precio.';
