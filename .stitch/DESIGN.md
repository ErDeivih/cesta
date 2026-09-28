# Cesta · sistema de diseño

El lenguaje visual de las **dos superficies** del proyecto, en formato que Stitch puede consumir
(`stitch::manage-design-system` sube este fichero y aplica el tema a las pantallas;
`stitch::extract-design-md` es el que lo genera desde el código).

> **Estado:** escrito a mano el 27 de septiembre de 2026 a partir de
> `plataforma/web/app/src/estilos.css` (la aplicación) y `plataforma/aprende.py` (el sitio de
> documentación). La prosa con las medidas y el porqué de cada decisión está en `docs/DISENO.md`
> (1.039 líneas) y el inventario de pantallas en `docs/PANTALLAS.md`.

---

## 1. Qué es esto

**Cesta** comparona el precio por unidad del mismo producto entre cinco supermercados españoles
(Mercadona, Carrefour, DIA, Alcampo, Aldi) y lo usa para tres cosas: buscar un producto, montar una
lista de la compra que diga dónde conviene comprar cada cosa, y avisar cuando algo baja de precio.

Se usa **de pie, en el pasillo, con una mano y con el móvil**, y a veces sin cobertura. Eso manda
sobre cualquier decisión estética: tipografía legible a un brazo de distancia, objetivos táctiles
grandes, y la cifra que importa (€/kg, €/l, €/ud) siempre visible.

## 2. Las dos superficies

| | Aplicación | Sitio de documentación |
|---|---|---|
| Ruta | `/` (`plataforma/web/app`, React + Vite + Tailwind) | `/aprende` (`plataforma/aprende.py`, HTML estático) |
| Para qué | buscar, listar, comparar, avisar | explicar cómo funciona todo, con fórmulas |
| Ancho | móvil primero (390×844), escritorio después | 74ch de texto por línea |
| Tema | claro y oscuro por `prefers-color-scheme`, **sin interruptor** | igual |
| Tokens | los de `estilos.css` (abajo) | los mismos **nombres**, otros valores |

Los nombres de los colores y su significado son **los mismos en las dos**: `--fondo`, `--tinta`,
`--tinta-suave`, `--borde`, `--acento`. Leer la app y leer los docs tiene que sentirse como el mismo
sitio.

## 3. Color

### 3.1 Aplicación (Tailwind + variables CSS)

| Token | Claro | Oscuro | Para qué |
|---|---|---|---|
| `--fondo` | `#fafafa` | `#262626` | superficie dentro de una tarjeta |
| `--tinta-suave` | `#525252` | `#a3a3a3` | texto secundario (**7,17:1**: el marcador de un campo es la única etiqueta visible del buscador) |
| `--borde` | `#e5e5e5` | `#404040` | separadores |
| `--aviso` | `#b45309` | `#fcd34d` | avisos («no se pudo comparar», «producto al peso») |
| `--bien` | `#059669` | `#10b981` | borde de lo que ha salido bien |
| `--bien-suave` | `#ecfdf5` | `#022c22` | fondo de lo que ha salido bien |

Además de los tokens, la app usa las escalas de Tailwind `neutral` y `sky` (el `sky-600` es el
anillo de foco). **La marca no impone paleta propia**: el color se usa para decir algo (bueno, aviso,
dudoso), no para decorar.

### 3.2 Sitio de documentación

| Token | Claro | Oscuro | Para qué |
|---|---|---|---|
| `--fondo` | `#ffffff` | `#131518` | fondo |
| `--fondo-suave` | `#f7f8fa` | `#16181b` | barras y bloques secundarios |
| `--panel` | `#ffffff` | `#1a1d21` | tarjetas |
| `--tinta` | `#16181b` | `#eceef0` | texto |
| `--tinta-suave` | `#5b6169` | `#a3aab2` | texto secundario |
| `--borde` / `--borde-fuerte` | `#e4e6ea` / `#cfd3d9` | `#2b2f35` / `#3a3f46` | bordes |
| `--acento` | `#0b5cab` | `#7cc2ff` | enlaces y lo activo |
| `--acento-suave` | `#eef5fd` | `#12283c` | fondo de enlace activo |
| `--codigo` / `--codigo-tinta` | `#f6f7f9` / `#24313f` | `#1f2328` / `#dfe4ea` | bloques de código |

Y cinco fondos de nota, uno por tipo de aviso, porque **el color dice de qué va el aviso**:
`--nota` `#eef5fd`, `--aviso` `#fff7e6`, `--trampa` `#fdecec`, `--leccion` `#ecf8f1`,
`--regla` `#f2effd` (en oscuro, cada uno su variante).

## 4. Tipografía

    familia   ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
    cuerpo    16px / 1,7
    código    ui-monospace, monospace  (bloques con --codigo de fondo)
    cifras    tabular-nums SIEMPRE (clase `.cifra`)

**Las cifras van en ancho fijo**, sin excepción: una tabla de precios con ancho variable baila fila
a fila y comparar dos precios de un vistazo cuesta más. Aplica a precios, €/kg y porcentajes.

En el sitio de documentación, la medida de línea es **74 caracteres** (`--ancho: 74ch`) y el
`scroll-padding-top` de 5rem deja hueco a la barra fija al saltar a un apartado.

## 5. Piezas (lo que ya existe y hay que respetar)

| Pieza | Qué es | Regla |
|---|---|---|
| **Etiqueta** | píldora con tono: `dato`, `bien`, `aviso`, `mal` | lleva el porqué en el `title`; nunca dice lo que no es |
| **`.cifra`** | número tabular | obligatorio en cualquier cifra de una tabla |
| **`Dato`** | par etiqueta/valor de una ficha | la etiqueta arriba, pequeña y suave; el valor grande |
| **Tabla de resultados** | rejilla de productos comparados | se puede recorrer en horizontal en el móvil (`overflow-x-auto`), nunca se sale de la pantalla |
| **Barra inferior** | 6 destinos: Buscar, Lista, Favoritos, Escáner, Avisos, Panel | reserva su alto al final de la página (un dedo, un carro en la otra mano) |
| **Sello de oferta** | «oferta» / «oferta solo con tarjeta» / «oferta · 2 ud» | una oferta que exige comprar dos unidades lo dice; un precio de tarjeta no es lo que pagas en caja |
| **Sello de retirada** | rojo, arriba | manda sobre cualquier otra cosa de la fila |

## 6. Restricciones que **no** se pueden romper

1. **Sin JavaScript ni CSS en línea.** La CSP de Caddy es `script-src 'self'` y `style-src 'self'`:
   no hay `<script>` embebido, ni `style="…"`, ni Google Fonts, ni CDN. Todo es local.
2. **Sin dependencias de red en tiempo de ejecución**: nada de fuentes, iconos o analítica externos.
3. **Móvil primero** (390×844) y **objetivos táctiles ≥ 44 px**.
4. **Funciona sin cobertura** para lo que ya está cargado (la lista se puede tachar sin red).
5. **Contraste**: el texto secundario nunca por debajo de 4,5:1 (el marcador de un campo va a 7:1
   porque en el buscador es la única etiqueta visible).
6. **La cifra comparable manda**: si hay que elegir entre un adorno y el €/kg, se va el adorno.
7. **Nada que parezca una promesa que no se puede sostener**: «desde», «podría», «estimado» solo
   cuando de verdad lo es, y el dato lleva su fecha cuando puede caducar.

## 7. Las pantallas que merece la pena diseñar

Por orden de valor (el inventario completo está en `docs/PANTALLAS.md`):

1. **Buscar** — campo + resultados comparados con la cadena más barata, el €/kg y el ahorro.
2. **Ficha del grupo** — la clave del proyecto: el mismo producto en cinco cadenas, cuál gana
   contigo, la curva de precios y el «por qué» de cada cosa.
3. **Lista de la compra** — líneas, tachado, reparto por tiendas (¿dónde conviene comprar cada
   cosa?) y total con y sin ofertas.
4. **Dónde comprar** (panel) — pasillos ganadores por cadena, oportunidades del día.
5. **Avisos** — alertas de bajada y de mínimo de 90 días, con la frase que las explica.
6. **Favoritos** — con añadir a la lista de un toque.
7. **Sitio de documentación** (21 capítulos, 8 secciones) — portada, índice lateral, buscador,
   bloques de código y las cinco cajas de aviso.

## 8. Cómo se mide una mejora aquí

No hay «me gusta más»: hay cuatro barras, y dos son automáticas.

| Barra | Qué exige |
|---|---|
| `uv run python -m plataforma.prueba_produccion` | la pantalla servida contesta y las cuatro preguntas tienen respuesta (automática) |
| `uv run python -m plataforma.prueba_navegador` | el recorrido en un navegador de verdad, en un móvil de 390×844 (automática) |
| `uv run python -m plataforma.prueba_funciones` | **cada función de la aplicación hecha de verdad** (46 comprobaciones: alta y baja, varias listas, favoritos, avisos, vistas guardadas, pesos, escáner, elegir tienda, y que lo que se despliega lleve su flecha), con cuenta desechable (automática) |
| `docs/PRUEBA-15-SEGUNDOS.md` | **la barra (a)**: una persona que no ha escrito esto contesta las cuatro preguntas en 15 segundos con el móvil. La cierra el dueño, no el código |
| `uv run pytest` | 935 pruebas, 0 fallos, y el sitio de documentación con sus 13 pruebas |
