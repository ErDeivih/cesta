# Demo publicada — Cesta en GitHub Pages (14/11/2026)

**URL:** <https://erdeivih.github.io/cesta-demo/> — **HTTP 200** (comprobado el 14/11/2026).
**Repositorio:** <https://github.com/ErDeivih/cesta-demo> (público, Pages desde la rama `gh-pages`,
tipo `legacy`, estado `built`).

## Qué es

La misma app de Cesta, compilada en **modo demo** (`npm run build:demo`), con **la muestra de datos
incrustada** y sin servidor detrás:

- La muestra son **130 KB de datos reales** capturados de la API del proyecto el 13/11/2026: una
  lista (`La casa`, 6 líneas), el reparto por cadenas, 120 resultados de búsqueda de las tres
  búsquedas de ejemplo y 6 grupos con sus precios por supermercado.
- `src/demo/api.ts` responde a `/api/*` con esos datos, así que la demo funciona **sin red** una vez
  cargada la página. Las rutas van en el **hash** (`#/compra/listas`) para que Pages no tenga que
  resolver rutas profundas.
- **Los datos viven en el dispositivo**: la primera visita siembra la muestra en **IndexedDB**
  (`src/demo/almacen.ts`); a partir de ahí, añadir, tachar, cambiar cantidad, quitar o cerrar la
  compra **se guarda en el navegador y sobrevive a recargar**. Si la muestra cambia de versión, se
  vuelve a sembrar; **`?demo=reset` borra lo guardado** y deja la demo como nueva.
  *No hay sincronización entre dispositivos*: para eso hace falta la API en el servidor.
  La demo no promete precios vivos.

## Estados, para enseñarlos

En la propia demo:

| Estado | URL |
|---|---|
| Normal | <https://erdeivih.github.io/cesta-demo/#/compra/listas> |
| Vacío (sin listas) | `#/compra/listas?demo=vacio` |
| Carga (listas lentas) | `#/compra/listas?demo=carga` |
| Error (listas a 500) | `#/compra/listas?demo=error` |
| Reiniciar la demo (borra lo guardado) | `#/compra/listas?demo=reset` |

## Cómo se publica

```bash
cd plataforma/web/app
npm run build:demo        # tsc + vite --mode demo + .nojekyll; sale en plataforma/web/demo-dist
cd ../demo-dist
git init -b gh-pages && git add -A && git commit -m "Demo de Cesta"
git remote add origin https://github.com/ErDeivih/cesta-demo.git
git push -u origin gh-pages
```

Pages se activó al primer empuje de `gh-pages`; el estado quedó `built` y la raíz respondió 200 en
menos de un minuto. El build normal (`npm run build`) sigue saliendo a `plataforma/web/dist` para
Caddy: la demo no toca la app que se sirve en casa.

## Medición de la demo publicada

Con el mismo instrumento del proyecto, contra la URL publicada, a **390×844** y 1440×900:
`medicion-demo-pages.json` y `capturas/ui-demo-pages-*`. Resumen a 390×844:

- Sin scroll horizontal en `/compra`, `/compra` con filtro, `/compra/listas` y la comparativa.
- Entrada normal: typeahead «Añadir a la lista» a `top=319`, **0/14 controles tapados**; al escribir
  «leche» salen **8 sugerencias** con €/unidad y `Escape` cierra conservando el texto; «Elegir
  varias líneas» abre un listbox con **6 opciones**, `Espacio` marca (`aria-selected`) y `Escape`
  sale.
- Estados vacío/carga/error servidos por la propia demo (`?demo=`), con 0 controles tapados
  (0/5, 0/0 y 0/1) y sin scroll horizontal.

## Límites, dichos

- Las pantallas fuera de la compra (panel, recetas, ajustes) no tienen muestra: se quedan en su
  estado vacío o de error. La demo es de **la compra**, que es lo que se quiere enseñar.
- Los precios son de la captura del 13/11/2026 y no se actualizan.
- Lo que se escribe queda **en este navegador**: no viaja a otro dispositivo ni a otra persona, y
  borrar los datos del sitio devuelve la muestra.
- El cambio de cuenta y la sincronización entre dispositivos no existen en la demo: para eso hace
  falta la API en el servidor (decisión del 14/11 en `DECISIONES.md`).

## Persistencia comprobada en la URL publicada (14/11/2026)

Con Edge headless contra <https://erdeivih.github.io/cesta-demo/>: la lista de la muestra tiene
**6 líneas** → se añade una por la API de la demo (`POST /api/listas/{id}/lineas`, **200**) →
**7 líneas** → **recarga completa** → **7 líneas**, con «Producto de prueba (demo)» al final →
`#/compra/listas?demo=reset` + recarga → **6 líneas**. El estado lo guarda IndexedDB en el propio
navegador; el build desplegado fue el `3a44741` de `gh-pages`.

**El vacío también se alcanza de verdad**, no solo con `?demo=vacio`: en la URL publicada se borra
«La casa» (`DELETE /api/listas/{id}` → **200**), se recarga y sale **«No tienes ninguna lista» con el
buscador en pie**; después, `?demo=reset` + recarga devuelve la lista con sus **6 líneas**. Captura:
`capturas/ui-demo-pages-vacio-borrando-390x844.png`.
