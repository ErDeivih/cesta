-- *** EL SELLO DEL CIERRE: PARA QUE UN REINTENTO NO CREE OTRA COMPRA. ***
--
-- *Un cierre puede reintentarse -- se pulsa dos veces, se corta la red y el navegador lo repite, dos
-- pestanas cierran a la vez -- y hasta hoy cada intento que llegaba creaba una compra.* *El dinero
-- quedaba contado dos veces en el historico y no habia forma de saber cual era la buena.*
--
-- *El sello es el que ya viaja en la cotizacion: identifica **que** se cerro (lineas, cantidades,
-- tiendas, precios y version del catalogo).* *Dos intentos del mismo cierre traen el mismo sello, y el
-- segundo devuelve la compra del primero en vez de inventar otra.*
--
-- *Se admite NULL: una compra vieja, o un cierre sin revision, no tiene sello y no participa.* *Por eso
-- el indice es **parcial**: solo protege las que si lo tienen.*

ALTER TABLE compra ADD COLUMN IF NOT EXISTS sello text;

-- *Un sello, una compra por lista.* *El indice unico es la garantia, no la comprobacion previa: dos
-- peticiones simultaneas pueden pasar las dos por el `SELECT` y solo una pasara por el `INSERT`.*
CREATE UNIQUE INDEX IF NOT EXISTS compra_sello_unico
    ON compra (lista_id, sello)
 WHERE sello IS NOT NULL;
