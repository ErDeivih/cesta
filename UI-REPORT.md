# UI-REPORT — Cesta (pasada de UI del 13/11/2026)

Contrato: [`ESPECIFICACION.md`](ESPECIFICACION.md) (§10 es el anexo de cierre, con lo que se movió
al hacerlo). Medición: [`medicion.json`](medicion.json) (después) y
[`medicion-antes.json`](medicion-antes.json) (antes). Capturas: [`capturas/`](capturas/).
Código nuevo: [`plataforma/web/app/src/componentes/ui-sdk/`](plataforma/web/app/src/componentes/ui-sdk/).

Piezas: `@ui-sdk/core` y `@ui-sdk/react` **0.1.0-beta.1** (Apache-2.0), instaladas en
`plataforma/web/app/package.json`.

---

## 1. Qué cambió, en una tabla

| Antes | Después | Por qué |
|---|---|---|
| «Añadir producto» era un `<Link>` a `/compra`: apuntar obligaba a **salir de la lista**, buscar y volver | **Typeahead en la propia lista** (`Combobox` + `useAsyncOptions`): se escribe, salen hasta 8 sugerencias **con su €/kg**, y Enter/click apunta sin soltar el campo | Es el hueco medido: buscar era otra pantalla y volver, otro viaje. El €/kg es la decisión de compra |
| Si no había ninguna lista, la pantalla era un cartel («No tienes ninguna lista») y un mosaico | El **typeahead también está ahí**: apunta en la lista de casa, que se crea sola | Quien acaba de llegar no puede tener como primer paso crear una lista antes de apuntar |
| Ninguna de las tres pantallas decía **«sin conexión»** | `SinConexion` en las tres: «lo que apuntes se guarda en el móvil y sube al volver la red», sin bloquear y sin prometer lo que no consta | La app se usa en el pasillo, que es donde peor va la red |
| Cerrar la compra era un `Aviso` abierto en la propia lista | **Diálogo modal** (`Dialog` de `@ui-sdk`): `role="dialog"`, nombre, foco dentro, Tab que no se escapa, Escape y foco que vuelve al botón | Una acción que quita N cosas y no se deshace de un toque se pregunta aparte, no dentro de la lista que estás tocando |
| Quitar líneas era **una por una** | **Selección múltiple** (`Listbox multiple`): espacio marca, Mayús+espacio/rango, Ctrl+A todas, barra «N líneas seleccionadas» y «Quitar N líneas» | Quitar media lista de una en una es el trabajo que hace que la lista se deje de usar |
| La comparativa pintaba **todas** las líneas | Desde **21 líneas**, `ListaVirtualizada`: se pinta la ventana (con `aria-setsize`/`aria-posinset`) y el detalle se lee en un diálogo | Con 60 líneas, el primer pintado entero y el lector sin saber cuántas hay |
| Una lista compartida para mirar no tenía un campo que explicara que no se puede escribir | Campo **solo lectura** con el motivo («pide el papel de escribir») | Un botón que no puede funcionar es una promesa que no se cumple |
| Un fallo del buscador se quedaba mudo | Estado **error** dentro del combo: «No he podido buscar» + `Reintentar`, **sin perder el texto** | Un error sin salida deja la pantalla muerta |

Lo que **no** cambia: datos, API, permisos, lógica de negocio, tokens/colores, tipografía y las
otras pantallas. El buscador de `/compra` no se tocó (ver §7).

### 1.1 Las cuatro piezas y sus pruebas

| Pieza | Fichero | `@ui-sdk` que usa | Pruebas |
|---|---|---|---:|
| `Typeahead` | `src/componentes/ui-sdk/Typeahead.tsx` | `Combobox` + partes; `useAsyncOptions` | **6** |
| `SeleccionMultiple` | `src/componentes/ui-sdk/SeleccionMultiple.tsx` | `Listbox`/`ListboxItem` `multiple` | **4** |
| `Foco` (`Dialogo`) | `src/componentes/ui-sdk/Foco.tsx` | `Dialog`/`DialogContent`/`DialogTitle` | **3** |
| `ListaVirtualizada` | `src/componentes/ui-sdk/ListaVirtualizada.tsx` | — (se dice por qué en el fichero) | **7** |

*`ListaVirtualizada` es la única que no delega*: `createVirtualizer` de `@ui-sdk/core` lee
`clientHeight` del contenedor y esta pieza recibe la ventana por prop (`alto`, `alturaFila`), que es
lo que permite medirla en jsdom. El porqué está escrito donde se decide, no escondido.

---

## 2. Las tres pantallas y sus estados

| Pantalla | Vacío | Carga | Error | Sin conexión | Solo lectura |
|---|---|---|---|---|---|
| **Entrada** `/compra/listas` | el existente + **typeahead usable** | `Cargando`/esqueleto, sin parpadeo del combo | `Fallo` con reintentar; el combo tiene su propio error | **nuevo** aviso + búsqueda en lo último traído | **nuevo**: no ofrece apuntar |
| **Listado** `/compra` | los tres vacíos de siempre | `Esqueleto filas={6}` | `Fallo titulo="No he podido buscar"` | **nuevo** aviso («enseño lo último que busqué») | n/a |
| **Comparativa** `/compra/listas/:id/comparar` | los tres `Vacio` distintos | `Cargando que="la comparación"` | `Fallo` con salida | **nuevo** aviso («un precio de ayer es un dato, no un error») | `puedeEscribir` sigue mandando |

Los vacíos, cargas y errores que ya estaban **no se reescribieron**: se comprobaron y se midieron.

---

## 3. Medición 390 × 844 (y 1440 × 900)

Instrumento: `plataforma/web/app/scripts/medir-ui-cesta.mjs` (CDP crudo contra Edge headless),
adaptación declarada de `F:\\Inforepositorios\\scripts\\medir-ui-movil.js`. Antes: 13:50;
después: 17:52 (hora local del fichero). Sin errores de consola ni respuestas de API que no sean
2xx en ninguna ruta.

### 3.1 390 × 844

| Ruta | Scroll horizontal | Primer contenido (`y`) | Filas visibles | €/ud en pantalla | Textos «cortados» |
|---|---|---|---|---|---|
| `/compra` | **no** | 89 | 2 de 40 | 2 | 3 (todos `sr-only`) |
| `/compra/listas` | **no** | 89 | — | 0 (6 en el DOM) | 1 (`sr-only`) |
| `/compra/.../comparar` | **no** | 89 | — | 0 (25 en el DOM) | 0 |

- **Typeahead medido** en `/compra/listas`: `existe: true`, etiqueta **«Añadir a la lista»**,
  `top: 319`, `enPantalla: true`, no es de solo lectura. Dentro de la banda útil
  (109…787, con cabecera de 69 y barra inferior de 57).
- **Nada de scroll horizontal**: `scrollWidth === clientWidth` en las tres.
- **Texto cortado**: la medida cuenta 3 en `/compra`, 1 en `/compra/listas` y 0 en la
  comparativa; **todos son `sr-only`** (etiquetas para lector de pantalla, ocultas a propósito),
  no truncamientos de contenido visible.
- **€/kg**: 2 ejemplos visibles sin desplazar en el listado a 390 px; en la sugerencia del
  typeahead la prueba comprueba `0,66 €/l` en la opción, no solo en la fila.

### 3.2 1440 × 900

| Ruta | Scroll horizontal | Primer contenido (`y`) | Filas visibles | Typeahead |
|---|---|---|---|---|
| `/compra` | no | 83 | 5 de 40 | no aplica |
| `/compra/listas` | no | 83 | — | `top: 261`, en pantalla |
| `/compra/.../comparar` | no | 83 | — | no aplica |

### 3.3 Criterios de §6, uno a uno

1. **Sin scroll horizontal** — 6 de 6 rutas × viewport. ✅
2. **Primer contenido en la banda útil** — el primer bloque con texto arranca a `y=89`
   (20 px bajo la cabecera de 69) y el primer dato está dentro de la banda: primeras filas
   visibles en `/compra` y typeahead a 319 en `/compra/listas`. ✅
3. **Nada de texto cortado** — solo etiquetas `sr-only`; nombre de producto y cadena truncan con
   `truncate` o caben. ✅
4. **€/kg visible sin desplazar** — sí en el listado (2) y en la sugerencia (prueba). ✅
5. **Objetivos ≥ 44 px y campos ≥ 16 px** — `tests/test_ui_movil.py`: **15 passed**; el campo
   nuevo mide `min-h-[44px]`. ✅

Capturas (antes / después), 9 + 9:

```text
capturas/ui-antes-{compra,listas,comparar}-{390x844,1440x900}.png          (+ 3 «completa» móvil)
capturas/ui-despues-{compra,listas,comparar}-{390x844,1440x900}.png        (+ 3 «completa» móvil)
```

Destacan `ui-despues-listas-390x844.png` (el typeahead dentro de la lista) y la pareja
`ui-antes-listas-390x844.png` / `ui-despues-listas-390x844.png`.

---

## 4. Puertas (salida real, no «debería»)

```text
$ npx vitest run
 Test Files  28 passed (28)
      Tests  314 passed (314)          [exit 0]

$ npm test                            # node --test "tests/**/*.test.mjs"
 ℹ tests 404  ℹ pass 404  ℹ fail 0   [exit 0]

$ npx tsc --noEmit
 (sin salida)                          [exit 0]

$ npm run build                       # tsc + vite build + sella-sw
 ✓ built in 8.10s
 sella-sw: version 2026111316, 41 trozos precacheados   [exit 0]

$ ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_ui_movil.py
...............                           [100%]
15 passed in 5.05s                                         [exit 0]
```

`-p no:cacheprovider` es obligatorio: `.pytest_cache` tiene la ACL rota en esta máquina y pytest
no puede escribir ahí; sin la bandera se cae antes de empezar.

**Suite completa de Python** (misma bandera), con dos pruebas dependientes del disco
**deseleccionadas** y el porqué:

```text
$ ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider \
    --deselect tests/test_fase2_f05_ficha_carrefour.py::test_contra_la_ficha_real \
    --deselect tests/test_fase2_f05_ficha_mercadona.py::test_contra_el_crudo_real
1503 passed, 813 skipped, 2 deselected, 2 warnings in 143.16s   [exit 0]
```

- `test_contra_la_ficha_real` (Carrefour): recorre los 58.760 `.json.gz` de `data/raw` y en esta
  máquina pasa de 10 minutos (comando cortado a los 10; ya documentado en
  `docs/COBERTURA-DIARIA-2026-11-04.md` §8).
- `test_contra_el_crudo_real` (Mercadona): leyó un crudo real y falló por un dato del propio crudo
  («ingredientes sospechosamente cortos: 'Anís'»), no por este cambio. **Ninguna de las dos toca la
  UI.** Con las dos dentro: `1 failed, 1503 passed, 813 skipped` (el fallo es el de Mercadona).

Instrumento de medida comprobado: `node --test scripts/prueba-medicion.test.mjs` → **6/6**.

---

## 5. Auditoría de diseño

### 5.1 `ai-design-check` (MIT)

Paquete: `@enmera/ai-design-check` (npm). Se pasa sobre lo **nuevo** y sobre `src/` entero.

```text
$ npx -y @enmera/ai-design-check src/componentes/ui-sdk src/componentes/SinConexion.tsx src/estado/conexion.ts
Style (4)
  SeleccionMultiple.tsx  88  warn  Plurals through the plural system: === 1 ? 'línea' : 'líneas'
  Typeahead.tsx         110  warn  Raw <input>: use <Input>
  Typeahead.tsx         177  warn  Raw <button>: use <Button>
  Typeahead.tsx         188  warn  Plurals through the plural system: === 1 ? 'resultado' : 'resultados'
0 accessibility, 4 style: 0 errors, 4 warnings, 0 notes.   [exit 0]
```

**0 errores** en el código nuevo. Los 4 avisos, explicados:

- **`raw <input>` / `raw <button>`**: el input es el de **solo lectura** (necesita `role="combobox"`
  + `aria-disabled` y no lleva el componente de campo porque no se escribe), y el botón es el
  `Reintentar` **dentro de la capa** del combo, no un botón de página. Los dos están en el DOM por
  una razón y no por no usar el componente compartido.
- **plurales**: el copy exacto lo fijan las pruebas y el resto de la app usa el mismo patrón
  («1 línea seleccionada» / «3 líneas»). Cambiarlo por el sistema de plurales es una pasada de
  copy que no toca este encargo.

Línea base **heredada** de `src/` (no de esta pasada):

```text
$ npx -y @enmera/ai-design-check src
1 accessibility, 434 style: 108 errors, 293 warnings, 34 notes.
```

Son 108 errores de `text-[Npx]` (tamaños fuera de la escala) y avisos de componentes compartidos
**que ya existían** en 30 pantallas. No se tocan aquí: la pasada no rediseña el resto de la app y
el cambio de escala tipográfica es un encargo propio.

### 5.2 `unslop` (CC-BY-4.0, método, con atribución)

`unslop` **no tiene punto de entrada ejecutable** (es una habilidad de agente en texto): se aplica
el **método** —auditar los signos, fijar dirección, corregir por pasadas— sobre lo nuevo:

| Signo de *slop* | Lo nuevo |
|---|---|
| Degradados, resplandores, glass | **ninguno** añadido |
| Emojis como texto de interfaz | **ninguno** nuevo (el `🎤` de `/compra` es preexistente, es un icono con `aria-label`) |
| Etiquetas gritonas / decorativas en mayúsculas | solo `text-micro uppercase` de las secciones existentes; en lo nuevo, `text-etiqueta` normal |
| Texto de relleno («potencia tu compra») | **cero**: el copy nuevo dice qué pasa («No he podido buscar», «Te la compartieron para mirar») |
| Espaciado y escala | 4/8/12/16/24 px y los tokens del sistema «Cesta App»; no se añadió ni un color/radio/sombra |
| Dirección | la que ya tiene el producto (verde bosque, serif de titulares, cifras tabulares); no se importó ninguna moda |

Hallazgos: ninguno grave. Con atribución: método de <https://github.com/heydamir/unslop>
(CC-BY-4.0), reimplementado con palabras propias; no se copió ningún fichero de la habilidad.

---

## 6. Cómo reproducir

```bash
# 1) API y web de la plataforma (Docker Desktop levantado)
cd plataforma && docker compose up -d          # Caddy en :8080

# 2) Vite de desarrollo apuntando a Caddy (la cookie de sesión queda en el mismo origen)
cd plataforma/web/app
CESTA_API=http://127.0.0.1:8080 npx vite --port 5173

# 3) Medición (la misma que produjo medicion.json)
CESTA_WEB=http://localhost:5173 CESTA_PREFIJO=ui-despues \
  node scripts/medir-ui-cesta.mjs

# 4) Puertas
npx vitest run && npm test && npx tsc --noEmit && npm run build
cd ../../.. && ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_ui_movil.py
```

`CESTA_PREFIJO=ui-antes` produce la tanda «antes» (la que está en `medicion-antes.json` y
`capturas/ui-antes-*`).

---

## 7. Lo que queda fuera (dicho, no escondido)

- **Typeahead sobre los resultados de `/compra`** (§3.2 del contrato): no se montó. El listado ya
  tiene su buscador con 250 ms; poner un segundo campo de búsqueda encima de sus resultados
  duplicaba la pregunta. Queda como siguiente paso con su propia medición.
- **Virtualización**: el umbral es 21 líneas. La lista de la casa del caso real tiene 6, así que
  **la medición de la comparativa no cambia** con esto; lo que lo prueba es la unidad
  (`ListaVirtualizada.test.tsx`: 60 filas → 12 pintadas, `aria-setsize`/`posinset`, teclado) y la
  ruta >20 que queda montada.
- **Ojos frescos** (§7.5): no se pudo hacer; esta sesión corre sin subagentes. Se compensa con
  `ai-design-check` (0 errores en lo nuevo) y la medición.
- **Suite de Python**: 2 pruebas dependientes del disco deseleccionadas (arriba, con motivo).
- **`/compra` typeahead y escala tipográfica** de las 30 pantallas heredadas: fuera de alcance.

---

## 8. Ronda 2 — revisión de la pantalla de compra/listado a 390 px

Revisión externa (Codex) sobre `/compra`: los controles ocupaban más de media pantalla y a 390 px
apenas se veían dos productos; el porcentaje del grupo no decía cuánto dinero es; y no había
forma de ver el mismo producto cadena a cadena. Medición propia antes/después con el mismo
instrumento: **`medicion-r2-antes.json`** (build de la entrega anterior servido por Caddy, :8080)
y **`medicion-r2-despues.json`** (Vite con el código nuevo, :5173). Capturas `ui-r2-antes-*` y
`ui-r2-despues-*` (12 + 12).

### 8.1 Qué se cambió, por impacto

| Antes | Después | Por qué |
|---|---|---|
| El panel «Filtros» se daba por cerrado, pero su contenido seguía pintado **flotando sobre los resultados**: los campos del panel caían encima de las filas y tapaban **20 controles** a 390 px | Panel **de verdad plegado** (estado + render condicional, no `<details>`): cerrado no deja nada en el flujo. Cadenas, pasillo, dieta, ofertas, conservación y número de resultados viven **dentro** | Un `<details>` cerrado daba `open=false` pero el `display` de las utilidades de Tailwind dejaba el contenido en su sitio. Medido: 20 controles tapados y 450 px de controles antes del primer producto |
| Las cadenas eran una fila **siempre visible** encima de los resultados, y «Guardar estos filtros» otra | Las cadenas están **dentro de Filtros**; «Guardar estos filtros» pasa a **segundo plano** (dentro del panel); los filtros puestos se ven como **chips** que se quitan de uno en uno, con «Quitar todos» | Cada fila de controles es una fila de producto que no se ve. Los chips dicen **cuál** es el filtro, no solo cuántos |
| Cada producto arrastraba foto, marca, Nutri-Score, eco-score, sellos, ofertas y «hasta 2,09 €/l» | Cada fila enseña **nombre, supermercado, precio de venta y precio por unidad**; el resto queda en la ficha del producto | En 390 px cada sello es una línea más y lo que se viene a mirar es el precio. **El precio de venta y el €/kg siguen juntos**, que es lo que la revisión pide no tocar |
| «Hasta un 117,7 % en el grupo» (porcentaje del grupo de equivalencias) | **«0,66 €/l menos que el más caro»**: diferencia en euros **con la misma unidad**, solo si el grupo es comparable y no dudoso | Un porcentaje no dice cuánto dinero es y se lee como «lo que te ahorras comprando este». Con la misma unidad, la diferencia es una cantidad comparable; sin abanico no se pinta nada |
| No había forma de ver el mismo producto en cada supermercado desde el listado | **«Ver ofertas por supermercado»** en cada fila: despliega el grupo entero (una fila por cadena) **ordenado por precio por unidad**, pidiéndolo al abrir y con la diferencia total del grupo al pie | La lista enseña el más barato de cada producto, pero no **dónde**. Ordenar por €/unidad y no por precio de venta es la comparación que la app existe para hacer (un pack más caro puede ser más barato por kilo) |

### 8.2 Medición (móvil 390 × 844)

| Ruta | Control tapado | Controles hasta el 1.º producto | Productos visibles | €/ud en pantalla | Chips |
|---|---:|---:|---:|---:|---|
| `/compra` **antes** | **20 / 35** | **450 px** | **2 de 40** | 2 | — |
| `/compra` **después** | **0 / 12** | **282 px** | **4 de 40** | 7 | — |
| `/compra` con filtro **antes** | 0 / 22 | 1.370 px | 0 de 35 | 0 | — |
| `/compra` con filtro **después** | **0 / 14** | **338 px** | **4 de 35** | 4 | `DIA ×`, `Quitar todos` |
| `/compra/listas` (sin cambios) | 0 / 14 | — | — | — | — |
| `/compra/.../comparar` (sin cambios) | 0 / 1 | — | — | — | — |

Escritorio 1440 × 900: `/compra` pasa de 14/44 controles tapados a **0/16**; con filtro, de 42 a 18
controles y de 1 a 7 productos visibles. Sin scroll horizontal en ninguna ruta.

**La acción nueva, pulsada de verdad** (el instrumento pulsa el primer «Ver ofertas por
supermercado» y lee el panel):

```text
antes:  {"hayBoton": false, "hayPanel": false}
después: {"hayBoton": true, "hayPanel": true,
  "filas": ["Aldi … 0,96 € 0,96 €/l", "Carrefour … 0,96 € 0,96 €/l",
            "Mercadona … 0,96 € 0,96 €/l", "DIA … 1,09 € 1,09 €/l",
            "Alcampo … 2,09 € 2,09 €/l"]}
```

**Una fila por supermercado** (el formato más barato por unidad de cada cadena) y orden no
decreciente por €/unidad (0,96 → 1,09 → 2,09), que es lo que promete la acción. *La captura se
toma con el panel plegado otra vez: la foto es de la pantalla, no del desplegable.*

### 8.3 Puertas de la ronda 2

```text
npx vitest run                 →  29 ficheros / 319 tests passed      [exit 0]
npm test                       →  tests 404 / pass 404 / fail 0    [exit 0]
npx tsc --noEmit               →  sin salida                        [exit 0]
npm run build                  →  ✓ built in 7.75 s · sella-sw 41 trozos   [exit 0]
pytest tests/test_ui_movil.py -p no:cacheprovider  →  15 passed in 3.41 s  [exit 0]
pytest suite completa -p no:cacheprovider (2 deselect)  →  1503 passed, 813 skipped, 2 deselected, 2 warnings in 182.72 s  [exit 0]
node --test scripts/prueba-medicion.test.mjs  →  tests 6 / pass 6 / fail 0  [exit 0]
ai-design-check (ficheros de la ronda)  →  0 errores, 23 avisos heredados/explicados  [exit 0]
```

Los avisos de `ai-design-check` son los patrones que ya estaban en esos ficheros (`raw <button>`,
`uppercase tracking-wide`, plurales a mano); la ronda no añade errores. Las 2 pruebas Python
deseleccionadas son las que dependen de `data/raw` (Carrefour recorre 58.760 `.json.gz` y pasa de
10 minutos; Mercadona depende del crudo real del día), con el motivo explicado en §4.

Pruebas nuevas: `src/paginas/Buscar.test.tsx` (5) — cadenas y guardar dentro de Filtros, chips,
los cuatro datos por fila, la diferencia en euros, el despliegue ordenado por €/unidad y el caso
sin comparación fiable.

### 8.4 Codex CLI sobre la captura (14/11, 10:00)

Revisión de `capturas/ui-r2-despues-compra-390x844.png` con
`codex exec --sandbox read-only -i` (modelo `gpt-6.1-sol`), dos pasadas. La primera devuelve tres
hallazgos; la segunda, sobre la captura ya corregida, solo uno:

| Hallazgo | Qué se hizo | Por qué |
|---|---|---|
| «Dos filas de Carrefour con el mismo nombre y precio parecen duplicadas» | **Aplicado**: el panel despliega **una fila por supermercado**, con el formato más barato por unidad de cada cadena. Medido: el panel pasa de **6 a 5 filas** (Aldi, Carrefour, Mercadona, DIA, Alcampo), y `Buscar.test.tsx` fija el caso de dos formatos en una cadena | Era ruido real en la captura: el grupo tiene dos formatos de Carrefour y se pintaban los dos. Una fila por cadena es lo que promete la acción |
| «La acción de ofertas es un enlace pequeño y poco visible» | **Aplicado**: «Ver ofertas por supermercado» pasa de enlace subrayado a **botón con borde y 44 px** (misma altura, más visible) | La revisión pide una acción visible; el enlace se perdía entre la fila. La medición sigue en **0 controles tapados (0/12)** |
| «La diferencia en euros destaca en turquesa y compite con el precio» | **Aplicado a medias**: se mantiene la diferencia (la pide el punto 3 de la revisión) pero **pasa a color secundario**, sin acento verde | El dato es obligatorio; su jerarquía no. El precio de venta y el €/unidad siguen siendo lo que manda |
| «La búsqueda de “leche entera” devuelve “Chocolate con leche Valor almendras enteras”» | **Descartado para esta pantalla**: es relevancia del buscador (matching del catálogo), no maquetación | Arreglarlo es del motor de búsqueda y sus umbrales, no de la pantalla de compra; queda anotado como siguiente paso de datos, no se toca aquí para no cambiar resultados bajo una revisión de UI |

Segunda pasada, sobre la captura actualizada: solo devuelve el hallazgo de relevancia y añade
«No veo otros problemas relevantes claramente demostrables en esta captura».

---

## 9. Ronda 3 — entrada `/compra/listas`: typeahead, selección y estados (390 × 844)

Pieza cerrada sobre la pantalla de entrada: los dos gestos del encargo ejercitados con **teclado de
verdad** (el instrumento escribe con `Input.insertText` y pulsa con `Input.dispatchKeyEvent`, no con
`element.click()`), y los tres estados medidos **generándolos de verdad** (interceptando `fetch` de
`/api/listas` antes de arrancar la app: `[]` para vacío, 500 para error, 5 s de retardo para carga).

Medida: `medicion-entrada.json`, generada con
`CESTA_ENTRADA=1 node scripts/medir-ui-cesta.mjs`. Capturas:
`capturas/ui-entrada-{normal,vacio,carga,error}-390x844.png`.

| Estado | Qué se pinta | Scroll H | Controles tapados | Typeahead |
|---|---|---:|---:|---|
| **Normal** (La casa, 6 líneas) | lista, precio estimado y typeahead | no | **0 / 14** | sí: `top=319`, etiqueta «Añadir a la lista» |
| **Vacío** (sin listas) | «No tienes ninguna lista» + typeahead que apunta en la de casa | no | **0 / 5** | sí: `top=130` |
| **Carga** (listas lentas) | «Cargando tus listas…» | no | **0 / 0** | no: no se monta hasta tener lista |
| **Error** (listas a 500) | «No he podido traer tus listas» + «Volver a intentarlo» | no | **0 / 1** | no |

**Typeahead con teclado** (estado normal): se escribe «leche» → `aria-expanded=true`, **8
sugerencias**, la primera con su **€/unidad** (`0,79 €/l`); `Escape` cierra la lista
(`aria-expanded=false`) y **conserva el texto** «leche» (no lo borra).

**Selección accesible** (estado normal): «Elegir varias líneas» abre un `role="listbox"` con **6
opciones**; `Espacio` marca la primera (`aria-selected=true`) y la barra dice «1 línea seleccionada»;
`Escape` sale de la selección y devuelve el botón.

Puertas de la pieza (solo cambia el instrumento y los documentos; `src/` no se toca):

```text
node --check scripts/medir-ui-cesta.mjs           →  OK
node --test scripts/prueba-medicion.test.mjs      →  tests 6 / pass 6 / fail 0   [exit 0]
npx vitest run                                    →  29 ficheros / 319 tests passed  [exit 0]
pytest tests/test_ui_movil.py -p no:cacheprovider →  15 passed in 3.95 s        [exit 0]
```

La decisión de producto que desbloquea esto (datos en el dispositivo con IndexedDB y demo con
muestra pequeña incrustada) queda anotada en `DECISIONES.md` (2026-11-14). El almacén local es la
siguiente pieza; esta ronda cierra la pantalla y su medición.

---

## 10. Demo publicada en GitHub Pages (14/11/2026)

**Publicada:** <https://erdeivih.github.io/cesta-demo/> → **HTTP 200** (14/11/2026).
Repositorio: <https://github.com/ErDeivih/cesta-demo>, público, Pages desde la rama `gh-pages`
(`status: built`). Guía de publicación y límites: `docs/DEMO-PAGES.md`.

| Qué | Cómo |
|---|---|
| Datos | **muestra incrustada** de 130 KB, capturada de la API el 13/11: 1 lista de 6 líneas, reparto por cadenas, 120 resultados de búsqueda y 6 grupos con sus precios |
| Sin servidor | `src/demo/api.ts` responde a `/api/*`; la app se compila en modo `demo` (`npm run build:demo`, base `/cesta-demo/`) |
| Rutas | en el **hash** (`#/compra/listas`), para que Pages no tenga que resolver rutas profundas |
| Estados | `?demo=vacio`, `?demo=carga` y `?demo=error` los sirve la propia demo, sin servidor |
| Escribir | se guarda en **IndexedDB** en el dispositivo y sobrevive a recargar; `?demo=reset` vuelve a la muestra |

Medición de la **URL publicada** con el mismo instrumento, a 390×844 y 1440×900
(`medicion-demo-pages.json`, capturas `capturas/ui-demo-pages-*`):

| Ruta / estado | Scroll H | Controles tapados | Dato a 390×844 |
|---|---:|---:|---|
| `/compra` | no | **0 / 14** | 4 productos visibles, 7 precios por unidad en pantalla |
| `/compra` con filtro | no | **0 / 14** | 3 productos visibles, chips `DIA ×` / `Quitar todos` |
| `/compra/listas` | no | **0 / 14** | typeahead «Añadir a la lista» en `top=319` |
| comparativa | no | **0 / 1** | resumen y totales, sin scroll horizontal |
| entrada **vacía / carga / error** | no | 0/5 · 0/0 · 0/1 | «No tienes ninguna lista» / «Cargando tus listas…» / «No he podido traer tus listas» |

Typeahead y selección en la demo publicada, con teclado real: al escribir «leche» salen **8
sugerencias** con €/unidad (`0,96 €/l`), `Escape` cierra **conservando el texto**; «Elegir varias
líneas» abre un `role=listbox` de **6 opciones**, `Espacio` marca (`aria-selected=true`, barra «1
línea seleccionada») y `Escape` sale devolviendo el botón.

**Datos en el dispositivo, comprobado contra la URL publicada** (Edge headless): 6 líneas en la
muestra → añadir una (`POST /api/listas/{id}/lineas`, **200**) → **7** → recarga completa →
**7** con «Producto de prueba (demo)» al final → `?demo=reset` + recarga → **6**. La demo guarda
en **IndexedDB** (`src/demo/almacen.ts`); la medición se rehízo contra el build con persistencia.

**Lo que no se publica tal cual, y se dice:** las pantallas fuera de la compra (panel, recetas,
ajustes) no tienen muestra y se quedan en su estado vacío/error; los precios son de la captura del
13/11 y no se actualizan; lo escrito se guarda **en este navegador** (IndexedDB) pero no se
sincroniza entre dispositivos. Para la sincronización hace falta la API en el servidor, que es la
decisión anotada en `DECISIONES.md`.
