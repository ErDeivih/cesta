# ChipEtiqueta

Las etiquetas que significan algo, en una pieza: la letra del Nutri-Score y los sellos del producto.

## Cuándo

En la ficha de un producto y en cada fila de resultado. Son dos formas distintas y no se mezclan: la
letra es un cuadrado (`radio-nota`, 24×24), el sello es una pastilla baja (`radio-pastilla`, alto 24).

## Anatomía

- **Letra del Nutri-Score** — cuadrado de 24 px en `radio-nota`, fondo `nutri-a` … `nutri-e`, texto
  `nutri-texto-a` (A) o `nutri-texto-b-e` (B, C, D) o `nutri-texto-e` (E). La letra va en 13 px,
  peso 600.
- **Sello** — pastilla en `sello-fondo` (que es `lavado-verde`) con texto `sello-tinta` (que es
  `verde-fuerte`), 13 px. Texto en minúscula: «vegano», «sin gluten», «sin lactosa».
- **Sin dato** — «sin Nutri-Score», en una pastilla con borde `borde-fuerte` y texto `tinta-suave`.
  No se pinta el hueco como una letra gris: un hueco se lee como un cero.

## El consumidor pone

La letra (`a`…`e`, o `null`) y la lista de sellos (`vegano`, `vegetariano`, `sin-gluten`, `sin-lactosa`,
`ecologico`, `sin-azucar`, `sin-sal`, `sin-aceite-palma`). Una letra que no venga, no se inventa.

## Sí / no

- Sí: la A con `nutri-texto-a` (blanco) y la B con `nutri-texto-b-e` (tinta). Las correcciones están
  medidas: el naranja oficial de la E no pasaba AA y aquí es `#cf3a0f`.
- Sí: tres o cuatro sellos como mucho. Un producto con nueve sellos no dice nada.
- No: la letra como único indicador de calidad: el Nutri-Score mide el perfil nutricional, no si el
  producto es bueno.
- No: rellenar la E de un producto sin dato («no hay dato» no es «lo peor»).
- No: emoji en lugar de sello.
