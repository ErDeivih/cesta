-- «He terminado la compra»: lo que iba en el carro se guarda como una compra y sale de la lista.
--
-- Por que no basta con borrar las lineas del carro. La lista se vacia al terminar la compra, y
-- el historial (`almacen.historial_de`) **ya cuenta las lineas borradas**, asi que el mosaico de
-- «lo de siempre» sigue funcionando sin nada de esto: eso se decidio el 23 de septiembre de 2026
-- y esta escrito en su docstring. Lo que contando lineas no se puede saber es **cuanto costo la
-- compra**: el precio vive en gold, y gold se reescribe cada dia. Una compra sin su precio no se
-- puede volver a mirar, y la lista de la compra que no deja rastro de lo que costo es una lista
-- que hay que rehacer cada semana desde cero.
--
-- Por que `precio_cent` puede ser NULL. Una linea puede no tener precio hoy: el producto puede
-- no estar en el catalogo, o puede ser una de las lineas que apuntan a otro producto (el caso
-- que cierra `catalogo.lineas_movidas`). Se guarda la linea con su precio en NULL **y se cuenta
-- aparte** (`compra.sin_precio`): tirarla seria borrar de la compra algo que si se compro, y
-- contarla como cero seria mentir en el total.
--
-- Por que `cadena` y no `cadena_elegida`. Es la cadena **de la que se cogio el precio**, que es
-- la que se decidio en la lista si se decidio, y si no la mas barata de hoy. Guardar
-- `cadena_elegida` dejaria compras con la cadena vacia y un precio que no es de nadie.

CREATE TABLE IF NOT EXISTS compra (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lista_id    uuid NOT NULL REFERENCES lista(id) ON DELETE CASCADE,
    usuario_id  uuid REFERENCES usuario(id) ON DELETE SET NULL,
    cerrada_en  timestamptz NOT NULL DEFAULT now(),
    lineas      integer NOT NULL,
    sin_precio  integer NOT NULL DEFAULT 0,
    total_cent  integer NOT NULL DEFAULT 0,
    CONSTRAINT compra_total_coherente CHECK (total_cent >= 0)
);

CREATE INDEX IF NOT EXISTS compra_por_lista ON compra(lista_id, cerrada_en DESC);

CREATE TABLE IF NOT EXISTS compra_linea (
    compra_id   uuid NOT NULL REFERENCES compra(id) ON DELETE CASCADE,
    linea_id    uuid NOT NULL,
    grupo_id    bigint,
    producto_id text,
    nombre      text NOT NULL,
    cantidad    integer NOT NULL CHECK (cantidad > 0),
    cadena      text,
    precio_cent integer,
    PRIMARY KEY (compra_id, linea_id)
);

-- `usuario_id` va con ON DELETE SET NULL y no CASCADE, por lo mismo que en `lista_linea`:
-- darse de baja no puede borrarle la compra a la otra persona de una lista compartida. La
-- compra es de la lista; quien la cerro es un dato, no el dueno.
