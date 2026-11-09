# Cambios de interfaz aplicados — 2026-11-09 (noche)

Los ocho problemas de [la revisión de interfaz](revision-interfaz.md) que **no** dependen de una
decisión de David, aplicados con captura de antes y de después. Los que sí la necesitan están en
[decisiones-interfaz-2026-11-09.md](decisiones-interfaz-2026-11-09.md), para que se los pases.

- **Antes:** `data/revision-ui-2026-11-09-antes/` (capturas de la revisión, misma tanda de
  datos: lista de 10 líneas, 3 favoritos, 2 recetas).
- **Después:** `data/revision-ui-2026-11-09-despues/` (banco de ensayo nuevo, mismo sembrador:
  misma lista de 10 líneas y mismas búsquedas; cambian los ids de receta y el orden de algún
  favorito, nada que afecte a lo que se compara).
- Las dos carpetas están **fuera de git** (`data/`), como el resto de artefactos: se regeneran.
- Capturas: móvil 390 × 844 (página completa y primera pantalla); escritorio en las seis de
  siempre. La barra fija sale en mitad de la página completa: es artefacto de la captura.

## Lo aplicado, con su antes y su después

| # | Problema (revisión) | Antes | Después | Qué cambió |
|---|---|---|---|---|
| 1 | §4.1 La portada enseñaba «0,00 €» y coronaba una cadena | `01-portada-movil.png` | `01-portada-movil.png` | Sin líneas comparables no se pinta ningún total: se dice que faltan precios confirmados |
| 2 | §4.2 Cuatro totales «0,00 €» en comparar la cesta | `06-comparar-cesta-movil.png` | `06-comparar-cesta-movil.png` | Donde no hay producto, «sin precio» en vez de un cero con forma de precio |
| 3 | §4.4 La cabecera repetía el nombre y ponía «Cesta / Cesta» | `18`, `19`, `20`, `22` | los mismos | Un solo título por pantalla; las sueltas ya dicen su nombre (Tu perfil, Avisos, Escáner, Panel, Matching) |
| 4 | §4.5 «Importar una receta» se titulaba «Compra» | `17-importar-receta-movil.png` | `17-importar-receta-movil.png` | Título «Importar receta» (cabe al lado del botón del menú) |
| 5 | §4.7 «40 min» dentro de «Coste de ingredientes» y el muro de «Faltan precios» | `10-receta-movil.png` | `10-receta-movil.png` | El tiempo se queda en la cabecera; con más de tres sin precio, un contador que remite a la lista de ingredientes |
| 6 | §4.8 «Buscar por nombre…» recortado a «Buscar por nomb» | `09-recetario-movil-visible.png` | `09-recetario-movil-visible.png` | Buscador y filtro en dos filas en móvil; el placeholder se lee entero |
| 7 | §4.9 «Cadena habitual» en singular y valor con elipsis | `18-ajustes-movil.png` | `18-ajustes-movil.png` | «Cadenas que tienes cerca», y el valor se lee entero en dos líneas (sin `title` ni `truncate`) |
| 8 | §4.10 Tildes sueltas | `15`, `16` y la barra interior | los mismos | «Últimos», «14 días», «aparecerá», «Qué», «Cuánto», «vacío» y «Calorías» en la barra y el menú |

### 1. La portada, sin ceros con forma de precio

`Portada.tsx`: si `reparto.lineas` es 0 no hay ninguna línea comparable, y el filtro anterior
dejaba pasar todas las cadenas con total 0 y coronaba «0,00 €». Ahora, con `comparables === 0` se
dice «Todavía no hay ninguna línea con precio confirmado…»; y aunque haya líneas, si ningún total
es mayor que cero no se corona nada. La lista de 28,60 € sigue enseñando su precio estimado: el
cero de la portada no era el precio de la lista, era la comparación sin datos.

Prueba nueva en `Portada.test.tsx`: «con lineas pero sin ningun precio confirmado, no corona un
0,00» (busca que no aparezca ni «0,00 €» ni «la más barata»).

**Después:** captura 01 — «MI CESTA · Todavía no puedo comparar la lista entera: hay líneas sin
precio confirmado o productos que no están en todas las cadenas · Ver mi lista». Nada de 0,00 €.

### 2. Comparar la cesta: «sin precio»

`CompararCesta.tsx`, `CadenaEnLaLista`: si `contadas === 0`, en el sitio del total se pinta
«sin precio» en vez de `euros(0)`. La frase de cabecera ya explicaba que no se pueden comparar
entre sí; ahora los números no mienten mientras se lee la explicación.

**Después:** captura 06 — las cuatro cadenas dicen «sin precio · con 0 de 8 productos», y debajo
sigue el aviso de confirmar los productos.

### 3. Una cabecera, un título

`componentes/Suite.tsx`:

- **Fuera el rótulo pequeño con el nombre de la app encima del `h1`.** En móvil el botón del menú
  ya dice la app y en las pantallas sueltas el rótulo repetía «Cesta» sobre un título que también
  decía «Cesta». Queda el `h1` con el nombre de la pantalla.
- **`tituloDeSeccion` nombra las pantallas sueltas**: `/ajustes` → Tu perfil, `/avisos` → Avisos,
  `/escaner` → Escáner, `/panel` → Panel, `/panel/matching` → Matching, `/unirme/…` → Invitación.
- **`/compra/despensa` → Despensa** y **`/compra/importar` → Importar receta** (antes caían en el
  nombre de la app).
- **`'Calorias'` → `'Calorías'`** en `APLICACIONES`: la barra interior y el botón del menú ya
  dicen la palabra como la enseña la portada.

**Después:** 18 «Cesta · Tu perfil», 19 «Cesta · Avisos», 22 «Cesta · Escáner», 16 «Compra ·
Despensa», 17 «Recetas · Importar receta», 20 «Cesta · Panel». Ya no hay dos títulos iguales
seguidos en ninguna pantalla.

### 4. Receta: el tiempo fuera del coste y el aviso sin muro

`RecetaDetalle.tsx`:

- `CosteDeLaReceta` ya no recibe `minutos`: el tiempo está en la cabecera de la receta («RECETA ·
  4 RACIONES · 40 MIN») y dentro de la tarjeta verde parecía parte de la cuenta.
- `avisosDeCobertura`: con **más de tres** ingredientes sin precio, un contador («Faltan precios de
  4 ingredientes: los marcados como «sin coste» aquí abajo») en vez de la frase con los nombres
  encadenados. Con uno a tres se sigue diciendo el nombre, que ahí sí cabe. La lista de
  «Ingredientes» de justo debajo ya lleva cada nombre con su «sin coste».

**Después:** captura 10 — la tarjeta dice «COSTE DE INGREDIENTES / Coste no disponible /
Faltan precios de 4 ingredientes: …», sin «40 min» al lado del precio.

### 5. Recetario: el buscador se lee entero

`Recetario.tsx`: en móvil el buscador y el filtro de etiquetas van en dos filas (`flex-col` hasta
`sm`), con el campo a todo el ancho. Antes compartían fila y el `min-w-0` recortaba el placeholder
a «Buscar por nomb».

**Después:** captura 09 — «Buscar por nombre…» completo y «Todas las etiquetas» debajo.

### 6. Ajustes: plural y sin elipsis

`Ajustes.tsx`: «Cadena habitual» → «Cadenas que tienes cerca» (que es lo que ya decía el `legend`
del fieldset) y el resumen se lee entero: se quitó `truncate` y el `title` que solo servía con
ratón. El texto envuelve en dos líneas y sigue alineado a la derecha.

**Después:** captura 18 — «Cadenas que tienes cerca · DIA, Alcampo, Mercadona y Carrefour», con el
chevron del desplegable al lado.

### 7. Tildes

- `Tendencias.tsx`: «Últimos», «{n} días», «no hay nada anotado en estos días», «aparecerá».
- `Despensa.tsx`: «Qué», «Cuánto», «(vacío = no se sabe)», «no se sabe cuánto queda».
- `Suite.tsx`: «Calorías» (barra, menú y botón).

**Después:** capturas 15 y 16, y la barra de cualquier pantalla interior.

## Lo que no se ha tocado (y por qué)

- **§4.3 el producto de Carrefour repetido**: es una decisión (colapsar en pantalla o deduplicar
  en identidad). Opciones, coste y qué gana: [decisiones §1](decisiones-interfaz-2026-11-09.md).
- **§4.6 la base de los porcentajes**: es una decisión de producto; la app ya calcula en la más
  barata en dos sitios y la portada en la más cara. [Decisiones §2](decisiones-interfaz-2026-11-09.md).
- **El resto de §4.7** (lista desplegable en vez de contador): se aplicó el contador porque cabe y
  no duplica; la alternativa está escrita en [decisiones §3](decisiones-interfaz-2026-11-09.md).
- **Las imágenes de Carrefour y DIA** que no cargan son del CDN (403/ORB), no de la app; el
  arreglo sería un *placeholder* propio en `onerror`, que es una decisión de diseño.

## Comprobado

- `npm run test:componentes` (vitest): **21 ficheros, 245 pruebas, 0 fallos**.
- `npm test` (node): **404 pruebas, 404 pasan, 0 fallan**.
- `npm run tipos` (`tsc --noEmit`): limpio. `npm run lint`: limpio.
- `npm run build`: compila y sella el service worker (`version 2026110918`). `dist/` está fuera de
  git; el `dist` local queda actualizado para el contenedor de producción.
- Suite de Python completa: **1.451 verdes, 812 saltadas, 0 rojos, 10 min 21 s** (las saltadas son
  las pruebas de PostgreSQL, sin base). La primera pasada de la noche cazó un BOM que PowerShell
  había dejado en `Ajustes.test.tsx`; se quitó y esta es la pasada limpia.
- **`npm run setup` no existe en este proyecto** (los scripts de `plataforma/web/app/package.json`
  son `dev`, `build`, `tipos`, `test`, `test:componentes`, `lint`). Se ha usado la instalación
  existente (`node_modules`) y se han corrido los cuatro que sí existen.

## Reproducir las capturas

    .\.venv\Scripts\python.exe -m plataforma.ensayo prepara
    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:55432/cesta_ensayo_propio'
    $env:CESTA_GOLD='F:\Proyectos\cesta\data\gold'
    .\.venv\Scripts\python.exe -m uvicorn plataforma.api.main:app --port 8099   # otra ventana
    cd plataforma\web\app; $env:CESTA_API='http://127.0.0.1:8099'; npm run dev  # otra ventana
    $env:CESTA_CAPTURA_SALIDA='data/revision-ui-2026-11-09-despues'
    .\.venv\Scripts\python.exe scripts\capturar_pantallas.py
    .\.venv\Scripts\python.exe -m plataforma.ensayo limpia
