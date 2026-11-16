# Demo publicada, verificada a 390×844 — cierre del fallo (16/11/2026)

**URL:** <https://erdeivih.github.io/cesta-demo/>
**Momento:** 16/11/2026, 13:20–13:30 (Europe/Madrid).
**Build desplegado:** compilación `build:demo` del commit `a8b49bb` (+ manifest con rutas
relativas), publicada en `cesta-demo` `gh-pages` como **`9731f40`**.
**Instrumentos:** `curl` para el HTTP; `scripts/sonda-demo.mjs` y
`scripts/prueba-flujo-demo.mjs` para el navegador (Edge headless por CDP, 390×844).

## 1. Código y contenido sobre la URL real

| Recurso | HTTP | Tamaño |
|---|---:|---:|
| `/cesta-demo/` (raíz) | **200** | 1.770 B |
| `/cesta-demo/assets/index-CL_TrlWf.js` (bundle nuevo) | **200** | 590.961 B |
| `/cesta-demo/site.webmanifest` | **200** | 740 B |
| `/cesta-demo/icono.svg` | **200** | — |
| `/cesta-demo/assets/index-of8g-bLA.js` (bundle anterior, no borrado) | **200** | — |
| `/cesta-demo/api/listas` | **404** | página de Pages |

El 404 de `/api/*` **sigue siendo el comportamiento correcto**: en Pages no hay backend. La
diferencia con el fallo del 16/11 por la mañana es que el bundle ya no depende de él: lleva
**99 productos reales** del catálogo y `src/demo/api.ts` responde a `/api/*` antes de que
ninguna pantalla pregunte. Medido en el navegador: **0 peticiones a `/api/*`** salen a la red
y **0 respuestas no-2xx**.

## 2. La primera pantalla, a 390×844

Hay dos primeras pantallas, y se dan las dos porque significan cosas distintas:

| Pantalla | Qué pinta | En el primer viewport (sin desplazar) |
|---|---:|---:|
| **Entrada** (`/cesta-demo/`, La semana) | **8 productos** («La semana (8)», 17,06 €) | **2** líneas completas |
| **Búsqueda** (`#/compra?q=leche`) | **7 resultados** | **4 filas** (3 completas y la 4.ª asomando) |

**El número que responde al encargo es 8:** la primera pantalla de la demo publicada pinta
**8 productos**. La búsqueda pinta **7 resultados**, de los que **4** entran en el primer
pantallazo. En ambos casos hay **0 scroll horizontal** y **0 errores de consola**.

Lo que se ve en la búsqueda, en la primera fila:

> **Leche semidesnatada** · Aldi · **5 cadenas** · «0,34 €/l menos que el más caro» ·
> **0,83 €** · **0,83 €/l** · Ver ofertas por supermercado

Es decir: nombre, supermercado, **precio por unidad**, **cuántas cadenas comparan** y el
desplegable con el mismo producto en cada cadena. Captura: `capturas/demo-publicada-busqueda-390x844.png`.

## 3. El flujo entero, en la URL publicada

`node scripts/prueba-flujo-demo.mjs --base https://erdeivih.github.io/cesta-demo` → **`ok: true`,
0 fallos**:

| Paso | Resultado |
|---|---|
| Buscar «leche» | **7** filas; la primera con €/l y «5 cadenas» |
| Comparar | panel abierto con **5 cadenas** y su €/unidad (Aldi 0,83 → Carrefour 1,17 €/l) |
| Ficha | abre con «Añadir a la cesta» |
| Añadir | la ficha pasa a «En la cesta» |
| Lista | **9 líneas** (las 8 de la semana + la añadida), **17,89 €**, la leche está |

Captura del final del recorrido: `capturas/demo-publicada-flujo-390x844.png`.

## 4. Persistencia y reinicio, también sobre la URL publicada

Con un perfil de navegador persistente:

- **Favorito:** se pulsa «Guardar» en la ficha de «Leche entera brik 1 l.» (pasa a «Guardado»)
  y, tras recargar `#/compra/favoritos`, la pantalla dice **«1 producto»** con su precio
  (`0,94 €/l`). Sobrevive a la recarga.
- **Lista:** añadir una línea desde el typeahead deja «La semana (9)» y **sobrevive** a
  recargar (probado en local con el mismo bundle; en la URL publicada el flujo de arriba
  vuelve a la lista y la encuentra).
- **`?demo=reset`:** `#/compra/listas?demo=reset` vuelve a «La semana (8)», 17,06 €. Los datos
  viven en **IndexedDB** y la muestra está versionada (v3): lo guardado con la versión
  anterior se vuelve a sembrar en vez de mezclarse.

## 5. Qué se ha tocado

- `plataforma/web/app/src/demo/catalogo.json` y `catalogo.ts`: 99 productos reales, búsqueda,
  filtros y comparación.
- `plataforma/web/app/src/demo/estadoMuestra.ts`: lista de la semana, cuentas y favoritos.
- `plataforma/web/app/src/demo/api.ts`: la API de demo usa el catálogo y el estado nuevo.
- `plataforma/web/app/src/componentes/TablaResultados.tsx`: la fila del móvil dice cuántas
  cadenas comparan.
- `plataforma/web/app/public/site.webmanifest`: rutas relativas, para que el manifiesto y los
  iconos no den 404 bajo `/cesta-demo/`.
- El bundle anterior **no se ha borrado**: sigue respondiendo 200 en Pages; solo se añaden los
  assets nuevos y se actualiza el `index.html`.

## 6. Lo que la demo sigue sin prometer

- **No hay precios vivos**: son los de la captura de gold del **15/11/2026**.
- **No hay sincronización entre dispositivos**: lo escrito vive en este navegador.
- **No hay backend**: `/api/*` en Pages sigue siendo 404, y así se queda.
