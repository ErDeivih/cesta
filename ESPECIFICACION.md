# Especificación de interfaz — Cesta (pasada UI del 13/11/2026)

Contrato de esta pasada. Se escribe **antes** de tocar píxeles, como manda
`F:\Inforepositorios\ENCARGO-UI-COORDINADOR.md` §Protocolo. Lo que no esté aquí no se hace;
lo que esté aquí se mide.

- Documento de pantallas que ya existe y **no se reescribe**: `docs/PANTALLAS.md`,
  `docs/USABILIDAD.md`, `docs/UX-MOVIL.md`. Esta pasada no los contradice: los cumple y
  rellena el hueco que dicen que hay.
- Sistema de diseño aprobado: `designs/cesta-app-design-system/project/` (tokens claro/oscuro,
  92 parejas AA medidas). **Los tokens ya viven en `plataforma/web/app/src/estilos.css` y no se
  reinventan**: esta pasada no añade ni un color, radio, sombra o espaciado nuevo.
- app: `plataforma/web/app` (Vite + React 19 + TS + Tailwind 3), PWA móvil, 390 px primero.

## 1. Alcance

Tres pantallas clave, con sus estados. El resto de la app hereda y **no se toca**.

| # | Pantalla | Ruta | Qué tiene que resolver |
|---|---|---|---|
| 1 | Entrada de la cesta | `/compra/listas` | entrar y ponerse a apuntar sin salir de la pantalla |
| 2 | Listado con €/kg | `/compra` | buscar, ver el precio por unidad y decidir |
| 3 | Comparativa por cadena | `/compra/listas/:listaId/comparar` | ver qué cadena gana y por qué |

Fuera de alcance (no se toca en esta pasada): lógica de negocio, API, datos, ingesta,
permisos, `docs/PANTALLAS.md`, el catálogo de `F:\Inforepositorios`, y las otras 30 rutas de
la app más allá de heredar los componentes nuevos.

## 2. El hueco que se cierra (y por qué es este)

Medido sobre `src/` el 13/11/2026, antes de nada:

| Comportamiento | Estado real hoy | Consecuencia |
|---|---|---|
| Typeahead (combobox con lista de sugerencias) | **no existe**: `Buscar.tsx` es un `<input>` a pelo con 250 ms de retardo; `PegarEnLaLista` pide candidatos por línea y los pinta como botones sueltos | se escribe a ciegas: ni flechas, ni `aria-activedescendant`, ni decir cuántos resultados hay |
| Selección accesible múltiple | `Casilla` por línea (bien etiquetada, `htmlFor` + `useId`), pero **no hay** patrón listbox ni acciones en lote | tachar es un gesto por línea; no se puede «quitar tres de golpe» con teclado |
| Foco en lo que se abre | sólo `Suite.tsx` tiene `role="dialog"`/`aria-modal`; las hojas de la lista (cuenta, cerrar compra, compartir) **no atrapan ni devuelven el foco** | con teclado, el foco se va detrás de la hoja y no vuelve a donde estaba |
| Virtualización | **no existe**: la comparativa pinta todas las líneas y el listado pinta toda la página | con 60 líneas y 60 filas por cadena, el móvil paga el primer pintado entero |

Esto es exactamente lo que el encargo llama «el hueco real» y lo que
`indice/PLAN-UI-PROYECTOS.md` línea 29 pide para Cesta: *«formularios y listas grandes con
`ui-sdk` (typeahead, selección), estados de carga y error en cada pantalla»*.

Pieza elegida: **`vercel-labs/ui` → `@ui-sdk/core` + `@ui-sdk/react` 0.1.0-beta.1,
Apache-2.0** (ficha `repos/vercel-labs--ui/FICHA.md`). Límite declarado en la ficha:
evidencia **documental**, sin pruebas de nadie; es beta. Por eso cada behavior se prueba
aquí con vitest antes de entrar en una pantalla, y si un behavior no hace lo que promete se
implementa a mano **diciéndolo**, no disimulándolo.

## 3. Las tres pantallas, con todos sus estados

Reglas comunes a las tres (van en el contrato porque hoy no se cumplen siempre):

- **Cuatro estados por pantalla, siempre**: vacío, carga, error y **sin conexión**. El de
  «sin permiso» (`papel: 'mira'`) es un quinto estado donde existe escritura: se dice qué no
  se puede hacer y por qué, no se esconde el botón.
- **Nada de pantalla en blanco**: la carga es esqueleto con la forma de lo que viene.
- **El error dice qué falló, si se puede reintentar y con qué botón**. «Algo salió mal» no
  vale.
- **El vacío dice qué es esto, por qué está vacío y cuál es el siguiente paso** (un botón).
- **Foco visible siempre** (`:focus-visible` ya usa `ring-verde`), `Escape` cierra lo que se
  abre, `Enter` confirma, el foco vuelve a quien lo abrió.
- **Objetivos ≥ 44 px** y campos ≥ 16 px (los vigila `tests/test_ui_movil.py`).

### 3.1 Entrada de la cesta — `/compra/listas`

Qué es: la pantalla a la que se llega para apuntar la compra. Hoy, sin `:listaId`, enseña
**tus listas** (`misListas`), el alta/entrada de sesión y «nueva lista».

| Estado | Hoy | Lo que tiene que pasar en esta pasada |
|---|---|---|
| Vacío | `Vacio` con el alta de cuenta o «no tienes listas» | igual, pero **con el buscador de productos ya usable**: apuntar no exige crear una lista antes ni salir a `/compra` |
| Carga | `Cargando que="tus listas"` | se mantiene; el typeahead no parpadea mientras carga (no se monta hasta que hay lista) |
| Error | `Fallo` con `reintentar` | igual, y el typeahead muestra su propio error de red sin tumbar la pantalla |
| Sin conexión | **no hay estado** | **aviso** «Sin conexión: lo que apuntes se guarda en el móvil y sube al volver» + el typeahead trabaja contra la caché local de lo ya visto, no contra la red |
| Sin permiso | no aplica a listas propias | en una lista compartida de sólo lectura, el typeahead no ofrece «añadir» |

Gesto nuevo: **typeahead de producto en la propia pantalla** (`Typeahead` de `ui-sdk`), que
sustituye el callejón sin salida de hoy — `Cesta.tsx:2218` manda a `/compra` con un `<Link>`
«Añadir producto», o sea **salir de la lista para buscar**. Al elegir un producto, se añade
con `anadirLinea` y el foco se queda en el campo para seguir apuntando.

Copy aprobado (corto, sin «eyebrows»): campo `Añadir a la lista`; vacío del combo
`Sin resultados para «…»`; carga `Buscando…`; error `No he podido buscar. Reintentar`.

### 3.2 Listado con €/kg — `/compra`

Qué es: el buscador de productos y su listado, con precio, cadena y **precio por unidad**
(€/kg, €/l, €/ud). Ya tiene filtros (`FiltrosBusqueda`), cadenas encima de los resultados,
tabla que se apila en móvil y página.

| Estado | Hoy | Lo que tiene que pasar |
|---|---|---|
| Vacío | `Vacio` «Escribe al menos dos letras, o elige un pasillo» + ejemplos | igual, y el typeahead enseña **sugerencias mientras se escribe** (hasta 8) con nombre, cadena y €/kg |
| Carga | `Esqueleto filas={6}` a los 250 ms | igual, y el combo dice «Buscando…» en el `aria-live` en vez de quedarse mudo |
| Error | `Fallo titulo="No he podido buscar"` | igual; el combo ofrece reintentar sin perder el texto escrito |
| Sin conexión | **no hay estado** | **aviso** «Sin conexión: enseño lo último que busqué» y resultados de la última consulta cacheada; si no hay nada, vacío con salida |
| Sin resultados | tres vacíos distintos (con filtros / sin filtros / pasillo vacío) | se quedan: son la distinción correcta |

Gesto nuevo: **typeahead accesible sobre los resultados** — `role="combobox"`, `aria-expanded`,
`aria-controls`, `aria-activedescendant`, flechas ↑↓, `Home`/`End`, `Enter` para abrir la
ficha, `Escape` para cerrar la lista sin borrar el texto escrito. Hoy el campo no anuncia nada
de eso. El €/kg se queda **en la fila y en la sugerencia**: es la decisión de compra.

### 3.3 Comparativa por cadena — `/compra/listas/:listaId/comparar`

Qué es: el total de la lista en cada cadena, quién gana, cuánto se ahorra y qué le falta a
cada una. Ya tiene: resumen (3 cifras), `QuienGana`, `AhorroDeLaCesta`, `LaMejorCompra`,
`ComoSeCalcula`, `CadenaEnLaLista`, `LineaComparada`, `CalculadoraDeEnvases`,
`BuscarAlternativa`.

| Estado | Hoy | Lo que tiene que pasar |
|---|---|---|
| Vacío | tres `Vacio` distintos: lista sin nada, hoy sin comparar, todavía sin precios | se quedan tal cual: están bien escritos y son distintos a propósito |
| Carga | `Cargando que="la comparación" filas={6}` | igual, y **la lista de líneas se virtualiza**: no se pinta lo que no se ve |
| Error | `Fallo` con salida | igual |
| Sin conexión | **no hay estado** | **aviso** + se enseña la última comparación guardada con su **fecha de datos** (`fechaDatos` ya existe en la cabecera): un precio de ayer es un dato, no un error |
| Sin permiso | `puedeEscribir` gatea «buscar alternativa» | se queda, y el motivo se dice en una línea cuando no se puede |

Gestos nuevos, los dos que hoy no existen:
1. **Selección accesible múltiple** de líneas (`SeleccionMultiple`): `role="listbox"`,
   `aria-selected`, `Espacio` marca, `Shift+Espacio` rango, `Ctrl/Cmd+A` todas, barra de
   acciones en lote con el número («3 líneas seleccionadas»), y salir de la selección con
   `Escape`. Uso real: quitar varias líneas o buscar alternativa solo en las marcadas.
2. **Virtualización** (`ListaVirtualizada`): ventana con overscan sobre las líneas, filas de
   altura fija, `aria-setsize`/`aria-posinset` para que el lector de pantalla sepa cuántas hay
   aunque sólo estén 12 en el DOM, y scroll por teclado con el foco dentro.

## 4. Piezas de comportamiento (y dónde van)

| Pieza | Fichero | Se usa en |
|---|---|---|
| `Typeahead` | `src/componentes/ui-sdk/Typeahead.tsx` | 3.1 entrada de cesta, 3.2 listado |
| `SeleccionMultiple` | `src/componentes/ui-sdk/SeleccionMultiple.tsx` | 3.3 comparativa |
| `Foco` (trampa + retorno) | `src/componentes/ui-sdk/Foco.tsx` | hojas de 3.1 y 3.3 |
| `ListaVirtualizada` | `src/componentes/ui-sdk/ListaVirtualizada.tsx` | 3.3 comparativa |

Base: `@ui-sdk/core` + `@ui-sdk/react` 0.1.0-beta.1 (Apache-2.0). Cada pieza lleva escrito
qué behavior del paquete usa y, si no lo usa, por qué.

## 5. Tokens y componentes base

- Tokens: los de `estilos.css` (§LOS TOKENS DEL SISTEMA «CESTA APP»), copiados de
  `designs/cesta-app-design-system/project/tokens.css`. **No se añade ninguno.**
- Componentes base: los de `src/componentes/ui.tsx` (`Boton`, `CampoTexto`, `Tarjeta`,
  `Etiqueta`, `Aviso`, `Cargando`, `Esqueleto`, `Fallo`, `Vacio`, `Resumen`, `TablaScroll`,
  `Th`, `Td`). Lo nuevo **compone** con ellos, no los duplica.
- Espaciado = escala Tailwind 4/8/12/16/24/32/48; radios de token (`--radio-campo`,
  `--radio-tarjeta`, `--radio-hoja`); movimiento con `--movimiento-duracion-*`.

## 6. Medición (criterio de aceptación numérico)

Instrumento: `plataforma/web/app/scripts/medir-ui-cesta.mjs`, adaptación declarada de
`F:\Inforepositorios\scripts\medir-ui-movil.js` (CDP contra Edge headless), a **390×844** y
**1440×900**. Salidas: `medicion.json` y `capturas/ui-*.png` en la raíz del proyecto.

Criterios, por pantalla y viewport:

1. **Sin scroll horizontal**: `documentElement.scrollWidth <= innerWidth`.
2. **Primer contenido visible** dentro de la banda útil: a 390×844 la cabecera mide ~109 px y
   la barra de abajo ~57, así que lo útil es **y ∈ [109, 787]**. El primer dato que se viene a
   leer (primera línea de la lista / primer resultado / primera cadena) tiene que empezar ahí.
3. **Nada de texto cortado**: nombre de producto y de cadena a una línea con elipsis **o**
   entero; nunca cortado a mitad sin `truncate`.
4. **€/kg visible** en el listado sin desplazar, y en la sugerencia del typeahead.
5. **Objetivos ≥ 44 px** y campos ≥ 16 px (ya hay prueba que lo vigila; la medición lo
   confirma en pantalla).

## 7. Puertas antes de dar esto por bueno

En este orden, y con la salida pegada en `UI-REPORT.md`:

1. `npx vitest run` (hoy **286** en verde; no puede bajar) y `npm test` (hoy **404**).
2. `npm run tipos` y `npm run build`.
3. `ai-design-check` (MIT) sobre `src/` — sin violaciones, o con las que queden explicadas.
4. Auditoría con el **método** `unslop` (CC-BY-4.0, con atribución): sin hallazgos graves.
5. Revisión de ojos frescos: un subagente sin historial ve la captura y contesta qué hace la
   pantalla y qué se puede hacer en ella.

## 8. No objetivos (dichos para no hacerlos)

- No se rediseñan las otras 30 pantallas: heredan.
- No se cambian datos, permisos ni lógica para que quede mejor.
- No se añaden animaciones decorativas ni gradientes por defecto.
- No se copian componentes de webs ajenas: se implementan.
- No se toca el catálogo de `F:\Inforepositorios`.
- No se sustituye Tailwind ni el sistema de tokens por otro.

## 9. Criterio de «terminado»

Las tres pantallas con sus estados implementados y medidos, las cuatro piezas con pruebas,
las puertas en verde, `UI-REPORT.md` con `Before | After | Why` y las capturas de antes y
después en `capturas/ui-*.png`, y este documento actualizado si algo cambió al hacerlo
(se anota el cambio, no se reescribe la historia).

## 10. Anexo de cierre (13/11/2026, 18:00) — lo que cambió al hacerlo

*No se reescribe nada de arriba; se anota lo que se movió y por qué.*

### 10.1 Dónde quedó cada pieza

| Pieza | Lo que decía §4 | Dónde quedó y por qué |
|---|---|---|
| `Typeahead` | 3.1 entrada y 3.2 listado | **3.1** `/compra/listas`, en sus dos caras (con listas y sin ninguna): es donde se apunta. En 3.2 no se montó: el listado `/compra` ya tiene su buscador propio y un segundo campo encima de los resultados duplicaba la pregunta; queda como siguiente paso, dicho también en `UI-REPORT.md` |
| `SeleccionMultiple` | 3.3 comparativa | **3.1/3.2, lista de la compra** («Elegir varias líneas» → quitar en lote). En la comparativa las filas se expanden (`<details>`) y un listbox con hijos interactivos dentro rompe el patrón; en la lista las filas son homogéneas y quitar varias es el gesto que faltaba |
| `Foco` (diálogo) | hojas de 3.1 y 3.3 | **cierre de compra de 3.1** («He terminado la compra»), que era un `Aviso` abierto, y **detalle de línea de 3.3** cuando la lista se pinta por ventana |
| `ListaVirtualizada` | 3.3 comparativa | **3.3 comparativa**, a partir de 21 líneas (`LINEAS_PARA_VIRTUALIZAR`): se pinta la ventana y el detalle se lee en un diálogo, porque con una fila expandida dejan de medir todas igual |

### 10.2 Comportamientos de `@ui-sdk` que se usan

- Typeahead: `Combobox` con `ComboboxInput/List/Item/Label/Trigger` (`@ui-sdk/react/combobox`) y `useAsyncOptions` (`@ui-sdk/react/async-options`): retardo, descarte de respuestas viejas, `aria-activedescendant` y teclado.
- Selección: `Listbox`/`ListboxItem` con `multiple` (`@ui-sdk/react/listbox`): `aria-multiselectable`, espacio, Mayús+espacio/rango, Ctrl+A.
- Foco: `Dialog`/`DialogContent`/`DialogTitle` (`@ui-sdk/react/dialog`); la entrada y el retorno del foco y la trampa de Tab son de la pieza, porque el diálogo se abre desde un botón de la pantalla y no desde un `DialogTrigger`.
- Virtualización: **no** usa `createVirtualizer` de `@ui-sdk/core`. Se dice en el propio fichero: `createVirtualizer` lee `clientHeight` del scroller y esta pieza recibe la ventana por prop (también en jsdom). Es la única de las cuatro que no delega.

### 10.3 Estados, y lo que se añadió

- **Sin conexión**: `SinConexion` montado en las tres pantallas. El aviso no bloquea, no promete «guardado» y dice qué pasa con lo apuntado.
- **Solo lectura**: el typeahead de una lista compartida para mirar no ofrece apuntar.
- **Error de búsqueda**: el combo dice qué falló y ofrece `Reintentar` sin perder el texto escrito.
- **Vacío, carga y error** de las pantallas: no se tocaron; siguen como estaban y se midieron.

### 10.4 Medición

- El instrumento nombra las capturas con `CESTA_PREFIJO` (`ui-antes` / `ui-despues`) y añade la medida `typeahead` (existe, etiqueta, `top`, `enPantalla`, solo lectura).
- «Antes» queda en `medicion-antes.json`; «después», en `medicion.json`. Las capturas de antes se conservan (`ui-antes-*`).
- A 390 × 844: sin scroll horizontal en las tres, primer contenido en `y=89` (por debajo de la cabecera de 69), y el typeahead a `y=319` — dentro de la banda útil.

### 10.5 Lo que no se hizo (dicho para que no se suponga)

- El typeahead sobre los resultados de `/compra` (§3.2) no se montó.
- La revisión de «ojos frescos» (§7.5) no se pudo hacer: esta sesión corre sin subagentes.
- `unslop` no tiene punto de entrada ejecutable (es una habilidad en texto, CC-BY-4.0): se aplicó el **método** y los hallazgos están en `UI-REPORT.md`.
- La suite de Python completa se corrió con dos pruebas dependientes del disco **deseleccionadas** (recorren `data/raw` de Carrefour y Mercadona y en esta máquina pasan de 10 minutos o dependen del crudo del día); el resto del suite es el que se pega en el informe.
