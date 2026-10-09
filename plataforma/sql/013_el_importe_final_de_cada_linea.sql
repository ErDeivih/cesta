-- 013: el importe final de cada linea de una compra.
--
-- **Por que hace falta.** Hasta ahora `compra_linea` guardaba el precio **unitario**, y el total vivia solo en
-- `compra.total_cent`. Con eso, la igualdad «las lineas suman el total» no se puede comprobar sin recalcularla,
-- y recalcularla con el motor de hoy **no demuestra lo que se registro al cerrar**: el catalogo y las ofertas
-- cambian, y una compra de hace un mes se explicaria con los precios de hoy.
--
-- **Los registros antiguos quedan como desconocidos.** La columna entra NULL y **no se rellena**: reconstruirla
-- con los precios de hoy seria inventar lo que se pago. Quien lea una compra anterior vera NULL, que es la
-- verdad -- no se sabe.
--
-- **El importe es el final**: despues de ofertas y despues del reparto de centimos entre las lineas del mismo
-- grupo de compra. Su suma es, exactamente, `compra.total_cent`.
ALTER TABLE compra_linea ADD COLUMN IF NOT EXISTS importe_cent integer;

COMMENT ON COLUMN compra_linea.importe_cent IS
    'Importe final de la linea, tras ofertas y reparto de centimos. NULL en las compras anteriores a 013: desconocido, no reconstruido.';
