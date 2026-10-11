-- 015: que se pidio y que se compro, las dos cosas, en la linea de una compra.
--
-- **Que fallaba, y medido.** Con una sustitucion aceptada -- A pedido, B aceptado en la tienda T -- el
-- cierre guardaba `producto_id` = A y el precio de A, mientras la estimacion cobraba B con **su**
-- precio y **su** oferta. Reproducido el 13 de octubre de 2026 con el escenario del encargo (A de
-- 300 c pedido, B de 250 c con 3x2 aceptado, tres unidades):
--
--     estimacion    producto efectivo B, identidad «confirmada», total  500 centimos
--     cierre        precio_cent 300, coste_cent 900, producto_id A
--     discrepancia  400 centimos
--
-- *No es un redondeo: el historico apuntaba a un producto que nadie compro, a un precio que nadie pago,
-- sin la oferta que si se aplico.* **Y una compra no se recalcula: lo que se guarda mal miente para
-- siempre.**
--
-- **Por que dos columnas y no una.** `producto_id` pasa a significar **lo que se compro** -- que es lo
-- que su nombre dice -- y `producto_pedido_id` guarda **lo que se pidio** cuando no son el mismo.
-- Guardar solo uno obliga a elegir cual se pierde: con el pedido, el historico no dice que se compro;
-- con el efectivo, no se puede explicar por que. La 012 ya argumento esto mismo para `lista_linea`
-- --«confirmar una sustitucion [es] aceptar **ese** producto»-- y aqui vale igual.
--
-- **Y hace falta en la compra, no solo en la linea de la lista**, porque la linea de la lista se poda:
-- `limpiar_lineas_borradas` se lleva las archivadas a los 30 dias. *Una compra de hace un año tiene que
-- poder explicarse sola, sin depender de una fila que ya no esta.*
--
-- **Los registros antiguos quedan como desconocidos.** La columna entra NULL y **no se rellena**: no
-- consta que se pidiera otra cosa, y suponer que coinciden seria inventar. NULL significa «no consta»,
-- igual que en `importe_cent` de la 013 y que en `autorizado_producto` de la 012.
--
-- `IF NOT EXISTS` para que sea repetible: la aplican los contenedores al arrancar.

ALTER TABLE compra_linea ADD COLUMN IF NOT EXISTS producto_pedido_id text;

COMMENT ON COLUMN compra_linea.producto_pedido_id IS
    'El producto que la linea pedia, cuando no es el mismo que se compro. NULL en las historicas: no consta.';
