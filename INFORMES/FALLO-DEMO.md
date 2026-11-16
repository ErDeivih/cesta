# La demo publicada no enseña productos — reproducción y causa (16/11/2026)

**URL publicada:** <https://erdeivih.github.io/cesta-demo/>
**Comprobado:** 16/11/2026, 13:03–13:10 (Europe/Madrid), contra la URL real, sin servidor local.
**Instrumentos:** `curl` (HTTP) y `scripts/sonda-demo.mjs` (Edge headless por CDP, 390×844).

## 1. Lo que devuelve el servidor: la API no existe en Pages

```
$ curl -sS -o /dev/null -w "%{http_code} %{content_type}\n" https://erdeivih.github.io/cesta-demo/
200 text/html; charset=utf-8

$ curl -sS -o /dev/null -w "%{http_code} %{content_type}\n" \
    https://erdeivih.github.io/cesta-demo/assets/index-of8g-bLA.js
200 application/javascript; charset=utf-8

$ curl -sS -i https://erdeivih.github.io/cesta-demo/api/listas | head -1
HTTP/1.1 404 Not Found

$ curl -sS -o /dev/null -w "%{http_code}\n" \
    "https://erdeivih.github.io/cesta-demo/api/buscar?q=leche&limite=12"
404

$ curl -sS -o /dev/null -w "%{http_code}\n" https://erdeivih.github.io/cesta-demo/api/yo
404
```

El 404 **no es JSON**: GitHub Pages contesta su página de error (`Content-Type: text/html`,
`Server: GitHub.com`). Sirve para confirmar el diagnóstico del encargo: **en Pages no hay
backend, y todo `/api/...` que llegue al servidor acaba en 404**.

El bundle publicado (`assets/index-of8g-bLA.js`) sigue llevando las rutas `/api/...` dentro
(`/api/listas`, `/api/buscar`, `/api/entrar`, `/api/salir`, …), y también lleva
`__cestaDemoApi`, el parche que las intercepta. Es decir: **la app se salva solo mientras el
parche de demo se instale antes de la primera petición**. Si no se instala (build antiguo, una
ruta que no pasa por `fetch`, o el `?demo=` que fuerza un estado), la petición sale a Pages y
allí está el 404 de arriba.

## 2. El fallo de verdad: el catálogo no es un catálogo

Con la compilación publicada, la demo **sí pinta resultados para las tres búsquedas que lleva
capturadas**, y **cero para cualquier otra**. Medido a 390×844:

| Búsqueda | Resultados | Qué se ve |
|---|---:|---|
| `#/compra?q=leche%20entera` | **36** | «36 resultados · datos del 13 nov 2026», con €/unidad |
| `#/compra?q=papel%20de%20cocina` | 40 (capturado) | la muestra original |
| `#/compra?q=atún%20en%20aceite` | 39 (capturado) | la muestra original |
| `#/compra?q=arroz` | **0** | «Nada con «arroz»» |
| `#/compra?q=pollo` | **0** | «Nada con «pollo»» |
| `#/compra?q=huevos` | **0** | «Nada con «huevos»» |
| `#/compra` (entrada, sin texto) | 0 | ejemplos y mosaico «Lo de siempre» |

Evidencia en crudo: `.tmp-demo/sonda-arroz.json`, `.tmp-demo/sonda-compra.json`,
`.tmp-demo/sonda-entrada.json`, `.tmp-demo/sonda-listas.json`, `.tmp-demo/sonda-favoritos.json`.
Captura de la búsqueda con resultado: `capturas/sonda-demo-compra-390x844.png`.

**Causa raíz:** `src/demo/datos.json` no es un catálogo. Son **120 filas** capturadas de la API
el 13/11/2026 para **tres búsquedas de ejemplo** («leche entera», «papel de cocina», «atún en
aceite»). La función `busca()` de `src/demo/api.ts` filtra esas 120 filas por texto:

- «arroz», «pollo», «huevos», «manzana», «tomate» o «pan» existen en cualquier supermercado,
  pero **no están en esas 120 filas**, así que el buscador contesta «Nada con …».
- Los detalles por cadena (`grupos`) solo existen para **6 grupos**; los otros 114 resultados no
  tienen comparación real detrás.
- Los filtros de la pantalla (cadena, pasillo, ofertas, comparable…) **se ignoran** en la demo:
  `busca()` solo mira el texto.
- `#/compra/favoritos` enseña «No sigues ningún producto»: el endpoint devuelve `{}` y no hay
  forma de guardar un favorito.
- Además, el icono se pide a `https://erdeivih.github.io/icono.svg` (sin el prefijo
  `/cesta-demo/`) y da **404**: es el mismo error de base que arrastra el `<link rel="icon">`.

Así que la frase «no aparecen productos» es exacta, pero la causa no es solo el 404: **el 404
está tapado por el parche de demo, y lo que falla es que la muestra es demasiado pequeña**. La
persona busca lo que compra (arroz, pollo, huevos) y la demo no tiene nada que enseñar.

## 3. Cómo se reproduce

```bash
# HTTP: la API no existe en Pages
curl -sS -o /dev/null -w "%{http_code}\n" https://erdeivih.github.io/cesta-demo/api/listas

# Navegador real a 390×844: cero productos para una búsqueda normal
cd plataforma/web/app
node scripts/sonda-demo.mjs \
  --url "https://erdeivih.github.io/cesta-demo/#/compra?q=arroz" \
  --salida ../../../.tmp-demo/sonda-arroz.json
```

## 4. Qué se va a arreglar (y qué no)

1. **Catálogo real embebido** de 80–120 productos (nombre, precio, unidad, supermercado, imagen)
   sacado de `data/gold`, no inventado, con ofertas por cadena para poder comparar.
2. **Buscador y typeahead** contra ese catálogo, sin backend, con los filtros de la pantalla.
3. **€/unidad y comparación entre cadenas** visibles en el resultado y en la ficha.
4. **Lista de la semana y favoritos** en demo, guardados en el navegador (IndexedDB ya existe).
5. **Pruebas** del flujo búsqueda → añadir → lista → comparación.
6. **Publicación** y verificación a 390×844 sobre la URL real.

No se toca el backend (`cesta-api`, `cesta-db`) ni la app de casa servida por Caddy: esto es solo
la compilación `build:demo` que va a GitHub Pages.

## 5. Cierre (16/11/2026, 13:30)

Arreglado y verificado sobre la URL publicada: la primera pantalla pinta **8 productos**, la
búsqueda «leche» da **7 resultados** (4 en el primer viewport), el mismo producto se compara en
**5 cadenas** y el flujo búsqueda → añadir → lista → comparación termina con **9 líneas y
17,89 €**. `/api/*` sigue dando 404 en Pages, que es lo correcto: la demo ya no lo necesita.
Medidas, capturas y HTTP en [`DEMO-PUBLICADA.md`](DEMO-PUBLICADA.md).
