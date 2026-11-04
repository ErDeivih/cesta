# Tarjeta

La superficie de contenido del sistema: una pieza de la lista o el bloque que resume algo, en `papel`
`radio-tarjeta` y `space-16` de relleno.

## Cuándo

Para agrupar un producto, una cesta o un aviso. La variante `destacada` (fondo `bosque`, texto
`sobre-bosque`) es para **el dato que hay que ver primero en la pantalla**: la cifra de la cesta, el
ahorro. En una pantalla hay como mucho una.

## Anatomía

- **Superficie** — `papel`, `radio-tarjeta` (16 px), `space-16` de relleno, sombra `apoyado` si se
  puede pulsar. En oscuro, la tarjeta no se separa con sombra: se separa porque `papel` es más claro
  que `marfil`.
- **Rótulo** — `micro` (12 px, versalitas, `tinta-tenue`): «MI CESTA», «PRODUCTO». Dice de qué va la
  tarjeta sin gastar un título.
- **Título** — `subtitulo` en Fraunces (19/25) o `cifra` grande; es lo que se lee primero.
- **Meta** — 13 px en `tinta-tenue`: formato, cadena, fecha.
- **Insignia** — opcional, en `lima` con texto `sobre-lima` y `radio-pastilla`: el ahorro, la bajada.
- **Pulsable** — envuelta en un `<a>`; la tarjeta entera es el objetivo, y el foco es el anillo de 2 px
  en `verde`.

## El consumidor pone

El contenido (título, meta, cifras) y si la tarjeta lleva a algún sitio. La tarjeta no decide su propio
ancho: lo pone la columna de la pantalla (a 390 px, 358 px de ancho con margen de 16 px).

## Sí / no

- Sí: una tarjeta, un dato principal. Si hay dos cifras del mismo rango, no es una tarjeta: son dos.
- Sí: `destacada` con `sombra-alzado` cuando está en primer plano.
- No: borde lateral de color como acento (es el cliché de tarjeta de panel).
- No: esquinas distintas para la misma familia: la tarjeta siempre 16 px, el botón 10, la hoja 24.
- No: sombra en la variante `destacada` en modo oscuro: allí ya se separa por color.
