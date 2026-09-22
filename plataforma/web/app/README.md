# Cesta — la interfaz nueva

Vite + React + TypeScript + Tailwind. Sustituye a `../index.html` + `../app.js`
(80 KB escritos a mano). Aquellos dos ficheros **siguen ahí, sin tocar**, hasta
que esta tenga paridad; entonces se borran.

La interfaz está en español, como el resto del repositorio.

---

## Arrancar en desarrollo

```powershell
cd plataforma\web\app
npm install
npm run dev            # http://localhost:5173
```

`/api` se manda por proxy al backend, así que **todo se pide por rutas
relativas** (`/api/buscar`, `/api/grupo/4125`) y no hay CORS ni cookies que se
pierdan entre puertos.

El destino por defecto del proxy es `http://127.0.0.1:8000` (uvicorn a mano).
**Con `docker-compose.yml` tal como está hoy, la API no publica el 8000**: solo
la ve Caddy por la red interna. Para desarrollar contra la plataforma ya
levantada, apunta al 8080 de Caddy:

```powershell
$env:CESTA_API='http://127.0.0.1:8080'; npm run dev
```

## Construir

```powershell
npm run build          # tsc --noEmit && vite build
```

Deja el resultado en **`plataforma/web/dist`** (`index.html` + `assets/`), que es
lo que hay que montar en `/srv`:

```yaml
volumes:
  - ./web/dist:/srv:ro      # hoy pone ./web:/srv:ro
```

`base: '/'` y `build.outDir: '../dist'` están puestos a propósito en
`vite.config.ts`: con una base relativa, `/grupo/4125` pediría los assets a
`/grupo/assets/...` y la ficha saldría en blanco.

---

## Pantallas

| ruta | qué hace |
|---|---|
| `/` | **Buscador + resultados.** Filtros combinables (cadena, pasillo, sellos, ofertas, marca propia, comparables, con nutrición, sin alcohol, conservación), tabla ordenable, y **guardar la combinación de filtros con un nombre** en `localStorage`. |
| `/grupo/:id` | **El grupo, en columnas por cadena.** Precio, precio por unidad, diferencia % contra el más barato, calidad o gama, Nutri-Score, promo, chispa del histórico y un **control de pesos que reordena en vivo** y explica el orden. |
| `/producto/:cadena/:idFuente` | **Ficha de producto**: histórico (mínimo, máximo, media, evolución), su grupo de equivalencias y la explicación del emparejamiento (ver límites). |
| `/escaner` | **Escáner**: se teclea o se pega el código → `/api/ean/{codigo}`. Si lo encuentra, enseña la comparación y lleva al grupo; si no, el motivo y la sugerencia. Botón de cámara con `BarcodeDetector` **solo si el navegador lo tiene**. |
| `/panel` | **Panel**: hoy, cadenas, marcas (con su `aviso` siempre visible), histórico, movidos y bajadas. |
| `/panel/matching` | **Panel de matching**: la última pasada del emparejador —métricas, cambios contra la pasada anterior y una muestra de pares **con los rasgos que los sostienen**—. Solo lectura: no hay ni un botón de aprobar o rechazar. |

Los filtros del buscador viven **en la URL**, no en el estado del componente: así
el botón de atrás vuelve a la misma búsqueda y una vista guardada es
exactamente el enlace que se copiaría a mano.

### Estructura

```
src/
  api/            cliente.ts (fetch + ErrorApi), consultas.ts (TanStack Query), formato.ts (€ y fechas)
  componentes/    ui.tsx (botones, etiquetas, tablas), Chispa.tsx (uPlot), Cabecera, Nav,
                  FiltrosBusqueda, TablasResultados, ControlPesos, Etiquetas, VistasGuardadas,
                  ExplicacionEmparejamiento
  estado/         filtrosUrl.ts (filtros ↔ URL), vistasGuardadas.ts (localStorage)
  logica/         pesos.ts (la nota y el orden del grupo)
  paginas/        Buscar, Grupo, Producto, Escaner, Panel, PanelMatching
  tipos.ts        los contratos de la API
```

---

## Stack, y por qué

- **TanStack Query** para los datos de servidor. El estado de las cadenas lo usan
  la cabecera, el buscador y el grupo: se pide una vez y se comparte.
  `staleTime` largo porque gold cambia una vez al día.
- **TanStack Table** para la tabla de resultados: da el estado de ordenación y
  las columnas, pero el HTML lo escribe el componente, que es lo que permite que
  sea una `<table>` de verdad (con `scope="col"`, `aria-sort` y teclado) y no
  cuarenta `<div>` con pinta de tabla.
- **uPlot** para las series de precio (no Recharts). Son 40 px de alto y puede
  haber cuarenta en una pantalla; uPlot pinta en canvas y pesa ~50 KB, Recharts
  mete d3 y un SVG por gráfica. La chispa es un adorno del dato: los números
  (mínimo, máximo, media) van siempre escritos al lado.
- **Componentes propios** con Tailwind, sin el CLI de shadcn. Son ocho piezas
  pequeñas y así no se copia al repositorio una dependencia de herramienta con
  cientos de líneas que nadie lee.

El bundle construido son ~494 KB (157 KB comprimido), casi todo React y el
router. No está partido por rutas: con una app de seis pantallas que se usan
encadenadas, partir el bundle cambia una descarga por tres.

---

## Lo que la interfaz respeta del proyecto

- **Nada de validación humana.** No hay pantallas de aprobar ni de rechazar, ni
  de corregir equivalencias a mano. El panel de matching lo dice en pantalla.
- **`calidad` y `gama` no se mezclan.** Cada producto trae una de las dos (lo
  garantiza `/api/grupo`), la interfaz dice de dónde sale cada letra, y el peso
  "letra" usa la que haya **diciendo cuál es**. Nunca se suman: en la gama, la A
  es el extremo **caro** del grupo, no el mejor.
- **Un dato que no tenemos es `null`, nunca cero.** `precio_unidad_cent: null`
  se pinta "no lo sé"; `ahorro_pct: 0.0` es el centinela de "no comparable" y se
  pinta "no lo sé", no un 0 %.
- **`fecha_datos` se enseña siempre** (cabecera pegada, y en cada vista de
  catálogo). Un precio de más de `dias_precio_valido` (hoy 3) días se enseña con
  su fecha, se marca, **no decide** y queda fuera de la referencia del "más
  barato".
- **Los céntimos se pasan a euros al pintar**, no antes.
- **Móvil primero**: barra de navegación abajo, áreas de pulsar de 44 px, y
  tablas con scroll horizontal dentro de su caja (nunca la página entera).
- Sin tutorial, sin pantalla de actividad, sin valoraciones y sin publicidad.

---

## Endpoints que usa

`/api/buscar`, `/api/secciones`, `/api/estado`, `/api/grupo/{id}`,
`/api/producto/{cadena}/{id}`, `/api/ean/{codigo}`, `/api/bajadas`,
`/api/panel/hoy`, `/api/panel/cadenas`, `/api/panel/marcas`,
`/api/panel/historico`, `/api/panel/movidos`, `/api/panel/matching?limite=`.

**Endpoints que NO existen y por eso no se usan:**

- **Vistas guardadas** — no hay endpoint. Se guardan en `localStorage`, y lo que
  se guarda es la propia consulta (`?sellos=sin-lactosa&cadenas=dia`). La
  pantalla lo dice: "solo está en este navegador".

`GET /api/panel/matching` **sí existe** (`plataforma/api/catalogo.py`,
`matching()`, cometido el 22/09/2026). Se pide de verdad y se pinta con su
contrato: `ultima`, `metricas`, `cambios`, `pares` (con `nivel`, `metodo`,
`confianza` y `features`) y `ejecuciones`. Si el servidor que atiende es anterior
y contesta **404**, la pantalla no pinta un error rojo: dice que esa ruta no está
en ese servidor y que hace falta `docker compose up -d --build api`. Si contesta
bien pero `ultima` es `null`, dice que no hay ninguna pasada guardada en
`data/gold/matching/`.

---

## Límites conocidos, y cosas sin hacer

- **La marca no viene en `/api/buscar`.** El contrato devuelve `nombre`, pero no
  `marca`, así que las filas del buscador enseñan el nombre (que casi siempre la
  lleva dentro) y no una columna "Marca" que inventaría el dato. Se arregla
  añadiendo `marca` a la respuesta de `/api/buscar`.
- **La chispa no se pinta cuando la cadena tiene más de un producto en el
  grupo.** `serie` va por `fuente` y `fecha`, sin decir de qué producto es cada
  punto: con dos productos de la misma cadena, dibujar esa línea mezclaría dos
  históricos. En ese caso se dice en pantalla en lugar de dibujar algo falso.
  Se arregla añadiendo `producto_id` a cada punto de `serie`.
- **La explicación del emparejamiento no existe todavía.** En `/api/grupo` no
  hay ningún campo con el método ni con el parecido. La ficha busca los nombres
  plausibles de ese campo y, si no está, lo dice. No se inventa.
- **`BarcodeDetector` solo lo tienen Chrome y derivados** (ni Firefox ni Safari),
  y la cámara necesita HTTPS (o `localhost`). Si no está, el botón no se pinta.
- **Cámara no probada** en un dispositivo real: el flujo está escrito, pero lo
  único verificado es que el botón no aparece cuando el navegador no tiene
  `BarcodeDetector`.
- **Sin pruebas automáticas.** No hay ni un test en esta app. Lo que se ha
  comprobado es: `npm run build` pasa, y las pantallas se han abierto con un
  navegador de verdad (Edge en modo headless, viewport de 390 px) contra la API
  real, mirando que no haya desbordamiento horizontal, que los estados vacíos
  salgan y que los números cuadren a mano.
- **El buscador no pagina.** Pide 40 (o 80, o 120) resultados y ordena esos,
  dentro de la página que ha llegado; la pantalla lo dice.
- **El panel de matching se ha probado contra el contrato, no contra el
  servidor**: la imagen de la API que corre ahora mismo no tiene la ruta (ver
  abajo), así que se ha probado sirviendo una pasada real de
  `data/gold/matching/` leída con DuckDB. El estado 404 también está probado,
  contra la API de verdad.

## Dos problemas del backend que se han visto al probar esto

No se ha tocado nada fuera de `plataforma/web/app/`, así que quedan apuntados:

1. **`/api/grupo/{id}` da 500** para cualquier grupo cuyos productos tengan
   `promo_hasta` no nulo: DuckDB necesita `pytz` para devolver un
   `TIMESTAMP WITH TIME ZONE` y la imagen de la API no lo tiene.

   ```
   _duckdb.InvalidInputException: Invalid Input Error: Required module 'pytz'
   failed to import, due to the following Python exception:
   ModuleNotFoundError: No module named 'pytz'
   ```

   Se arregla añadiendo `"pytz"` al `pip install` del `Dockerfile` (o
   convirtiendo `promo_hasta` a texto en la consulta). Es la pantalla clave del
   encargo, así que merece la pena mirarlo pronto.

2. **La imagen de la API está anticuada**: el contenedor que corre no tiene la
   ruta `/api/ean` (`grep 'api/ean' /app/plataforma/api/main.py` no devuelve
   nada) ni `/api/panel/matching`, así que hoy contesta 404 a las dos. El código
   del repositorio sí las tiene; hace falta `docker compose up -d --build api`.

3. **`plataforma/web/dist` está metido en git.** Los ficheros que genera
   `npm run build` aparecen versionados (commit `cce2bbd`). Es un artefacto que
   se reconstruye: lo suyo es ignorarlo (`plataforma/web/dist/` en el
   `.gitignore` de la raíz). No se ha tocado el `.gitignore` de la raíz porque
   está fuera de `plataforma/web/app/`.
