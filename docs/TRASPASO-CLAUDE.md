# Cesta — traspaso: que falta, y que se hizo en cada ronda

> ## AVISO: este documento se quedo viejo, y hay que leerlo con cuidado
>
> Se escribio el 23 de septiembre **antes** del encargo de UX, de la invariante del
> reparto, de `/api/habituales` y del estudio de Jev. Sus numeros y su lista de "lo
> que falta" **ya no son el estado actual**. Sigue valiendo por dos cosas, que son
> las que no caducan: **la seccion 3, las trampas** (errores ya cometidos y pagados,
> para no repetirlos) y **la seccion 4, lo que NO hay que rehacer**.
>
> **El estado actual, al dia, esta en:**
>
>     docs/BACKLOG.md  §0        la barra de aceptacion, sus SEIS condiciones, el
>                                comando que reproduce cada una y el valor de hoy
>     docs/DISENO.md             33 mejoras de interfaz medidas en un navegador real
>     docs/COMPETENCIA-IMPLANTABLE.md   127 funcionalidades de ~50 apps, 17 fichas
>                                listas para implementar y 11 tareas (N29-N39)
>     docs/JEV-IMPLANTACION.md   donde encaja un modelo de salida forzada, y por que
>                                la parte que vale no necesita esperar a Jev
>     docs/REVISION-23SEP.md     la revision externa de ese dia
>
> **Lo que ha cambiado desde que se escribio, en corto:**
>
> - **La invariante del reparto** sustituyo a la cohesion contra el medoide como
>   criterio principal: un grupo no puede tener dos productos de la misma cadena
>   salvo que compartan EAN. Grupos de 11+ de **74 a 0**, cadena repetida sin EAN de
>   **1.385 a 0**, y ningun EAN en dos grupos. El medoide queda como **segunda red**,
>   con su umbral por calibrar contra el banco de pares.
> - **Las cinco cadenas escribieron bronze el mismo dia** (23 sep): esa condicion de
>   la barra, que aqui figura como "por comprobar", **esta cumplida**.
> - **`/api/habituales` existe** (`plataforma/api/habituales.py`), con los tres
>   origenes y el peso por recencia. Pendiente: reconstruir la imagen de la API para
>   que responda en produccion, y decidir si `origen` va por tarjeta o por respuesta
>   -- con el historial real de la casa el mosaico sale de **una** tarjeta.
> - **El contraste esta arreglado** y con la formula de WCAG dentro de las pruebas
>   (`tests/test_contraste.py`), mas las reglas de movil (`tests/test_ui_movil.py`) y
>   el contraste de los limites de campo.
> - **`/favoritos` y `/ajustes` ya tienen enlace**, que era funcion muerta.
> - Y los **cuatro instrumentos** de la barra viven en el repositorio
>   (`projects/cesta/ejes.py`, `tests/test_atributos.py`, `tests/test_contraste.py`),
>   no en scripts de `data/debug/`, que esta en `.gitignore`.

Escrito el 23 de septiembre de 2026 al cerrar el goal que ejecuto el encargo de
`docs/TAREAS-22SEP.md`. Va dirigido a quien siga: **lo que falta, con la prueba de
que falta**, y **lo que ya se hizo, para no repetirlo ni deshacerlo sin querer**.

## 0. Como leer esto, y que garantiza

- Los numeros son **medidos**, y cada uno lleva el comando que lo reproduce. Los
  que no he podido medir lo dicen: no hay estimaciones disfrazadas.
- Las afirmaciones sobre el codigo llevan `fichero:linea`.
- **Lo que NO he leido entero**: `docs/TAREAS-22SEP.md` (626 lineas). Conozco su
  estructura y sus tres correcciones por el resumen que paso el dueno, y por eso los
  bloques de abajo estan contados desde ahi y desde los commits, no desde una
  lectura completa. **Lo primero que hay que hacer es leerlo entero.**
- Las rondas 1 a 24 (goal anterior) no las recuerdo una a una: la sesion se compacto.
  Lo que queda de ellas es el registro durable -- los commits y
  `docs/DIAGNOSTICO-MATCHING.md`, que es donde estan sus numeros --, y asi estan
  contadas aqui. Las rondas 25 a 30 las cuento de memoria y con detalle.

---

## 1. Lo que falta, por orden de valor

### 1.1 Partir los grupos sobrem fundidos (lo primero, y lo que mas vale)

**Que pasa.** El grupo mayor del catalogo son **84 cervezas** que incluyen *sin
gluten* y *sin alcohol*; hay **43 aceites** mezclando *virgen* con *virgen extra*; y
**47 aguas** mezclando 1 l, 3,14 l y pack de 6x1,5 l. La forma del dato lo dice sin
mirar un nombre:

    tramo            grupos   mediana caro/barato   % con >3x
    2-4 productos     7.298          1,16               4,4 %
    5-10                634          1,97              10,4 %
    11 o mas             74          2,59              27,0 %

**El estado, medido hoy** (`uv run python -m projects.cesta.ejes`):

    grupos                                    37.681
    con algun eje contradictorio                  54    <- la barra pide CERO
    grupos de 11 o mas productos                  74    <- la barra pide < 30
    de esos, con eje contradictorio                5
    que mezclan un pack con sueltas              615
    de esos, de 11 o mas                          21

**Por que pasa, que es lo que hay que entender antes de tocar nada.**
`core/matching.py::enlaces()` reparte **1-a-1 por par de cadenas** (bien hecho).
Pero `agrupar_enlaces()` une por **componentes conexas**. Con cinco cadenas hay diez
pares, y basta que en uno se una *entera* con *sin lactosa* y en otro *sin lactosa*
con *desnatada* para acabar con entera y desnatada juntas **sin que ningun enlace
individual este mal**. Por eso el fallo no se arregla con vetos de par.

**Las tres reglas del dueno, que no se pueden cambiar:**

1. **El margen no es el cuchillo.** `core/comparacion.py` documenta ahorros reales de
   **28x** entre marca blanca y marca (preservativos, cerveza, tampones). Cortar por
   margen borraria justo los hallazgos que esta aplicacion existe para encontrar. El
   margen **detecta**; lo que corta es **el atributo que el nombre declara**.
2. **Si uno de los dos no declara nada, no bloquea.** No es tolerancia: es ausencia
   de prueba.
3. **No se toca el hungaro.** El fallo esta despues.

**Lo que hay que hacer:**

- **Partir por eje y por pack**, con el material que ya existe: `core/atributos.py`
  (los ejes) y `unidades_pack` en gold. El sitio donde se parte es
  `agrupar_enlaces()` (`core/matching.py`), que es quien une por componentes conexas.
- **La cohesion contra el medoide**, que es lo que hace falta para el caso de las 84
  cervezas: ahi **ningun eje se contradice** (nadie escribe "con alcohol" en una
  cerveza), y lo unico que lo caza hoy es el pack ([1, 12]). Un grupo no deberia
  contener a nadie que se parezca poco al miembro mas central.
- **Los techos ya estan puestos** en `tests/test_atributos.py`: 54, 74, 615, 21. Si
  bajan, se bajan en el mismo commit; si suben, algo ha empeorado.
- **Y lo que no se puede saltar**: despues de partir hay que **volver a medir las
  cinco condiciones juntas**, porque ya paso lo que pasa cuando se mira una sola
  columna: un numero subio mientras el otro empeoraba.

**Material de trabajo:** `data/debug/_conflictos.py` (conflictos de asignacion de una
pasada, desde su `equivalencia.parquet`) y `data/debug/_perf_*.py` (por que
`candidatos()` no terminaba). **Deberian subir a `projects/cesta/`**, no quedarse en
`data/debug/`, que esta en `.gitignore`.

### 1.2 La ingesta: tres cosas, y una es cara

- **Carrefour tiro 16.525 productos buenos** por una categoria de cuadernos de
  colorear que lleva rota veinte ejecuciones. La revision dice que la linea que lo
  arregla esta escrita y no aplicada.
- **Alcampo: enlaces con la forma equivocada** (un UUID donde va un numero). **Se
  comprueba sin una sola peticion de red, sobre el 100 % de las filas, al escribir el
  bronze**, y los patrones ya existen en `extension/contenido.js`. Habria cazado
  quince dias de Alcampo el primer dia.
- **Aldi se ha quedado sin control independiente**: su ficha ya no ensena precio a un
  cliente HTTP normal (8 de 8 "sin precio"), aunque el colector va bien. Hay que
  sondearla.
- **La quinta condicion de la barra**: las cinco cadenas escribiendo bronze el mismo
  dia. Hoy: **por comprobar**.

### 1.3 Los avisos no le buscan a nadie

`alertas.evalua()` **solo corre cuando alguien abre `GET /api/alertas`**. O sea: la
alerta salta si entras a mirar. El propio modulo dice de si mismo que es "lo unico
que convierte un historico en algo que te busca a ti en vez de esperar a que entres",
y hoy espera. Es un fallo de quien las construyo, con fecha.

### 1.4 Las ofertas: usar la serie propia, que ya existe

Mercadona publica oferta en **0 de 4.328** productos; Aldi en el **4,9 %**. Mientras
una oferta sea una cadena de texto que escribe la cadena, esas dos no tienen arreglo
por ahi. La via buena esta y no se usa: **17 dias de serie propia**, igual de
disponible para las cinco. Una bajada medida es mejor prueba que una etiqueta, y
encuadrada como dato y no como reclamo: *"lleva 14 dias a 3,00 y hoy esta a 2,50"*.
`data/gold/precio_derivado.parquet` ya trae `promo_empieza`, `promo_acaba`,
`precio_base_cent`, `min_90d_cent` y `posicion_90d`.

### 1.5 La interfaz: lo que queda de las mejoras medidas

`docs/DISENO.md` tiene **33 mejoras** medidas en un navegador real. Hechas las cinco
de mas valor salvo dos:

- **Siete zonas de pulsar por debajo de 44 px**, todas con su medida: el `summary`
  "Estado de las cadenas" (`Cabecera.tsx`, 358x24), "la cesta" de `Favoritos.tsx:48`
  (46x19), "Panel de matching ->" (`Panel.tsx:49-54`, 130x20), "Vuelve al buscador"
  (`App.tsx:48`, 173x39), el boton de ordenar (`ui.tsx:380`, 32), los enlaces de
  `/grupo` (`Grupo.tsx:612,622`, 36) y la `x` de una vista guardada
  (`VistasGuardadas.tsx:53`, ~26 de ancho).
- **`/favoritos` y `/ajustes` no tienen ni un enlace en toda la aplicacion** (buscado
  `to="/favoritos"` y `to="/ajustes"`: cero coincidencias). Son dos pantallas a las
  que solo se llega escribiendo la direccion. Eso no es pulido: es una funcion muerta.
- **`/api/habituales` no existe** en `plataforma/api`, asi que el mosaico de
  habituales (anadir pasaria de 2 pulsaciones mas teclear a 1) esta bloqueado por la
  API, no por el diseno.
- **La cesta no separa "por coger" de "en el carro"** (`Cesta.tsx:882-903`, un solo
  `<ul>`). Lo piden `docs/PANTALLAS.md:126` y `docs/UX-MOVIL.md:30-36`, y era lo mejor
  que tenia QueFalta: con 9 lineas y 4 en el carro hay que leer 9 nombres.

### 1.6 La puerta de salida

La **API de darse de baja ya funciona** (se arreglo el 500 de
`lista_linea_anadido_por_fkey`, que impedia borrarse a quien hubiera escrito en su
propia lista). Falta **el boton en Ajustes** y **poder echar a otra persona**, que hoy
no existe ni en la API ni en la interfaz.

### 1.7 El canal de vectores: apagado a proposito

Sube el recall de **65 % a 73 %** y **rompe los conflictos de asignacion de 0 a 861**.
Esta apagado (`USAR_VECTORES = False` en `projects/cesta/emparejar.py`), con la
medicion escrita al lado. El arreglo: que sus candidatos pasen por **el mismo reparto
y el mismo `ocupados`** que los otros dos canales, porque hoy `enlaces()` le da su
propio reparto hungaro y el 1-a-1 se respeta dentro del canal y no entre canales. Y
despues **volver a medir las dos columnas**: recall **y** conflictos.

---

## 2. Las rondas

Dos goals, 30 rondas. Las 24 primeras ejecutaron `docs/PLAN-UI-MATCHING.md`; las 6
ultimas, `docs/TAREAS-22SEP.md`.

### Goal 1 — `PLAN-UI-MATCHING.md`, rondas 1 a 24

Estas no las recuerdo una a una (la sesion se compacto). El registro durable son los
commits y `docs/DIAGNOSTICO-MATCHING.md`, que es donde estan los numeros. Lo que se
hizo, por fases del plan:

| Fase | Que se hizo | El numero |
|---|---|---|
| 0 | `docs/DIAGNOSTICO-MATCHING.md`, el informe con la medida del tope | |
| 1 | Equivalencias versionadas: `producto_id`, `ejecucion_id`, una carpeta por pasada | |
| 2 | El dato de formato: unidad por 100 g/ml por cadena, cantidad fiable | `--medir` 57 % -> **65 %** |
| 3 | Embeddings (bge-m3 por Ollama, coseno EN SQL) medidos contra el banco de pares | precision **0,90**, recall **0,89** |
| 4 | Asignacion hungara 1-a-1 en vez de eleccion mutua | grupos comparables 6.431 -> 7.997 |
| 5 | **No se empezo**: el prior medido decia que no puede separar lo que las otras no separan | |
| 8 | Auto-etiquetado con EAN: **descartado midiendo** | ningun rasgo separa aciertos de errores |
| 9 | LLM local para los pares ambiguos: **descartado midiendo** | prompt estricto: 100 % negativos |
| 10 | Front nuevo (Vite+React+TS+Tailwind+TanStack+uPlot) | compila a `web/dist` |
| 11 | Ampliar la API sin duplicarla: `/api/ean`, `/api/panel/matching`, `marca`, `producto_id` | 200 en produccion |

En el camino se midieron y **se descartaron con numeros**: IDF por pasillo, el peso de
los trigramas a 0,80, subir el umbral de union (mataba `calidad` 12.996 -> 5.546), la
version dura del freno de grupo, y el criterio "menos de 150 grupos anchos" -- que
resulto estar mal especificado y esta demostrado en `§17` del informe.

Y tres correcciones a mis propias afirmaciones, que quedan escritas porque son la
clase de error que este proyecto persigue:

- Dije "con `sorted`, 22.702 las dos veces" y no era verdad (22.702 y 22.705).
- Dije que el tamano de lote causaba el 400 de los embeddings: **refutado midiendo**.
- Retire el criterio de grupos anchos con ejemplos elegidos a mano. **Me equivoque**:
  ver §1.1, la distribucion entera dice lo contrario de lo que decian mis ejemplos.

### Goal 2 — `TAREAS-22SEP.md`, rondas 25 a 30

**Ronda 25 — los ejes contradictorios: el instrumento.** No habia con que medir la
condicion "cero grupos con eje contradictorio", asi que lo primero fue construirlo:
`core/atributos.py` (los ejes que **el nombre declara**, con la regla de que el que
calla no bloquea) y `projects/cesta/ejes.py` (el comando). Medido: **54 grupos con eje
contradictorio**, 74 de 11+, 5 de esos grandes. Los peores: el 2532 (43 productos,
`virgen` con `virgen extra`), el 294 (34, `oliva suave` con `orujo`), el 8087 (13, con
y sin azucar), el 3684 (13, blanco con integral), el 1116 (11, tres valores de
aceite). Ocho pruebas, y una de ellas encontro un fallo clasico en mi propio codigo:
`desnatad` casa dentro de `semidesnatad`, asi que la leche semidesnatada se leia como
"sin grasa" (el mismo fallo de subcadenas que la auditoria del 17 encontro dos veces).
Trinquete con techos 54 y 74.

**Ronda 26 — el pack no es la unidad.** Segunda dimension, que no estaba en ningun
diagnostico: **615 grupos mezclan un pack con unidades sueltas**, 21 de ellos de 11+.
Los ejemplos de la revision salen exactos (grupo 444 con unidades [1, 6], grupo 6182
con [1, 6, 12, 18]). Y el hallazgo util: **el instrumento del pack caza lo que el de
los ejes no ve** -- el grupo de las 84 cervezas es [1, 12], porque nadie escribe "con
alcohol" en una cerveza y el eje nunca llega a tener dos valores. Los techos pasan a
cuatro: 54, 74, 615, 21. En la misma ronda se commitearon `docs/DISENO.md` (1.250
lineas, medidas en un navegador real) y `docs/TAREAS-22SEP.md`.

**Ronda 27 — el contraste.** Los dos fallos de mas valor del estudio, arreglados:
la letra pequeña sobre el fondo de pagina (**4,35 -> 7,17**, minimo 4,5) en **29
sitios** (el estudio midio una muestra de 13), y el boton principal en oscuro
(**4,10 -> 5,93**), incluido su hover, que estaba en **2,77** y que el estudio no
llego a medir. Los contrastes los calcule yo con la formula de WCAG, no copiados. Y
`tests/test_contraste.py`, que **calcula** en vez de prohibir cadenas. En esta ronda
se me colo un BOM en 10 ficheros y lo quite antes de commitear.

**Ronda 28 — el limite de un campo y su marcador.** El borde de un campo estaba en
**1,48:1** (minimo 3) y su marcador en **2,54** (minimo 4,5) -- y en el buscador el
marcador es **la unica etiqueta visible**, porque el `<label>` es `sr-only`. Ahora
**4,74** y **7,81**. Afecta a todos los campos de la aplicacion. **Aqui commitee una
prueba en rojo sin darme cuenta** y tarde dos commits en verlo; la prueba tardo tres
versiones en medir lo que decia medir (la primera cogia el borde de una tarjeta).

**Ronda 29 — la cabecera.** El enlace de inicio media **43x28** (minimo 44) y la edad
del dato daba **3,74:1** en oscuro. Arreglados los dos. Y esa linea no es decorativa:
dice **de cuando es el precio**, que es la regla que atraviesa toda la interfaz.

**Ronda 30 — la barra de aceptacion, escrita.** Sus cinco condiciones con el comando
que reproduce cada una y el valor de hoy, en el BACKLOG (§0). Antes estaba repartido
entre scripts de `data/debug/` y mensajes de commit.

---

## 3. Las trampas, para no repetirlas

1. **Una columna no es una medida.** Lo que paso el 22: el recall subio y los grupos
   se fundieron peor. Cinco condiciones juntas, o no vale.
2. **El margen no es el cuchillo** (§1.1). Cortar por margen borra los hallazgos de
   28x, que son los que justifican la aplicacion.
3. **Un ejemplo no es una distribucion.** Retire el criterio de grupos anchos con
   pocos casos elegidos a mano, y la distribucion entera me desmintio.
4. **`enlaces()` usa los vectores segun un parametro, y el defecto importa.** Estuvo
   en `True` y cualquier llamada se metia en un camino de horas sin decirlo, la tarea
   de las 06:00 incluida.
5. **Lo que no da error hay que probarlo**: 27 clases de color que Tailwind omitia en
   silencio, `crypto.randomUUID` que no existe en http, campos a 14 px que hacen zoom
   en Safari, y una interfaz que avisaba a Google cada vez que alguien la abria.
6. **Una prueba puede medir otra cosa de la que dice.** Me paso tres veces con la del
   borde, y una con la de la medicion (`resumen()` sin `--peores`).
7. **Los numeros de los documentos caducan**: `uv run python -m projects.cesta.verificar_docs`
   lo dice, y `docs/CIFRAS.md` se regenera con `projects.cesta.cifras`.
8. **`catalogo_actual()` lee silver, no gold**, y `huella_catalogo` firma
   `(fuente, id_fuente)` -- **que productos hay y en que orden, no lo que dicen**.
   Por eso dos pasadas con la misma huella pueden dar numeros distintos.

## 4. Lo que NO hay que rehacer

- **El front**: paridad resuelta (escribir en la cesta, registro, compartir con
  enlace, favoritos, ajustes) y compilando a `plataforma/web/dist`.
- **`/api/ean/{codigo}` y `/api/panel/matching`**: existen y responden 200 en
  produccion. El inventario que dice lo contrario esta caducado.
- **Darse de baja**: la API funciona.
- **La explicabilidad** del emparejamiento (`explicacion` en `/api/grupo`).
- **`candidatos()`**: lee los vectores en SQL (239,9 s y 270 MB, donde antes no
  terminaba en 62 minutos). Ese trabajo se queda aunque el canal este apagado.
- **La privacidad**: ninguna interfaz carga nada de un tercero, y hay pruebas.
- **El contraste** del texto y de los limites, con las formulas dentro de las pruebas.
- **`docs/COMPETENCIA-IMPLANTABLE.md`** (127 funcionalidades de ~50 apps, 17 fichas
  listas para implementar, N29-N39) y **`docs/DISENO.md`** (33 mejoras medidas).

## 5. La barra de aceptacion, y donde esta hoy

    condicion                                   hoy
    pruebas verdes                              682 pasan, 0 fallan   CUMPLE
    --medir >= 57 %                             65 %                  CUMPLE
    cero grupos con eje contradictorio          54                    NO
    menos de 30 grupos de 11+ productos         74                    NO
    las cinco cadenas con bronze del mismo dia  por comprobar

Y las dos cifras que explican las dos que fallan:

    grupos que mezclan un pack con sueltas      615
    de esos, de 11 o mas                          21
