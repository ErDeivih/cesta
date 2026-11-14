# Nombre de la app — propuesta y decisión (14/11/2026)

**Decisión: `Cesta Clara`.** Se decide aquí, con criterio; el cambio de marca en código y textos va
en una pasada aparte (plan al final), para no dejar media app con un nombre y media con otro.

## El problema con «Cesta»

No está mal como palabra: es la categoría («la cesta de la compra») y ya está en todas partes del
código. Pero como **nombre** falla en dos cosas concretas:

- **No distingue**: hay muchas apps, listas y blogs llamados «Cesta»; buscar «Cesta» no lleva a esta.
- **No dice nada de lo que la hace distinta**: comparar cinco cadenas, precio por unidad, la compra
  de la semana y lo que se cocina con ello.

## Candidatos

| Nombre | A favor | En contra |
|---|---|---|
| **Cesta Clara** | Conserva la categoría (se busca «cesta de la compra») y añade el diferenciador: claridad de qué comprar, dónde y cuánto. Dos palabras, fácil de pronunciar y de recordar; `cestaclara` funciona como usuario y carpeta; no promete nada que la app no haga | Dos palabras, algo más largo en la barra del móvil; «Clara» es nombre de persona y puede dar lugar a confusión si se dice en voz alta sin contexto |
| **Hilada** | Sale del lema que ya existe («la compra de la semana, bien hilada»): corto, distinto, fácil de registrar y de buscar; suena a producto cuidado, no a comparador genérico | Opaco: quien no conoce la app no sabe qué es; pierde la palabra de categoría y obliga a un subtítulo siempre; «hilada» también es un término de sastrería |
| **La Semana** | Captura el bucle real (se compra una vez por semana) y es cálido, de casa | Muy genérico y muy ocupado: no dice de compras ni de precios, y se pierde en cualquier búsqueda; como marca no es apropiable |

## Por qué `Cesta Clara`

1. **Dice la categoría y el beneficio**: quien la oye por primera vez entiende «lista de la compra
   con las cosas claras», que es exactamente la promesa (qué compro, dónde sale mejor, cuánto cuesta
   y qué cocino).
2. **Se puede buscar**: dos palabras que juntas no compiten con el sustantivo suelto ni con las
   apps genéricas; el identificador `cestaclara` es razonable como usuario y como carpeta.
3. **No miente**: no promete «ahorro garantizado», «el más barato» ni «inteligencia»; promete
   claridad, que es lo que la app da (precio por unidad, diferencias en euros, cobertura por cadena).
4. **Encaja con lo autoalojado**: «clara» no tiene ecos de nube ni de marketplace; una app que vive
   en tu servidor no debería llamarse como una plataforma que se come tus datos.

**Lo que no se ha comprobado** (y por eso es una propuesta, no un hecho): disponibilidad de dominio,
registro de marca y usuarios ya ocupados en las tiendas y en GitHub. Antes de publicar con el nombre
nuevo hay que mirarlo; si `Cesta Clara` está tomado, la segunda opción es **Hilada** con el subtítulo
«la compra de la semana, bien hilada».

## Plan de cambio (cuando toque, no en esta pasada)

- `index.html`: `<title>`, `og:title` y `apple-mobile-web-app-title`.
- `public/site.webmanifest`: `name`, `short_name` y `description`.
- `src/App.tsx`: el `<h1>` de la portada.
- `tests/manifiesto.test.mjs` y `tests/portada.test.mjs`: los valores esperados.
- README, `AGENTE.md`, la demo publicada y el repo `cesta-demo`.

**Mientras no se haga ese cambio**, la app sigue llamándose «Cesta» en pantalla: un nombre a medias
en la barra del móvil es peor que el nombre viejo.
