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
- **Escribir se puede**: añadir, tachar, cambiar cantidad o cerrar la compra se aplica en memoria
  durante la visita. **No hay persistencia**: al recargar vuelve la muestra. Es una demo estática y
  lo dice; no promete precios vivos ni sincronización.

## Estados, para enseñarlos

En la propia demo:

| Estado | URL |
|---|---|
| Normal | <https://erdeivih.github.io/cesta-demo/#/compra/listas> |
| Vacío (sin listas) | `#/compra/listas?demo=vacio` |
| Carga (listas lentas) | `#/compra/listas?demo=carga` |
| Error (listas a 500) | `#/compra/listas?demo=error` |

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
- El cambio de cuenta y la sincronización entre dispositivos no existen en la demo: para eso hace
  falta la API en el servidor (decisión del 14/11 en `DECISIONES.md`).
