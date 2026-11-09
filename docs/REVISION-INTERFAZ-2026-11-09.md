# Revisión externa de la interfaz — inventario y problemas (2026-11-09)

Para que lo lean Claude, GPT o Codex sin preguntar nada. Las capturas están hechas y
medidas; este documento dice qué hay en cada pantalla, qué se ve raro y con qué
evidencia. **No es una prueba de usabilidad** (eso pide una persona delante): es un
inventario que sirve para que quien revise no tenga que abrir la app ni adivinar rutas.

- Capturas: `data/revision-ui-2026-11-09/` (**fuera de git**, se regeneran; ver §7).
  Cada pantalla tiene `-movil.png` (página completa, 390 × 844, ×2), `-movil-visible.png`
  (la primera pantalla) y, en seis casos, `-escritorio.png` / `-escritorio-visible.png`
  (1440 × 900). Los textos crudos de cada pantalla, en `textos/`.
- Medidas de todas: `data/revision-ui-2026-11-09/manifiesto.json`.
- Fecha de la pasada: **2026-11-09, 17:00–17:15** (Europe/Madrid), catálogo del día
  `20261109-113939`.
- Datos: cuenta de usar y tirar en una base desechable, no la base de casa (§1).

---

## 0. Qué se pide a quien revisa

1. Leer §4 (los diez problemas) y decir **cuáles son reales y cuáles no**, y **cuáles
   faltan**. En §5 están los falsos positivos ya descartados: si algo de ahí aparece en
   la revisión, es ruido conocido.
2. Para los que se acepten, proponer el arreglo con la pantalla y el fichero que se toca
   (en §4 ya viene una pista de dónde está cada uno).
3. Lo que **no** se ha revisado está en §6; no hace falta que lo cubráis también.

---

## 1. Cómo se capturó (repetible)

No se ha tocado la app ni su base. La pasada usó un banco de ensayo aislado:

    1. .\.venv\Scripts\python.exe -m plataforma.ensayo prepara
       → PostgreSQL desechable en 127.0.0.1:55432 (contenedor cesta-ensayo-propio)

    2. API contra esa base y con el gold de verdad:
       $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:55432/cesta_ensayo_propio'
       $env:CESTA_GOLD='F:\Proyectos\cesta\data\gold'
       .\.venv\Scripts\python.exe -m uvicorn plataforma.api.main:app --port 8099

    3. Interfaz en modo desarrollo (hace proxy de /api):
       cd plataforma\web\app
       $env:CESTA_API='http://127.0.0.1:8099'; npm run dev

    4. .\.venv\Scripts\python.exe scripts/capturar_pantallas.py

El guion (`scripts/capturar_pantallas.py`) crea o reutiliza la cuenta `revision-ui`, le
siembra **una lista de casa con 20 líneas reales** (buscando en el catálogo del día), tres
favoritos, dos recetas con ingredientes y una semana de plan. Después entra con patchright,
navega a cada ruta y guarda la captura y la medida. Se puede lanzar por partes:
`--solo 02-buscar,07-favoritos`.

**Lo que hay que saber para no confundirse:**

- La lista y las recetas **son datos sembrados para la revisión**, no la lista real de
  David. Por eso hay ingredientes raros (“Media tortilla de patata con cebolla Listo para
  Comer” como si fuera “patata”): el sembrador coge el primer resultado de la búsqueda.
- **Las capturas de página completa muestran la barra inferior fija en mitad de la imagen.**
  Es un artefacto de la captura: la barra está anclada al borde de la ventana y, al
  fotografiar la página entera, sale donde estaba. No es un fallo de la interfaz.
- En `manifiesto.json`, `errores` incluye cosas como `petición fallida: /api/estado`. Se
  comprobó una a una contra la API: **todas devuelven 200**; son peticiones abortadas por
  React Query (doble montaje/refresco), no fallos. No las reportéis como error.
- Las **imágenes de producto de Carrefour y DIA no cargan en estas capturas**: el CDN de
  Carrefour responde **403** a cualquier cliente sin su contexto (`static.carrefour.es`) y
  Chrome bloquea las de DIA con `ERR_BLOCKED_BY_ORB`. Es externo a la app, pero ensucia la
  revisión visual: hay huecos donde debería haber foto. Ver §5.
- Los recortes que cuenta el manifiesto (`recortados`) incluyen elementos `sr-only` de
  1 px de ancho. El único recorte real es el de Ajustes (§4.9).

---

## 2. Inventario de pantallas (23)

`alto` es la altura de la página completa en móvil (390 px de ancho). 844 = la altura
justa de la ventana: pantalla corta o estado vacío.

| # | Pantalla | Ruta | Qué hace | Captura (móvil) | Escritorio | Alto |
|---|---|---|---|---|---:|
| 01 | Portada | `/` | Qué cuesta la cesta, en qué cadena, qué se ha movido, pasillos | `01-portada-movil.png` | sí | 972 |
| 02 | Buscar | `/compra?q=leche` | Resultados con PVP, €/unidad, cadenas, oferta, Nutri-Score; filtros | `02-buscar-movil.png` | no | 10.174 |
| 03 | Ficha de producto | `/compra/productos/aldi/601131600` | Precio, €/l, serie de 4 días, alternativas, etiquetado | `03-ficha-producto-movil.png` | sí | 1.639 |
| 04 | Comparar un grupo | `/compra/comparar/10645` | Las 5 cadenas del mismo producto, ordenadas por pesos, con notas | `04-comparar-grupo-movil.png` | no | 3.091 |
| 05 | La lista | `/compra/listas/{id}` | Precio estimado, lo que falta por pasillo, lo del carro, lo de siempre, pegar/llevar/compartir | `05-lista-movil.png` | sí | 6.841 |
| 06 | Comparar mi cesta | `/compra/listas/{id}/comparar` | Total por cadena y producto a producto; lo que no suma se dice | `06-comparar-cesta-movil.png` | sí | 1.718 |
| 07 | Favoritos | `/compra/favoritos` | Lo guardado con su rango real de historial | `07-favoritos-movil.png` | no | 1.101 |
| 08 | Ofertas | `/compra/ofertas` | Lo que anuncian las cadenas, con tipo y condición de club | `08-ofertas-movil.png` | no | 8.884 |
| 09 | Recetario | `/recetas` | Mis recetas, archivadas, etiquetas, crear/importar | `09-recetario-movil.png` | sí | 844 |
| 10 | Receta | `/recetas/245` | Raciones, versión, coste de ingredientes, pasos, planificar | `10-receta-movil.png` | no | 1.329 |
| 11 | Plan semanal | `/recetas/plan` | Comida/cena por día, copiar la semana, pasar a la lista | `11-plan-semanal-movil.png` | no | 1.563 |
| 12 | Diario | `/calorias` | Día, macros, objetivo, anotar comida, tendencias/alimentos/pautas | `12-diario-movil.png` | sí | 1.432 |
| 13 | Pautas de salud | `/calorias/pautas` | Fibra, azúcar, sal, agua, fruta/verdura, alcohol, con fuente y enlace; gasto estimado | `13-pautas-movil.png` | no | 1.615 |
| 14 | Mis alimentos | `/calorias/alimentos` | Preparar una receta y anotar raciones | `14-alimentos-movil.png` | no | 1.179 |
| 15 | Tendencias | `/calorias/tendencias` | Últimos 7/14/30 días, con huecos donde no hay dato | `15-tendencias-movil.png` | no | 844 |
| 16 | Despensa | `/compra/despensa` | Declarar lo que hay y descontarlo | `16-despensa-movil.png` | no | 844 |
| 17 | Importar receta | `/compra/importar` | Pegar una URL y ver la previa antes de guardar | `17-importar-receta-movil.png` | no | 844 |
| 18 | Tu perfil | `/ajustes` | Cadenas cercanas, objetivo, avisos, darse de baja | `18-ajustes-movil.png` | no | 1.068 |
| 19 | Avisos | `/avisos` | Productos que sigues, cuando tocan su mínimo de 90 días | `19-avisos-movil.png` | no | 844 |
| 20 | Panel | `/panel` | Cuadro de mando de la ingesta (diagnóstico, sin enlace de consumo) | `20-panel-movil.png` | no | 1.940 |
| 21 | Matching | `/panel/matching` | Diagnóstico del emparejador, con el JSON a la vista | `21-matching-movil.png` | no | 8.436 |
| 22 | Escáner | `/escaner` | Buscar por código de barras escrito o pegado | `22-escaner-movil.png` | no | 844 |
| 23 | Entrar | `/compra/listas` (sin sesión) | Usuario y clave; el alta es el otro formulario de la misma tarjeta | `23-entrar-movil.png` | no | 844 |

Las pantallas 20 y 21 son de diagnóstico, no de consumo: sirven para entender de dónde
sale un dato, y no aparecen en ningún menú. Se incluyen porque también se enseñan.

---

## 3. Medidas objetivas de las 23 pantallas

Lo que se midió en el navegador, no a ojo (está en `manifiesto.json`):

| Medida | Resultado |
|---|---|
| Desbordamiento horizontal | **0 px en las 23** pantallas de móvil y en las 6 de escritorio |
| Texto por debajo de 12 px | **0** elementos con texto visible en las 23 |
| Controles táctiles menores de 24 px | Solo enlaces de texto en línea (“Confirmarlos en la lista”, “Editar ingredientes”); el resto cumple |
| Recortes con elipsis reales | **1**: el resumen de cadenas de Ajustes (§4.9) |
| Imágenes rotas | 7/40 en Buscar y 2/7 en Comparar (CDN de Carrefour/DIA, externo; §5) |
| Errores de consola reales | 0 (los `petición fallida` son abortos; §1) |

O sea: **la maqueta aguanta el ancho**. Lo que falla es qué se dice y en qué estado, no
que se rompa. Por eso los diez problemas de §4 son de contenido, jerarquía y estados —
salvo el del buscador del recetario, que sí es de sitio.

---

## 4. Los diez problemas, de más a menos claro

### 4.1. La portada enseña “0,00 €” y corona una cadena cuando no hay nada que comparar

**Qué se ve.** En `/` (captura `01-portada-movil.png`): tarjeta verde «MI CESTA» con
**0,00 €**, «en Alcampo, la más barata de 2 cadenas» y las filas Alcampo 0,00 € /
Carrefour 0,00 €. La misma lista, abierta en `/compra/listas/{id}`, dice **28,60 €**
(pantalla 05). Las dos pantallas no mienten: la portada solo corona cadenas que cubren
toda la lista, y en ese estado la lista tenía 10 líneas **sin confirmar**, así que no
había ninguna cadena completa… y aun así salió una “más barata”.

**Evidencia.** `plataforma/web/app/src/paginas/Portada.tsx:228-243`: el filtro es
`faltan.length === 0 && encontrados >= r.lineas`. Con `r.lineas === 0` (ninguna línea
comparable) **pasa cualquier cadena**, y `completas` acaba lleno de totales a cero.
El propio fichero dice en su cabecera (línea 12) que la tarjeta no debe enseñar «un
“0,00 €” que parece una respuesta»: el caso que se quería evitar es justo el que sale.

**Por qué importa.** Un cero que significa “no lo sé” se lee como un precio. Y encima
corona una cadena: el producto promete “dónde me sale mejor” y la respuesta es falsa.

**Arreglo propuesto.** Antes de coronar: si `r.lineas === 0` (o si todos los
`total_cent` son 0), enseñar el estado que ya existe para “no puedo comparar la lista
entera” —«Todavía no puedo comparar la lista entera»— con enlace a la lista para
confirmar los productos. Nunca pintar 0,00 € como precio.

**Gravedad.** Alta.

### 4.2. Comparar la cesta: cuatro “0,00 €” como totales de cuatro cadenas

**Qué se ve.** En `/compra/listas/{id}/comparar` (captura `06-comparar-cesta-movil.png`):
Alcampo 0,00 €, Carrefour 0,00 €, DIA 0,00 €, Mercadona 0,00 €, y debajo la explicación
correcta («Ninguna cadena tiene los 8 productos de la lista…»). El texto está bien; los
números, no: cuatro ceros que parecen precios.

**Evidencia.** `CompararCesta.tsx:409-452` pinta `euros(cadena.total_cent)` en todas las
filas de `una_tienda`, incluidas las que tienen 0 encontrados. La API devuelve
`total_cent: 0` con `encontrados: 0` (comprobado: `/api/listas/{id}/donde`).

**Por qué importa.** Es el mismo patrón que el contador del menú ya evita a propósito
(«un cero que también significa “no lo sé” no informa»). Aquí sí se pinta.

**Arreglo propuesto.** Cuando `encontrados === 0`, en el sitio del total poner
«sin precio» o «no la tiene»; y si ninguna cadena resuelve la lista, sustituir los cuatro
totales por una sola frase. Los ceros no se pintan.

**Gravedad.** Alta.

### 4.3. Comparar un grupo repite dos veces el mismo producto de Carrefour

**Qué se ve.** En `/compra/comparar/10645` (captura `04-comparar-grupo-movil.png`), la
tarjeta de Carrefour tiene **dos bloques idénticos**: «Leche semidesnatada Carrefour
brik 1 l. · 0,83 € · 0,83 €/l · +5,1 % · nota 87,8». Mismo nombre, mismo precio, misma
nota. No es que la captura esté repetida: son dos filas.

**Evidencia.** `GET /api/grupo/10645` devuelve dos productos de Carrefour con **ids
distintos y nombre y precio idénticos**: `530014571` y `521007071`, los dos a 83 céntimos
y 83,0 €/l. La pantalla pinta los miembros del grupo uno a uno
(`Grupo.tsx`, tarjeta por producto).

**Por qué importa.** Parece un fallo de la pantalla y es un duplicado del catálogo; pero
el lector ve duplicado, y en una pantalla que existe para comparar precios dos filas
iguales hacen dudar de todo lo demás. Si son dos productos distintos, hay que poder
saberlo (envase, EAN); si es el mismo, sobra uno.

**Arreglo propuesto.** En origen (identidad del catálogo) deduplicar por
`(cadena, nombre normalizado, precio, unidad)`; en la pantalla, mientras exista el
duplicado, colapsar los miembros con la misma cadena+precio en una fila con un contador
(«2 productos iguales»).

**Gravedad.** Alta (es el corazón del producto: comparar precios).

### 4.4. La cabecera dice el nombre de la app dos veces, y en las pantallas sueltas pone “Cesta / Cesta”

**Qué se ve.** En móvil la cabecera tiene tres niveles: el botón de menú («☰ Compra»), el
rótulo pequeño («COMPRA») y el título («Lista»). El nombre de la app sale **dos veces**
seguidas (botón y rótulo). Y en las pantallas sin app —`/ajustes` (captura
`18-ajustes-movil.png`), `/avisos`, `/escaner`, `/panel`— el rótulo y el título dicen los
dos **«Cesta»**: «CESTA / Cesta», y justo debajo la pantalla pone su propio título
(«Tu perfil», «Avisos», «Escáner»). Tres títulos para una pantalla.

**Evidencia.** `componentes/Suite.tsx:440` (botón: `{app?.nombre ?? 'Cesta'}`),
`:443-444` (rótulo: `{app?.nombre ?? 'Cesta'}`) y `:446` (`tituloDeSeccion(pathname)`),
que para `/ajustes`, `/avisos`, `/escaner` y `/panel` devuelve `'Cesta'` porque
`aplicacionDe()` es `null` (`Suite.tsx:126-146`).

**Por qué importa.** La cabecera es lo que orienta; repetir el nombre de la app y titular
dos veces la misma pantalla es ruido en el sitio más caro de la pantalla. En las
pantallas sueltas además el título visible no dice dónde estás.

**Arreglo propuesto.** Una sola fuente para el título: el rótulo pequeño queda para la
app (o se quita en móvil, donde el botón ya la dice) y el `h1` pone la pantalla. Para
`/ajustes` → «Tu perfil», `/avisos` → «Avisos», `/escaner` → «Escáner», `/panel` →
«Panel» (`tituloDeSeccion` ya sabe hacerlo si se le añaden esos casos).

**Gravedad.** Media-alta (afecta a todas las pantallas).

### 4.5. “Importar una receta” se titula “Compra”

**Qué se ve.** En `/compra/importar` (captura `17-importar-receta-movil.png`) el rótulo
dice «RECETAS» y el título grande dice **«Compra»**. La pantalla es de Recetas.

**Evidencia.** `Suite.tsx:131-146`: `tituloDeSeccion` para `/compra/importar` no encuentra
subsección exacta, no es `/productos/`, no es `/listas/`, y `app.clave` es `compra`, así
que cae en `return app.nombre` → «Compra».

**Por qué importa.** El usuario ha llegado desde Recetas y la app le dice que está en
Compra. Es un título cruzado, y es el tipo de detalle que hace desconfiar de toda la
navegación.

**Arreglo propuesto.** Añadir la ruta a `APLICACIONES` de recetas (`/compra/importar` →
«Importar una receta») o un caso en `tituloDeSeccion` antes del `return app.nombre`.

**Gravedad.** Media (fácil de arreglar).

### 4.6. Porcentajes sin base: el mismo grupo da 130,4 % en un sitio y −43 % en otro

**Qué se ve.** En Comparar un grupo (captura 04): «DIFERENCIA ENTRE LA MÁS CARA Y LA MÁS
BARATA: **130,4 %** · 1,03 € por unidad» y arriba «130,4 % · 1,03 € por unidad». En
Buscar: «hasta un **61,7 %** en el grupo». En la portada, la misma comparación se cuenta
como «−43 %» (el ahorro se calcula contra la cadena más cara: `Portada.tsx:247-249`),
mientras el grupo calcula contra la más barata.

**Evidencia.** `GET /api/grupo/10645` → `ahorro_pct: 130.4` (barata 0,79 €/l, cara 1,82 €/l:
`(1,82-0,79)/0,79 = 130,4 %`). `Portada.tsx:247-249` usa
`(cara - barata) / cara` → 43 %. `Grupo.tsx:364-366` pinta el `ahorro_pct` del grupo tal
cual. Los dos números son correctos y **parecen contradecirse**.

**Por qué importa.** Un porcentaje sin base es una cifra que no se puede comprobar. Y aquí
además dos pantallas de la misma app usan bases distintas para el mismo producto.

**Arreglo propuesto.** Escribir la frase completa en los dos sitios: «la más cara cuesta un
130 % más que la más barata» / «ahorras un 43 % eligiendo la más barata». Mantener **una**
base y nombrarla.

**Gravedad.** Media.

### 4.7. Receta: el tiempo dentro del coste y “faltan precios” como párrafo de seis nombres

**Qué se ve.** En `/recetas/245` (captura `10-receta-movil.png`): la tarjeta verde
«COSTE DE INGREDIENTES» lleva **«40 min» a la derecha**, que no tiene nada que ver con el
coste (el tiempo ya está en la cabecera). Debajo: «Faltan precios de Patatas para freir 2
Kg Carrefour, Media tortilla de patata con cebolla Listo para Comer, AUCHAN Tortilla
fresca de patata, con cebolla y elaborada sin gluten 600 g Producto Alcampo, y PRODUCTO
ALCAMPO Aceite de orujo de oliva botella 1 l.» — seis nombres de producto en una sola
frase, en negrita dentro de la tarjeta, sin lista ni forma de arreglarlo.

**Evidencia.** `RecetaDetalle.tsx:245-266` (recibe `minutos` y lo pinta dentro de la
tarjeta de coste) y `:214` (`Faltan precios de ${enEspanol(c.sinPrecio)}.`).

**Por qué importa.** Mezcla dos unidades en una tarjeta y convierte un aviso accionable
(“a estos ingredientes les falta precio”) en un muro de texto ilegible, que es justo lo
que empuja a no rellenar el dato.

**Arreglo propuesto.** Sacar el tiempo de la tarjeta de coste. Y el aviso, en lista: una
línea por ingrediente sin precio, con enlace al buscador o al producto; o un resumen
(«6 ingredientes sin precio») que se despliega.

**Gravedad.** Media.

### 4.8. El buscador del recetario no cabe: “Buscar por nombre…” se lee “Buscar por nomb”

**Qué se ve.** En `/recetas` (captura `09-recetario-movil-visible.png`), los dos campos de
la fila de filtros compiten por el ancho: el placeholder queda **«Buscar por nomb»** y el
otro, «Todas las etiquetas». En 390 px no caben los dos.

**Evidencia.** Captura. En el código, `Recetario.tsx:395-396` pone el campo con
`flex-1 min-w-0` dentro de una fila de dos; el `min-w-0` es lo que le permite encogerse
hasta que el placeholder se corta (el texto completo, «Buscar por nombre…», solo queda
como `aria-label` para lectores de pantalla).

**Por qué importa.** Es una pantalla de búsqueda: si el campo de búsqueda no dice para qué
es, el usuario no sabe si busca recetas, ingredientes o etiquetas.

**Arreglo propuesto.** Una sola columna en móvil (buscador arriba y etiqueta debajo) o
placeholder corto («Buscar») con la etiqueta visible fuera del campo.

**Gravedad.** Media-baja (pero es el único problema de sitio puro de la lista).

### 4.9. Ajustes: “Cadena habitual” en singular para cuatro cadenas, y el valor recortado

**Qué se ve.** En `/ajustes` (captura `18-ajustes-movil.png`): «Cadena habitual — DIA,
Alcampo, Mercado…» con elipsis. Son cuatro cadenas seleccionadas («DIA, Alcampo,
Mercadona y Carrefour», 271 px de texto en 184 px de hueco). La etiqueta dice «Cadena» en
singular para una selección múltiple, y en el móvil no hay `hover` que enseñe el valor
completo.

**Evidencia.** `manifiesto.json` → `18-ajustes`: `[184/271] 'DIA, Alcampo, Mercadona y
Carrefour' corte=ellipsis`. Código: `Ajustes.tsx:347` («Cadena habitual»),
`:350-352` (`title={resumenCadenas}` + texto, con `truncate`).

**Por qué importa.** El ajuste que decide **qué cadenas ves** es el que no se puede leer
entero. Y el singular invita a pensar que se elige una.

**Arreglo propuesto.** «Cadenas que tienes cerca» (que es lo que dice el `legend` de
`:361`) y el resumen en dos líneas o con contador («4 cadenas: DIA, Alcampo…»), sin
elipsis en móvil.

**Gravedad.** Media-baja.

### 4.10. Tildes que se han quedado por el camino

**Qué se ve.**

- `/calorias/tendencias` (captura 15): «**Ultimos**», «14 **dias**», «aparecera aqui».
- `/compra/despensa` (captura 16): «**Que**», «**Cuanto** (vacio = no se sabe)».
- La cabecera de la app escribe «**CALORIAS**» y «Calorias», mientras la barra inferior
  dice «Calorías» con tilde: la misma palabra, dos formas en la misma pantalla.

**Evidencia.** `Tendencias.tsx:68` («Ultimos»), `:78` (`{n} dias`); `Despensa.tsx:146`
(«Que») y `:151` («Cuanto (vacio…)»); `Suite.tsx:113` (`nombre: 'Calorias'`).

**Por qué importa.** El proyecto ya hizo una pasada de tildes y esto es lo que quedó. En
una pantalla de salud, «cuanto»/«vacio» sin tilde se nota; y la marca escrita de dos
formas en la misma pantalla es lo más barato de arreglar de toda la lista.

**Arreglo propuesto.** Tildes en esos literales y en `APLICACIONES` (`'Calorías'`), que
arrastra el rótulo, el menú y el botón de una vez.

**Gravedad.** Baja, pero es la más fácil de cerrar.

---

## 5. Falsos positivos ya descartados (no los reportéis)

1. **La barra inferior en mitad de la captura**: artefacto de la página completa; en
   `-movil-visible.png` está donde toca. No es un fallo.
2. **«Cargando…» que se queda**: la captura de Buscar de la primera pasada pilló el
   esqueleto de carga. Repetida con espera a que desaparezca, carga en ~2 s. No es un
   fallo (aunque la primera captura se conservó y se sustituyó).
3. **`petición fallida: /api/...` en el manifiesto**: abortos de React Query; la API
   responde 200 a todas (comprobado con httpx). No es un fallo.
4. **Los “recortes” del manifiesto con ancho 1**: son `sr-only` (enlaces “Saltar al
   contenido”, etiquetas para lectores). Solo el de Ajustes (§4.9) es visual.
5. **Imágenes de Carrefour y DIA que no cargan**: `static.carrefour.es` devuelve 403 a
   cualquier cliente sin su contexto (comprobado con PowerShell y con el navegador), y
   Chrome bloquea las de DIA por ORB. Es del CDN, no de la app; en un navegador con
   cookies de esos sitios puede cargar. No lo arregléis aquí: si molesta, el arreglo es un
   *placeholder* propio cuando `img.onerror`.
6. **El pie de Ajustes que empieza a media frase** («asociada ni patrocinada por…»): la
   barra fija tapa la línea anterior en la captura; la frase está entera en el texto
   (`textos/18-ajustes-movil.txt`).
7. **Duplicado “Casa (10)” / “Casa” en la lista (05)**: el selector de listas y el título
   de la lista abierta. Es el mismo dato dos veces, pero con funciones distintas (elegir
   vs saber dónde estás); no lo cuentes como el §4.4.

---

## 6. Lo que esta revisión NO cubre

- **Usabilidad con una persona real**: los quince segundos, “sin saber dónde está el
  botón”. Eso es `docs/PRUEBA-15-SEGUNDOS.md` y no se puede sustituir con capturas.
- **Accesibilidad formal**: contraste medido (ya hay `tests/test_contraste.py`, 92 parejas
  AA), foco, lector de pantalla, teclado. Aquí solo se midió tamaño de letra y de control.
- **Rendimiento real**: la pasada corre contra el servidor de desarrollo; no mide el
  paquete de producción ni la red del móvil.
- **PWA/offline**: instalación, service worker, “sin cobertura en el súper”. Tiene su
  propia puerta (`plataforma/prueba_navegador.py`, `test_ui_movil.py`).
- **Escritorio**: solo se capturaron 6 pantallas (las que más contenido tienen). El
  producto es móvil; si se quiere revisar escritorio entero, se añaden rutas a
  `ESCRITORIO` en el guion.
- **Estados de error de red**: no se simuló la API caída en esta pasada (hay guion y
  captura antigua en `data/capturas-a09/04-api-caida.png`).

---

## 7. Cómo rehacerlo o ampliarlo

    # 1. banco desechable (no toca la base de casa; puerto 55432)
    .\.venv\Scripts\python.exe -m plataforma.ensayo prepara

    # 2. API contra esa base, con el gold real
    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:55432/cesta_ensayo_propio'
    $env:CESTA_GOLD='F:\Proyectos\cesta\data\gold'
    .\.venv\Scripts\python.exe -m uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8099

    # 3. interfaz (otra ventana)
    cd plataforma\web\app
    $env:CESTA_API='http://127.0.0.1:8099'; npm run dev

    # 4. capturas (todas, o solo algunas)
    .\.venv\Scripts\python.exe scripts/capturar_pantallas.py
    .\.venv\Scripts\python.exe scripts/capturar_pantallas.py --solo 01-portada,05-lista

    # 5. recoger el banco
    .\.venv\Scripts\python.exe -m plataforma.ensayo limpia

Añadir una pantalla es añadir una línea a `PANTALLAS` en
`scripts/capturar_pantallas.py`; añadir una ruta a escritorio, a `ESCRITORIO`. La siembra
(cuenta, lista, recetas) es idempotente: repetir no duplica la lista ni las recetas de la
misma base, y cada pasada sobre una base limpia deja el mismo escenario.

---

## Anexo. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Capturas y medidas | `data/revision-ui-2026-11-09/` (`manifiesto.json`, `textos/`) |
| Guion que las produce | `scripts/capturar_pantallas.py` |
| Portada / cabecera / títulos | `plataforma/web/app/src/paginas/Portada.tsx`, `componentes/Suite.tsx` |
| Comparar cesta | `plataforma/web/app/src/paginas/CompararCesta.tsx` |
| Comparar grupo | `plataforma/web/app/src/paginas/Grupo.tsx` + `GET /api/grupo/{id}` |
| Receta | `plataforma/web/app/src/paginas/RecetaDetalle.tsx` |
| Recetario | `plataforma/web/app/src/paginas/Recetario.tsx` |
| Ajustes | `plataforma/web/app/src/paginas/Ajustes.tsx` |
| Tendencias / Despensa | `paginas/Tendencias.tsx`, `paginas/Despensa.tsx` |
| Banco de ensayo | `plataforma/ensayo.py` (`prepara` / `limpia`) |
