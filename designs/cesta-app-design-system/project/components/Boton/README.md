# Boton

La acción de la pantalla, en tres niveles y siempre con 44 px de alto.

## Cuándo

- **`primario`** — la acción que la pantalla existe para hacer: «Añadir a la lista». Uno por pantalla.
  Relleno `verde`, texto `sobre-verde`, `sombra-apoyado`; al pulsar, `verde-fuerte`.
- **`secundario`** — una acción de apoyo que no compite: «Compartir». Fondo `papel` con borde
  `borde-fuerte` (3,8:1 sobre papel: el borde delimita el control, así que no vale `borde`).
- **`fantasma`** — navegar dentro de lo mismo: «Ver las 6 cadenas». Sin fondo, texto `verde`, y al
  pasar por encima, `lavado-verde`.
- **No se puede** — fondo `lavado-aviso`, texto `aviso`, `disabled`, y **al lado** la frase que dice por
  qué y qué hacer («Sin permiso de cámara: ábrelo en los ajustes del navegador»). Un botón apagado sin
  explicación es un callejón.

## Anatomía

`min-height: 44px` (`toque-minimo`), `space-16` de relleno lateral, `radio-campo` (10 px), 16 px de
texto en peso 600, 8 px entre icono y texto. Icono SVG en línea de 16 px, `aria-hidden`. La transición
es de 120 ms en `background-color` y `box-shadow`, con `curva-suave`, y se apaga sola con
`prefers-reduced-motion`.

## El consumidor pone

La etiqueta (un verbo concreto: «Añadir a la lista», no «Aceptar») y qué hace. El botón es un
`<button type="button">` de verdad; si navega, un `<a>` con el mismo aspecto.

## Sí / no

- Sí: el foco visible, anillo de 2 px en `verde` con 2 px de separación.
- Sí: un icono cuando aclara la acción (compartir, escanear); nunca un icono solo sin nombre accesible.
- No: dos botones primarios en la misma pantalla: si hay dos, ninguno es el principal.
- No: `div` con `onclick`, ni `role="button"` sin teclado.
- No: botones de menos de 44 px de alto, aunque el texto quepa.
