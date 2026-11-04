# FilaComparacion

Una cadena en una línea: qué cadena, qué producto, cuánto cuesta, cuánto cuesta el kilo y si es la más
barata.

## Cuándo

En la comparación por cadena de un grupo comparable y en el resumen de la cesta. Es la pieza que
contesta la pregunta de la app: **¿dónde me sale mejor?**

## Anatomía

- **La fila entera es el objetivo** — un `<a>` (o un `<button>` si la acción no es navegar) con
  `min-height: 44px`. Nunca un `div` con `onclick`: con el teclado no se llega y con el pulgar tampoco.
- **Quién** — nombre de la cadena en `cuerpo-fuerte` (16/600) y, debajo, el producto en `etiqueta` con
  `tinta-suave`, recortado con puntos suspensivos: el nombre completo no cabe a 390 px y no hace falta.
- **Cifras, a la derecha** — precio en `precio-fila` (17/600) con `cifra`, y debajo el €/kg en
  `etiqueta` `tinta-tenue`.
- **La más barata** — fondo `lavado-verde`, texto del veredicto en `verde` con su marca de verificación
  y las palabras «la más barata». **El color no es el mensaje**: un daltónico tiene que leerlo igual.
- **La diferencia** — en las demás filas, «+0,40 €» en `tinta-suave`: lo que cuesta elegir esa cadena
  frente a la mejor. Es la cifra que hace decidir.
- **Foco** — anillo de 2 px en `verde` dentro de la fila (`outline-offset: -2px`) para que no se salga
  del bloque.

## El consumidor pone

La lista ya ordenada de más barata a más cara (el orden es parte del contenido, no del estilo), el
nombre de cada cadena, el producto, los dos importes y cuál es la mejor. La app no debe reordenar por
otro criterio sin decirlo: una lista ordenada por precio y una ordenada por cercanía se parecen
demasiado.

## Sí / no

- Sí: la mejor fila primero, con su lavado verde y su veredicto escrito.
- Sí: el €/kg siempre, porque es lo que permite comparar 1 kg con 500 g.
- No: la fila más barata solo en verde sin palabras (el color solo no informa).
- No: seis filas sin separación: `borde` de 1 px entre filas y `space-8` dentro.
- No: precios en columnas de ancho variable: van con `font-variant-numeric: tabular-nums`.
