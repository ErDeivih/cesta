# Precio

La cifra que decide la compra: precio actual, precio anterior y €/kg, con la bajada o la subida dichas
en dinero y no solo en color.

## Cuándo

Siempre que se enseñe el precio de un producto. En una tarjeta va la variante `precio` (20 px); en la
ficha del producto, `precio-grande` (30 px). En una fila de comparación va `precio-fila` (17 px).

## Anatomía

- **Precio actual** — `precio-*` + clase `cifra`, en `tinta`. Es lo más grande de la tarjeta.
- **Movimiento** — si el precio ha cambiado, una línea en `precio-baja` o `precio-sube` con su flecha
  y su cifra: «−0,40 €», «+0,20 €». La flecha y la palabra son obligatorias: el color solo no basta
  (la separación luminosa entre `bien` y `error` es de 1,02:1 en claro).
- **€/kg** — en `precio-unidad` (`tinta-tenue`), 13 px. Es la cifra honesta: compara formatos distintos.
- **Precio anterior** — en `precio-antes`, tachado con `text-decoration: line-through` y 1 px de
  grosor. Nunca se pinta del mismo color que el actual.
- **Sin dato** — una raya «—» en `tinta-tenue` y la frase que diga por qué («sin captura de esta
  cadena»). Un cero no es un precio.

## El consumidor pone

Los importes ya formados (el sistema no formatea), la unidad canónica (`kg`, `l`, `ud`) y, si existe,
el movimiento con su signo. Si el dato de hoy falta, `importe = null` y la pieza pinta la raya.

## Sí / no

- Sí: `1,99 €` con su `1,99 €/kg` debajo; en una tarjeta pequeña, el €/kg puede ir al lado en 13 px.
- Sí: «antes 2,39 €» tachado, siempre que el precio anterior sea real; si es una oferta condicionada,
  se dice en la línea de al lado, no aquí.
- No: la cifra en Fraunces (las cifras tienen que alinearse en columna).
- No: `1,99` sin unidad ni `1.99` con punto. Coma decimal y espacio antes del `€`.
- No: un precio sin su €/kg cuando el producto se compara con otro formato.
