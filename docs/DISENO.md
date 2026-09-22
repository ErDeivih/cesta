# Cesta — el diseño, con las medidas hechas

Escrito el **23 de septiembre de 2026**, después de leer los tres recursos que
pasó el dueño y de **medir la interfaz que existe hoy**, no una ideal.

Los tres recursos, y el día en que se miraron:

    vibeui.online                                   23 sep 2026
    styles.refero.design/ai-agents/design-md-examples 23 sep 2026
    github.com/context-dot-dev/designmd-supply      23 sep 2026

Este documento no resume los recursos: saca de ellos lo que se puede aplicar
**aquí**, y descarta el resto con el motivo. Lo descartado está en el punto 6, con
la cita.

Lo que dice el encargo y este documento **no** contradice: no hay chat ni
asistente (`docs/APP.md:395-410`), no entra ningún servicio externo ni ninguna
llamada a un modelo desde el front (`docs/APP.md:56-105`), no hay validación
humana (`docs/PANTALLAS.md:314-324`), un dato que no tenemos es «no lo sé»
(`docs/APP.md:147-166`), la calidad no sale del precio (`docs/BACKLOG.md:46-49`),
la barra de abajo tiene cuatro destinos y no se toca (`docs/USABILIDAD.md:89-107`).

---

## 0. Cómo se ha medido

Para que cualquiera pueda repetirlo o discutirlo.

    contrastes      calculados con la fórmula de WCAG 2.1 (luminancia relativa,
                    canal a canal, umbral 4,5:1 para texto normal y 3:1 para
                    texto grande y para el límite de un control)
    colores         los valores de `tailwind.config.js` y `src/estilos.css`; los
                    de Tailwind 3, de su paleta por defecto
    navegador       Chromium sin cabeza, ventana de 390 x 844 (un móvil de pie),
                    dos pasadas: `prefers-color-scheme: light` y `dark`, contra
                    el build de `plataforma/web/dist`
    red             `/api/**` cortada a propósito, para ver el estado «sin
                    conexión con casa» que pide `docs/PANTALLAS.md:151-157`
    peso            `npm run build` en `plataforma/web/app`
    zonas de pulsar medido el rectángulo del navegador, y cuando el control vive
                    dentro de un `<label>` se mide el `<label>`, que es el
                    objetivo de verdad
    orden de tabulación 60 pulsaciones de tabulador seguidas, apuntando dónde
                    cayó el foco

**Lo que NO está medido** está dicho donde toca y otra vez en el punto 7.

---

## 1. Los tokens

### 1.1 Lo que ya existe, y no se duplica

Esto ya está y no se toca:

    los seis colores con significado    tailwind.config.js:27-32 (los nombres)
                                        estilos.css:14-21 (claro)
                                        estilos.css:23-32 (oscuro)
                                        test_interfaz.py::test_colores_conocidos
    la fuente del sistema               tailwind.config.js:15-20
    el ancho de la app                  tailwind.config.js:34-38 (78rem)
    el fondo y la tinta de la página    index.html:13
    las cifras tabulares                estilos.css:49-51 (`.cifra`)
    el anillo de foco                   estilos.css:53-55
    el scroll horizontal de tabla       estilos.css:59-64

Los seis nombres con significado —`tinta-suave`, `fondo`, `borde`, `aviso`,
`bien`, `bien-suave`— **cambian con el tema y se usan sin `dark:`**. Cualquier
token nuevo que signifique algo tiene que hacer lo mismo, o se rompe la regla que
`docs/APP.md:345-358` explica y que ya costó un fallo real.

### 1.2 La escala de espaciado

**De dónde sale:** de Tailwind, que ya trae base de 4 px. Hoy se usa a pelo, sin
decidir nada. Los valores que aparecen en las pantallas:

    gap-0.5  2px     gap-1  4px     gap-2  8px     gap-3 12px    gap-4 16px
    p-2      8px     p-3   12px     p-4   16px     py-8  32px

**Lo que se propone:** no se inventa escala, se **cierra** a seis pasos y se les
da un papel. Lo que no esté en esta tabla, no se usa.

    paso   valor   papel
    1      4px     separación entre una etiqueta y su dato
    2      8px     separación dentro de un bloque (entre los botones de una fila)
    3      12px    separación entre bloques de una misma tarjeta
    4      16px    relleno de tarjeta y separación entre tarjetas
    6      24px    separación entre secciones de una pantalla
    8      32px    relleno de un estado vacío

**Dónde se declara:** en un comentario del bloque `theme.extend` de
`plataforma/web/app/tailwind.config.js`, al lado del que ya explica la paleta
(`tailwind.config.js:21-26`). **No** se declaran alias en `theme.spacing`: los
alias de Tailwind para los mismos píxeles son una segunda copia que se queda
vieja.

**Lo que hoy no cumple y se corrige:**

    p-3 en los mismos sitios que p-4   FiltrosBusqueda.tsx:66 y Grupo.tsx:299
                                       usan p-3 para la misma caja blanca que
                                       ui.tsx:116 y ControlPesos.tsx:53 hacen
                                       con p-4. Son la misma cosa: p-4.
    pb-28 en el armazón                App.tsx:26 reserva 112 px (7rem) para una
                                       barra que mide 57 px (medido: 91x56 por
                                       destino más el borde de arriba). Los 55 px
                                       que sobran son un hueco muerto al final de
                                       todas las pantallas. Pasa a `pb-[64px]`,
                                       que deja 7 px de aire.

### 1.3 La escala de tipografía

**De dónde sale:** de Tailwind, y hoy hay cuatro escalones con tres significados.
Los tamaños en uso son `text-xs` 12, `text-sm` 14, `text-base` 16, `text-lg` 18,
`text-xl` 20, `text-2xl` 24.

**Lo que se propone:** cuatro escalones, y el papel de cada uno. El quinto no
existe.

    escalón        clase                 cuándo
    cifra grande   text-2xl font-semibold  el único número que decide algo en
                   + .cifra                esa pantalla, uno por pantalla
    título         text-xl font-semibold   el `<h1>`, uno por pantalla
    título de caja text-base font-semibold el `<h2>` de una tarjeta o una columna
    cuerpo         text-sm (14)            todo lo demás, con `text-tinta-suave`
                                           para lo secundario
    meta           text-xs (12)            fecha, procedencia, «no lo sé»

**Dónde se declara:** el mismo comentario de `tailwind.config.js`. Y **ningún
tamaño en píxeles crudo**: ya no hay ninguno, y no se añade.

**Lo que hoy no cumple y se corrige:**

    el h1 tiene dos pesos:            font-bold en Escaner.tsx:142, Panel.tsx:48,
                                       Producto.tsx:170 y Grupo.tsx:213;
                                       font-semibold en Cesta.tsx:781,
                                       Favoritos.tsx:77 y Ajustes.tsx:62.
                                       Se queda font-semibold en los siete.
    el h1 falta en tres pantallas      medido: `/`, `/cesta` y `/ajustes` tienen
                                       h1=0. El buscador es la pantalla de
                                       entrada y no tiene ni título ni encabezado.
    la cifra grande tiene tres formas  Cesta.tsx:251,302,829 y Escaner.tsx:261 la
                                       ponen a text-2xl (una en bold y dos en
                                       semibold) y Grupo.tsx:508 a text-lg en
                                       bold. Se queda text-2xl font-semibold.
    el h2 y el h3 miden lo mismo       en Cesta.tsx:826 el h2 es text-base y en
                                       Cesta.tsx:243,295 el h3 también, mientras
                                       que el h3 de Cesta.tsx:552,606,648 es
                                       text-sm. Tres niveles, dos tamaños.
    el `<title>` es igual en todas     index.html:8 pone «Cesta» siempre. Medido
                                       en las nueve rutas: el título nunca cambia.

### 1.4 Los radios

**De dónde sale:** de Tailwind, y hoy hay cinco para tres cosas.

    rounded      4px    Td/Th/etiquetas de letra (Etiquetas.tsx:40)
    rounded-md   6px    Etiqueta (ui.tsx:89) y **cinco campos de entrar**
                        (Cesta.tsx:89,99,156,168,180) más el selector de lista
                        (Cesta.tsx:786)
    rounded-lg   8px    botón, casilla, selector, campo (ui.tsx:50,195,236,264)
    rounded-xl  12px    tarjeta (ui.tsx:116), vacío (ui.tsx:297) y **los dos
                        campos grandes** (Buscar.tsx:113, Escaner.tsx:170)
    rounded-full        solo los chips de cadenas (Ajustes.tsx:94)

**Lo que se propone:** tres, y `rounded-full` solo donde el chip ya está.

    campo y control     rounded-lg  (8px)
    tarjeta             rounded-xl  (12px)
    etiqueta y sello    rounded-md  (6px)

**Dónde se declara:** el mismo comentario de `tailwind.config.js`.

**Lo que hoy no cumple y se corrige:** el mismo papel —un campo de texto— tiene
tres radios: `rounded-md` en el formulario de entrar (Cesta.tsx:89), `rounded-lg`
en `CampoTexto` (ui.tsx:264) y `rounded-xl` en el buscador (Buscar.tsx:113) y en
el del escáner (Escaner.tsx:170). El buscador es el campo que más se usa de toda
la app.

### 1.5 Las sombras

**Lo que hay:** una sola, `shadow-sm` en ui.tsx:116 (la tarjeta). En modo oscuro
no se ve: debajo de una tarjeta `#262626` está la página `#171717`, y una sombra
negra sobre casi negro no existe.

**Lo que se propone: ninguna.** Se quita `shadow-sm`. La separación la hacen el
borde y el escalón de color. En claro el borde de la tarjeta ya separa (calculado:
`#e5e5e5` sobre `#f5f5f5` = **1,16:1**, y el relleno blanco sobre la página
**1,09:1**): la sombra no añade nada que esos dos números no hagan ya, y en
oscuro sí que no añade nada. Ver el punto 6: esto **sí** se adopta de los
recursos, y el motivo no es el gusto, es que hoy no pinta nada.

**Dónde se declara:** no se declara, se borra de ui.tsx:116.

### 1.6 Los tiempos de animación

**Lo que hay:** uno, `transition-colors` en ui.tsx:50, con la duración por
defecto de Tailwind (150 ms). Y ni un `@media (prefers-reduced-motion)` en todo
el front: buscado en `plataforma/web/app/src`, **no aparece ninguna vez**.
`docs/USABILIDAD.md:123` dice que «`prefers-reduced-motion` ya está puesto». No
está: ese documento hay que corregirlo, o la próxima persona que lea tocará un
ajuste que no existe.

**Lo que se propone:** dos duraciones, y solo dos, declaradas como variables en
`estilos.css` y mapeadas en `tailwind.config.js`:

    --dur-corta   120ms   un cambio de color (el botón al hundirse, el chip al
                          marcarse). Nada se mueve.
    --dur-media   200ms   algo que aparece: el aviso de «sin conexión con casa».

Y la regla que va con ellas, porque es la que importa en la tienda: **ninguna
animación puede retrasar el cambio de estado**. Tachar una línea se pinta con el
dedo, no cuando la transición acabe. Hoy ya se cumple (Cesta.tsx:727-739 recarga
del servidor), así que no se añade ninguna animación que lo rompa.

`prefers-reduced-motion` se añade en el mismo cambio que la primera transición
que mueva algo, no antes: hoy no hay nada que reducir.

### 1.7 Los colores

**Los seis con significado no se duplican.** Se quedan como están, y este
documento solo dice dónde se usan bien y dónde mal (punto 4).

**Lo que se propone:** **un solo color nuevo**, y porque hace falta.

    nombre        claro      oscuro     dónde se declara
    campo-borde   #737373    #a3a3a3    estilos.css:14-21 y :23-32 (los dos
                                       temas) + tailwind.config.js:21-33 (el
                                       nombre, como var) + la lista de
                                       test_interfaz.py::test_colores_conocidos

Por qué hace falta: el límite de un campo de texto hoy es `border-neutral-300`
(`#d4d4d4`), que sobre blanco da **1,48:1** y sobre el fondo de página
**1,36:1**. WCAG 1.4.11 pide **3:1** para la información visual necesaria para
identificar un control. El campo de entrar es peor: `border-borde` (`#e5e5e5`)
sobre `bg-fondo` (`#fafafa`) = **1,21:1**. Con el token nuevo: **4,74:1** en
claro y **6,00:1** en oscuro.

Y **no** se añade ningún color más: ni un acento, ni un color de marca, ni un
color por cadena. La paleta corta es una decisión (`tailwind.config.js:6-8`) y
este documento no la abre.

### 1.8 Dónde se declara cada cosa nueva

| qué | valor | dónde |
|---|---|---|
| `--campo-borde` (claro) | `#737373` | `src/estilos.css`, `:root` |
| `--campo-borde` (oscuro) | `#a3a3a3` | `src/estilos.css`, `@media (prefers-color-scheme: dark)` |
| el nombre `campo-borde` | `var(--campo-borde)` | `tailwind.config.js`, `theme.extend.colors` |
| la prueba del color nuevo | añadirlo a la lista | `tests/test_interfaz.py::test_colores_conocidos` |
| la escala de espaciado | los seis pasos | comentario en `tailwind.config.js`, `theme.extend` |
| los cuatro escalones de tipo | la tabla de 1.3 | el mismo comentario |
| los tres radios | la tabla de 1.4 | el mismo comentario |
| `--dur-corta` / `--dur-media` | `120ms` / `200ms` | `estilos.css` + `transitionDuration` |
| cero sombras | — | se borra `shadow-sm` de `ui.tsx:116` |

Nada de esto cambia un solo valor de los seis colores existentes. Si alguien
propone cambiar `--tinta-suave`, que traiga antes el número de contraste.

---

## 2. Las reglas de composición

### 2.1 Cuándo una tarjeta y cuándo una lista

**Una tarjeta es una unidad que se lee entera y se puede ignorar entera.** En la
tienda se mira una tarjeta y se pasa a la siguiente. Por eso:

    tarjeta   cuando el contenido tiene un título propio y un total propio:
              una cadena con su precio (Cesta.tsx:241), un favorito con su
              precio (Favoritos.tsx:88), una columna de cadena en el grupo
              (Grupo.tsx:296), un bloque del panel (Panel.tsx:134)
    lista     cuando son filas de lo mismo, sin título cada una, y lo que se
              hace es recorrerlas: las líneas de la cesta (Cesta.tsx:882, hoy un
              `<ul>`), las personas de una lista (Cesta.tsx:432), los rasgos de
              un par (PanelMatching.tsx:234)

**Lo que hoy no cumple:** en el buscador hay **cuatro cajas blancas seguidas**
antes del primer resultado —la fila del campo, `FiltrosBusqueda`, la fila de
vistas guardadas y, si no hay texto, la caja de puntos del vacío— y ninguna es una
unidad con título y total. Se ven en la foto: un campo blanco, una caja blanca
«Filtros», un botón blanco y una caja de puntos; cuatro bordes de **1,16:1**
(calculado) que no separan nada, porque son todos del mismo color que el fondo. Se
quedan **sin tarjeta**: el campo y los filtros son la misma cosa (lo que se escribe
y cómo se acota) y van dentro del mismo bloque.

### 2.2 Cuándo una tabla y cuándo un mosaico

    tabla     cuando hay que comparar un número de la misma clase entre filas:
              cinco cadenas y su precio por unidad (Escaner.tsx:293,
              Producto.tsx:293), los resultados de una búsqueda
              (TablaResultados.tsx:172), cualquier cosa del panel
    mosaico   cuando son cosas que se reconocen por la foto y se pulsan para
              añadirlas, sin comparar números entre ellas: los favoritos
              (Favoritos.tsx:83), el mosaico de habituales que aún no existe
              (`docs/API.md:380`, bloqueado, ver punto 3)

**Lo que hoy no cumple:** las tablas usan **siete anchos mínimos distintos** para
el mismo componente: 24, 26, 34, 40, 44, 46 y 52 rem (Panel.tsx:318,392,198,135,
432,524 y TablaResultados.tsx:172). Tres son suficientes:

    minAncho="24rem"   dos columnas de números
    minAncho="34rem"   cuatro columnas
    minAncho="52rem"   seis columnas o más (la tabla de resultados)

Y la tabla del buscador (`minAncho="52rem"`, que son **832 px**) se pinta dentro de
una ventana de móvil de 390 px: se ve menos de la mitad y hay que deslizar para
llegar a «Ahorro», que es la columna por la que se ordena. Eso no se arregla con un
ancho:
se arregla moviendo **Ahorro** y **Por unidad** a la izquierda, porque son las dos
columnas que deciden, y dejando «Marca» y «Dónde» para el final.

### 2.3 Cuántos niveles de jerarquía, como máximo

**Tres, más el nivel meta.** Un cuarto nivel visible en una pantalla de 390 px no
se lee, se salta:

    1  el h1 — en qué pantalla estoy
    2  el h2 — de qué caja
    3  el cuerpo — el dato
    meta  text-xs con text-tinta-suave — de cuándo es, de dónde sale, «no lo sé»

**Lo que hoy no cumple:** la ficha de producto tiene **cinco** escalones visibles
a la vez —`text-xl font-bold` (Producto.tsx:170), `text-base font-semibold`
(ui.tsx:123), `text-sm font-semibold` (Producto.tsx:398), el `text-xs uppercase
tracking-wide` de `Dato` (ui.tsx:173) y el `text-xs text-neutral-500`
(Producto.tsx:217,279)— y la cesta cuatro, con dos de ellos midiendo lo mismo. La
ficha del producto es la pantalla donde más se nota: `Dato` mete un nivel propio
para cada etiqueta de la rejilla.

Regla concreta para `Dato` (ui.tsx:172-179): la etiqueta va en **meta** (`text-xs
text-tinta-suave`, sin mayúsculas y sin `tracking-wide`, que en mayúsculas
espaciadas a 12 px se lee peor) y el valor en **cuerpo**. Así la ficha baja de
cinco escalones a cuatro sin perder un dato.

### 2.4 Dónde va la acción principal de cada pantalla

**Abajo, al alcance del pulgar, y una sola vez.** `docs/PANTALLAS.md:14-15`:
«Se usa con una mano y el carro en la otra. Navegación abajo. Nada importante en
la esquina superior.» El pulgar de una mano llega al tercio inferior; la esquina
superior la alcanza la otra mano, que está sujetando el carro.

    pantalla        acción principal                     hoy
    /               escribir en el buscador              arriba del todo ✓ (el
                                                          campo tiene el foco
                                                          visual y es lo primero)
    /grupo/:id      añadir el grupo a la cesta           **arriba a la derecha**
                                                          (Grupo.tsx:212-218)
    /producto/...   ninguna: es una pantalla de lectura  —
    /escaner        buscar el código                      arriba ✓ (es un
                                                          formulario de un campo)
    /cesta          tachar la línea que se coge           en la lista ✓
    /favoritos      quitar de favoritos                   ✓
    /ajustes        marcar las cadenas de casa            ✓
    /panel          ninguna (es de lectura)               —
    /panel/matching ninguna (es de auditoría)             —
    /unirme/:codigo entrar                               ✓

**Lo que hoy no cumple:** `/grupo/:id` es la pantalla que existe para una sola
cosa —añadir el grupo a la cesta— y su botón está arriba a la derecha, junto a
«Guardar», en la cabecera. Es lo contrario de la regla que el propio proyecto
escribió. Se mueve a una **barra pegajosa encima de la barra de abajo**, con el
precio por unidad de la alternativa que gana y el botón. Ver el punto 6: esto es
lo único que se adopta de la librería de `vibeui.online` («Sticky bottom bar»,
`cta-3`) y lo que se adopta es la colocación, no el patrón: no hay mensaje de
venta, no hay «descartar» y no se puede cerrar, porque no es una promoción, es la
acción de la pantalla.

---

## 3. Los estados, uno por uno

Los cuatro estados que `docs/PANTALLAS.md:21-27` exige por pantalla. Lo que hay
hoy, con la línea, y lo que falta.

### 3.1 Los estados vacíos, y la diferencia que importa

«No hay nada» y «no hay nada **con estos filtros**» son dos problemas distintos y
se arreglan de forma distinta. En el buscador **ya se distinguen**, y bien: tres
ramas separadas en `Buscar.tsx:184-212` (con filtros → «Quita los filtros» y el
botón al lado; con texto → «prueba una palabra más corta»; sin texto y con
pasillo → «este pasillo está vacío»), más los tres ejemplos pulsables del estado
vacío de entrada (`Buscar.tsx:145-152`). No se toca.

    pantalla        vacío hoy                                        falta
    /               tres ejemplos pulsables (Buscar.tsx:135-154) ✓  —
    /cesta          «La lista está vacía» + qué hacer (Cesta.tsx:871) ✓  —
    /cesta (sin listas)  «No tienes ninguna lista» + qué hacer (Cesta.tsx:765) ✓  —
    /cesta (dónde)  «No puedo decir dónde» (Cesta.tsx:927) ✓        —
    /favoritos      dice QUÉ son, no CÓMO añadir uno (Favoritos.tsx:63-72)  ver 3.4
    /grupo          «Este grupo no tiene ningún producto con precio»
                    (Grupo.tsx:283) ✓                               —
    /escaner        «Escribe o pega un código» + para qué (Escaner.tsx:344) ✓  —
    /panel          «Hoy no se ha movido nada» (Panel.tsx:430) ✓     —
    /panel/matching «No hay ninguna pasada guardada» + cómo se llena
                    (PanelMatching.tsx:67-76) ✓                      —
    /ajustes        no tiene vacío propio                            —
    /unirme         no tiene vacío propio                            —

### 3.2 Cargando

`Cargando` (ui.tsx:272-278) es un `<p role="status">` con texto. Está en las
nueve pantallas. Está bien que sea texto y no una rueda: dice **qué** está
cargando («Cargando tu sesión», «Cargando el catálogo», «Cargando la lista»).

**Lo que falta:** el buscador tarda 250 ms a propósito antes de salir a la red
(`Buscar.tsx:66-72`) y mientras tanto no se ve nada. Se ve el resultado anterior,
que es lo correcto. Pero cuando **no hay** resultado anterior, el estado de
cargando aparece después de medio segundo de pantalla quieta. Falta que la
primera carga diga algo desde el primer fotograma: la etiqueta «actualizando…»
(`Buscar.tsx:173`) ya existe, pero solo cuando ya había datos.

### 3.3 El error de red

`Fallo` (ui.tsx:280-293) ya trae el texto de `textoDeError` y un botón «Volver a
intentarlo». Medido en el navegador con `/api/**` cortado: sale bien, y el mensaje
es el correcto —«Sin conexion con casa. Esto es lo ultimo que hay en pantalla»
(`api/cliente.ts:41-44`)—. Sin embargo:

    /cesta     `listas.isError` usa `Vacio`, NO `Fallo`: dice el error y **no da
               el botón de reintentar** (Cesta.tsx:759-763)
    /favoritos `favs.isError` igual (Favoritos.tsx:54-60)
    /panel     bien, usa `Fallo` vía `Bloque` (Panel.tsx:98-100) ✓

Dos sitios donde la aplicación dice lo que ha pasado y no deja hacer nada al
respecto, teniendo el componente que lo hace escrito al lado.

**Lo que falta, y es el estado más importante de todos:** «sin conexión con casa».
`docs/PANTALLAS.md:151-157` pide que la cesta diga que **lo que cambies se
guardará** y cuántos cambios hay pendientes. Hoy lo único que hay es el mensaje de
la mutación que falló (`Cesta.tsx:815-827`: «No he podido guardar el cambio. La
lista sigue como estaba»), que es correcto pero aparece **después** de intentarlo,
y el aviso de la cabecera (`Cabecera.tsx:30-34`: «No sé de qué día son los
precios: la API no contesta»), que habla de las fechas y no de la lista. Medido y
visto en la foto: con la red cortada, la primera pantalla dice que no sabe de qué
día son los precios, y nada más.

Y hay una decisión escrita que esto **no** cambia: la cola de cambios sin conexión
se descartó a propósito (`Cesta.tsx:17-22`: pintar un cambio que el servidor no ha
aceptado mentiría sobre la lista de la compra). Así que el estado no puede
prometer «se guardará»: tiene que decir la verdad de esta implementación —
«lo que hagas ahora no se guarda»— y eso es una decisión del dueño, no del
diseño.

### 3.4 Sin sesión

    /cesta      la puerta con los dos formularios (Cesta.tsx:206-230) ✓
    /favoritos  «Entra para ver tus favoritos» + enlace a la cesta
                (Favoritos.tsx:43-52) ✓
    /ajustes    «Entra para cambiar tus ajustes» y **ni un enlace ni un botón**
                (Ajustes.tsx:42-48)
    /unirme     la misma puerta (Unirse.tsx:85-110) ✓

**Medido:** en `/ajustes` sin sesión hay **cero** elementos interactivos en el
contenido. Se cuentan seis en toda la pantalla y los seis son de fuera: el enlace
de la marca (cabecera) y los cuatro de la barra de abajo. La pantalla dice «hacen
falta tus listas» y no hay por dónde. Y como `/ajustes` no tiene ningún enlace en
toda la aplicación (ver 3.6), el camino completo es: escribir la dirección a mano,
leer que hay que entrar, y volver a escribir otra dirección a mano.

### 3.5 Sin datos de hoy, y el dato viejo

Esta es la regla que más veces se repite en los documentos
(`docs/APP.md:147-166`, `docs/PANTALLAS.md:26-27`): un precio de más de
`dias_precio_valido` días **se enseña con su fecha y no decide**.

    dónde se cumple hoy
    /grupo       por cadena: «al día» o «precio del <fecha>» (Grupo.tsx:304-308),
                 y cada alternativa que no decide dice por qué y cuántos días
                 tiene (Grupo.tsx:101-107, 558-564) ✓
    /grupo       precios sin fecha: se dice y no se puede fechar (Grupo.tsx:273-278) ✓
    /producto    la fecha de los datos en la cabecera del grupo (Producto.tsx:176) ✓
    /cesta       la fecha de los datos va una vez, en su tarjeta (Cesta.tsx:846) ✓
    cabecera     la fecha de los datos y las cadenas con retraso, siempre a la
                 vista (Cabecera.tsx:35-53) ✓

    dónde falta
    /            la tabla de resultados ordena por precio y **no dice de qué día
                 es cada precio**. Un grupo cuyo último precio es de hace cuatro
                 días se pinta igual que uno de hoy. Se sabe que la API lo manda
                 (`/api/estado`, `cadenas[].ultimo_dia`), porque el grupo ya lo usa.
    /favoritos   igual: el precio de hoy no lleva fecha (Favoritos.tsx:107-111)

Y falta el estado «los datos no son de hoy» como **estado**, no como etiqueta: si
`fecha_datos` es de anteayer, la cabecera muestra una fecha y nada más. Lo que
pide el proyecto es que eso se note antes de mirar los precios, no con una etiqueta
de 12 px a la derecha.

### 3.6 Los estados que no existen porque la pantalla no se puede alcanzar

**Medido, y es el hallazgo más tonto y más caro de este documento:** `/favoritos`
y `/ajustes` existen, están escritos y probados, y **no hay ni un solo enlace a
ninguno de los dos en toda la aplicación**. Buscado `to="/favoritos"` y
`to="/ajustes"` en `plataforma/web/app/src`: cero coincidencias. Las dos pantallas
solo se abren escribiendo la dirección.

Un favorito no se puede añadir desde la interfaz nueva (`Favoritos.tsx:10-12` lo
dice). Y «las cadenas que tengo cerca» —el único ajuste que cambia lo que sale en
el buscador— está en una pantalla a la que no se llega, mientras el propio panel de
filtros dice «o tus cadenas de casa si las tienes guardadas»
(`FiltrosBusqueda.tsx:104-108`) sin decir dónde se guardan.

Eso no es un estado que falte: es que la pantalla del ajuste está desconectada. Se
arregla con dos enlaces, y el sitio del primero ya está escrito: la frase de
`FiltrosBusqueda.tsx:104-108` es exactamente donde alguien busca ese ajuste.

---

## 4. Accesibilidad y móvil, con la comprobación

### 4.1 Contraste: lo que se cumple y lo que no

Umbral de WCAG 2.1 AA: **4,5:1** en texto normal y **3:1** en texto grande
(≥24 px, o ≥18,66 px en negrita) y en el límite de un control. Las columnas
«medido» dicen si el número salió del cálculo o de la pasada del navegador.

**Las que cumplen**

| pareja texto / fondo | ratio | medido |
|---|---|---|
| cuerpo claro `#141618` / `#f5f5f5` | 16,64 | calculado |
| cuerpo oscuro `#f5f5f5` / `#171717` | 16,44 | calculado |
| `tinta-suave` claro `#525252` / `#fafafa` | 7,49 | calculado |
| `tinta-suave` claro `/ #ffffff` | 7,81 | calculado |
| `tinta-suave` oscuro `#a3a3a3` / `#262626` | 6,00 | calculado |
| `tinta-suave` oscuro `/ #171717` | 7,11 | calculado |
| `text-neutral-600` / `#f5f5f5` | 7,17 | calculado |
| `text-neutral-400` / `#262626` (meta en oscuro) | 6,00 | calculado |
| `aviso` `#b45309` / `#ffffff` | 5,02 | calculado |
| `aviso` `#b45309` / `#f5f5f5` | 4,61 | calculado |
| `aviso` oscuro `#fcd34d` / `#262626` | 10,50 | calculado |
| `bien` oscuro `#10b981` / `#262626` | 5,97 | calculado |
| botón principal claro: blanco / `sky-700` `#0369a1` | 5,93 | calculado |
| nav activo claro: `sky-800` / blanco | 7,56 | calculado |
| nav activo oscuro: `sky-300` / `#171717` | 10,75 | calculado |
| enlace sutil oscuro: `sky-300` / `#262626` | 9,08 | calculado |
| `summary` oscuro: `sky-400` / `#262626` | 7,06 | calculado |
| etiqueta aviso claro: `amber-900` / `amber-100` | 8,15 | calculado |
| etiqueta aviso oscuro: `amber-100` / `amber-950` | 13,45 | calculado |
| etiqueta bien claro: `emerald-900` / `emerald-100` | 8,57 | calculado |
| etiqueta info claro: `sky-900` / `sky-100` | 8,24 | calculado |
| etiqueta neutra clara: `neutral-800` / `neutral-200` | 12,01 | calculado |
| caja de aviso clara: `amber-950` / `amber-50` | 14,44 | calculado |
| `amber-800` / `#f5f5f5` (lo que no decide) | 6,50 | calculado |
| `amber-400` / `amber-950` al 30 % sobre `#262626` | 9,21 | calculado |
| verde de ahorro `#065f46` / `#ffffff` | 7,68 | calculado |
| verde de ahorro oscuro `#34d399` / `#262626` | 7,87 | calculado |
| rojo de subida `#991b1b` / `#f5f5f5` | 7,62 | calculado |
| rojo de subida oscuro `#f87171` / `#262626` | 5,47 | calculado |
| botón peligro claro: `red-800` / blanco | 8,31 | calculado |
| botón peligro oscuro: `red-300` / `#262626` | 7,97 | calculado |
| cabecera: ámbar claro / blanco | 5,02 | calculado |
| cabecera: ámbar oscuro / `#171717` | 10,74 | calculado |
| cabecera: verde claro / blanco | 5,48 | calculado |
| cabecera: verde oscuro / `#171717` | 9,33 | calculado |
| `th`: `neutral-600` / `neutral-50` | 7,49 | calculado |
| `th` oscuro: `neutral-300` / `#262626` | 10,21 | calculado |
| foco claro: `ring-sky-600` `#0284c7` / blanco | 4,10 | calculado |
| foco claro `/ #f5f5f5` | 3,76 | calculado |
| foco oscuro: `ring-sky-400` `#38bdf8` / `#171717` | 8,37 | calculado |

El anillo de foco pasa en los dos temas. `docs/USABILIDAD.md:115-116` dice que
«hay `:focus-visible` con el ámbar»: no es ámbar, es azul (`estilos.css:53-55`), y
está por encima del mínimo de 3:1 que pide un indicador de foco.

**Las que NO cumplen**

| # | pareja texto / fondo | ratio | mínimo | dónde | medido |
|---|---|---|---|---|---|
| 1 | `#737373` / `#f5f5f5` — el gris de la letra pequeña sobre el fondo de página | **4,35** | 4,5 | 13 sitios, ver abajo | **sí**: `/escaner`, 12 px |
| 2 | blanco / `sky-600` `#0284c7` — botón principal y chips activos en oscuro | **4,10** | 4,5 | `ui.tsx:28`, `Escaner.tsx:272`, `FiltrosBusqueda.tsx:96,178`, `Panel.tsx:68` | **sí**: `/escaner` y `/panel` en oscuro, 14 y 16 px |
| 3 | `#737373` / `#181818` — «(hace N días)» de la cabecera, en oscuro | **3,78** | 4,5 | `Cabecera.tsx:38` | no: la API estaba cortada y ese texto no se pinta |
| 4 | blanco / `orange-500` `#f97316` — la letra `d` del Nutri-Score | **2,80** | 3,0 | `Etiquetas.tsx:22` | no |
| 5 | blanco / `neutral-400` `#a3a3a3` — la letra del Nutri-Score cuando no hay color | **2,52** | 3,0 | `Etiquetas.tsx:40` | no |
| 6 | placeholder `#9ca3af` / blanco — el texto del buscador | **2,54** | 4,5 | `Buscar.tsx:110`, `Escaner.tsx:169` (preflight de Tailwind, sin corregir en `estilos.css`) | **sí** |
| 7 | borde de campo `#d4d4d4` / blanco | **1,48** | 3,0 | `ui.tsx:236,264`, `Buscar.tsx:113`, `Escaner.tsx:170` | **sí** |
| 8 | borde de campo `#d4d4d4` / `#f5f5f5` | **1,36** | 3,0 | igual que 7, cuando el campo está fuera de una tarjeta | no |
| 9 | borde de campo `border-borde` `#e5e5e5` / `bg-fondo` `#fafafa` — el formulario de entrar | **1,21** | 3,0 | `Cesta.tsx:89,99,156,168,180` | no |
| 10 | borde de campo oscuro `neutral-600` `#525252` / `#262626` | **1,94** | 3,0 | `ui.tsx:236,264` | no |

Y una que pasa por poco y conviene saber por qué: blanco sobre `emerald-600`
`#059669` (la letra `a` del Nutri-Score y el token `--bien`) da **3,77**. Pasa
**solo** porque la letra mide 24 px en negrita. Como texto normal no pasa: `--bien`
no puede usarse nunca como color de texto sobre blanco, solo como borde, que es
como se usa hoy (`Ajustes.tsx:96`).

Los trece sitios del fallo 1, que es el que más se repite:

    Escaner.tsx:189     la explicación del código de barras       medido: 4,35
    ui.tsx:329          «Desliza la tabla para ver todas las columnas»
    ui.tsx:173          la etiqueta de todo `Dato` (dt)
    Grupo.tsx:240,255   «gana contigo» y «los de más de N días no cuentan»
    Grupo.tsx:582,588   el peso y la nota al pie del desglose
    Grupo.tsx:596,630   «no pinto el histórico» y «datos del grupo»
    Producto.tsx:217    de dónde salen los sellos
    TablaResultados.tsx:110,126  «hasta <precio>» y «N productos»
    Chispa.tsx:107      «Sin histórico: solo tenemos un día de este precio»

Los trece están fuera de una tarjeta, sobre el fondo `#f5f5f5`, y todos a 12 o
14 px. **Y son justo el texto que sostiene la credibilidad del proyecto**: la
fecha, la procedencia del sello, el «no lo sé», por qué un precio no decide. Lo
que se lee peor es lo que más importa.

**El arreglo es el token que ya existe:** `text-tinta-suave` da **7,17** sobre
`#f5f5f5` y **7,11** sobre `#171717`. En oscuro ya se usa `neutral-400`, que
resuelve al mismo `#a3a3a3` que el token: el fallo es solo de la mitad clara. Son
trece sustituciones de `text-neutral-500 dark:text-neutral-400` por
`text-tinta-suave`, sin `dark:`.

### 4.2 Área de pulsación

La regla del proyecto es **44 px** (`docs/UX-MOVIL.md:137-139`). Medido en el
navegador, en las nueve rutas, lo que no llega:

| dónde | medido | pantallas |
|---|---|---|
| enlace «Cesta» de la cabecera (`Cabecera.tsx:24`) | **43 × 28** | las nueve |
| `summary` «Estado de las cadenas» (`Cabecera.tsx:61`) | **358 × 24** | ocho |
| botón de ordenar de una columna de tabla (`ui.tsx:380`, `min-h-[32px]`) | 32 de alto | las cinco con tabla |
| «Ficha e histórico» y «Ver en <cadena>» (`Grupo.tsx:612,622`, `min-h-[36px]`) | 36 de alto | `/grupo` |
| botón `×` de una vista guardada (`VistasGuardadas.tsx:53`) | ≈26 × 44 (lo ancho lo pone el glifo) | `/` |
| enlace «la cesta» del vacío de favoritos (`Favoritos.tsx:48`) | **46 × 19** | `/favoritos` |
| enlace «Panel de matching →» (`Panel.tsx:49-54`) | **130 × 20** | `/panel` |
| enlace «Vuelve al buscador» de la ruta que no existe (`App.tsx:48`) | **173 × 39** | 404 |

Y lo que sí cumple, medido, para que nadie lo «mejore»: los cuatro destinos de la
barra de abajo miden **91 × 56** cada uno, y las casillas de la cesta llevan el
nombre dentro del `<label>` (ui.tsx:191-208), así que el objetivo es la fila
entera y no el cuadradito de 16 px. Las dos cosas están bien.

### 4.3 Foco visible

`:focus-visible` está en un solo sitio (`estilos.css:53-55`) y se aplica a todo,
que es lo correcto. Pasa el mínimo de 3:1 en los dos temas (4,10 en claro, 8,37 en
oscuro). Dos problemas de recorte:

    VistasGuardadas.tsx:39  el `overflow-hidden` del contenedor de la vista
                            guardada recorta el anillo, que va `ring-2` **más**
                            `ring-offset-2`: 4 px por fuera del borde. El foco del
                            botón `×` se ve a medias.
    Escaner.tsx:204         el mismo `overflow-hidden` alrededor del vídeo. Ahí no
                            hay nada que enfocar, así que no pasa nada hoy.

### 4.4 Orden de tabulación

Medido, con 60 pulsaciones de tabulador y apuntando dónde cayó el foco:

| pantalla | paradas | dónde está la barra de abajo |
|---|---|---|
| `/` | 12 | paradas 9-12 (las últimas) |
| `/cesta` (sin sesión) | 10 | paradas 7-10 |
| `/panel` | 13 | paradas 10-13 |
| `/ajustes` | 6 | paradas 3-6 |
| `/favoritos` | 7 | paradas 4-7 |
| `/grupo/:id` (error) | 8 | paradas 5-8 |
| `/escaner` | 4 | **las cuatro** |

**La barra de abajo es siempre lo último.** Está después del `<main>` en el DOM
(`App.tsx:26,56`), y es el destino que se usa cien veces por visita. En la cesta
con líneas, cada línea suma cuatro paradas más —casilla, −, +, Quitar
(`Cesta.tsx:878-891`)—: con nueve líneas son 36 paradas antes de poder cambiar de
pantalla, más las cinco de «Compartir».

El arreglo no cuesta nada visualmente: `NavAbajo` es `fixed inset-x-0 bottom-0`
(`Nav.tsx:81`), así que se puede poner **antes** del `<main>` en `App.tsx` y se
sigue viendo en el mismo sitio. La barra pasa de la parada 12 a la 1.

Y en `/escaner` hay algo peor: el único campo tiene `autoFocus`
(`Escaner.tsx:167`) y su botón está deshabilitado mientras el campo esté vacío
(`Escaner.tsx:173`), así que una pulsación de tabulador desde el campo **sale del
contenido y se va a la barra de abajo**. Quien navegue con el teclado no puede
llegar al botón sin escribir primero; y quien lo lea con un lector de pantalla
tampoco. Es el mismo botón de siempre: el `disabled` se sustituye por una
comprobación al enviar, que ya está (`Escaner.tsx:146-149`).

### 4.5 Qué se lee en un lector de pantalla

Lo que ya está bien y no se toca: los iconos llevan `aria-hidden`
(`iconos.tsx:20`), los botones de solo icono llevan `aria-label`
(`Cesta.tsx:380,389,398`; `VistasGuardadas.tsx:51`), las tablas son `<table>` con
`scope="col"` y `aria-sort` (`ui.tsx:367-368`), los chips llevan `aria-pressed`
(`FiltrosBusqueda.tsx:91,173`; `Ajustes.tsx:92`; `Panel.tsx:511`), el aviso es
`role="status"` y el fallo `role="alert"` (`ui.tsx:152`), y la chispa es
`role="img"` con su etiqueta (`Chispa.tsx:117-118`).

Lo que falta:

    el total de la cesta no se anuncia   Cesta.tsx:893-903. Al tachar algo cambia
                                        el número que se está mirando y no pasa
                                        nada por el lector. Medido: **no hay ni un
                                        solo `aria-live` en toda la aplicación**.
                                        `docs/USABILIDAD.md:117-119` ya lo pedía.
                                        Es un `aria-live="polite"` en el párrafo.
    las pestañas del panel               Panel.tsx:57-74: hay `role="tablist"` y
                                        `role="tab"` con `aria-selected`, pero
                                        ningún `role="tabpanel"`, ningún
                                        `aria-controls`, y las flechas del teclado
                                        no hacen nada. Un `tablist` a medias es
                                        peor que seis botones: promete un
                                        comportamiento que no existe.
    la pantalla no tiene nombre          medido: h1=0 en `/`, `/cesta`,
                                        `/ajustes` y `/favoritos`, y el `<title>`
                                        es «Cesta» en las nueve rutas
                                        (`index.html:8`). Un lector de pantalla
                                        anuncia lo mismo al entrar en cualquier
                                        sitio.
    la foto de un producto es decorativa `alt=""` en TablaResultados.tsx:217,
                                        Grupo.tsx:487, Producto.tsx:159 — es
                                        correcto: el nombre va al lado y repetirlo
                                        solo alarga. No se toca.

### 4.6 Móvil

Lo que ya está y se comprueba: `viewport-fit=cover` y `theme-color` por tema
(`index.html:5-7`); el hueco de la barra con `safe-area-inset-bottom`
(`Nav.tsx:79-81`); 16 px en los campos, con la prueba
`tests/test_ui_movil.py` detrás (`ui.tsx:227-232,259-260`); `loading="lazy"` en
las fotos; `inputMode="numeric"` en el escáner (`Escaner.tsx:165`); el teclado
numérico y `enterKeyHint` en el buscador (`Buscar.tsx:112`).

Medido en la ventana de 390 px: **ninguna pantalla desborda a lo ancho**
(`scrollWidth` = 390 px en las nueve). El `min-w-[16rem]` del campo del buscador
(`Buscar.tsx:113`) cabe; el `min-w-0` del escáner (`Escaner.tsx:155,170`) hace su
trabajo.

Lo que falta de `docs/USABILIDAD.md:121-122` (texto al 200 %): las rejillas de tres
columnas (`Favoritos.tsx:83`, `Cesta.tsx:868`) son `sm:grid-cols-2 lg:grid-cols-3`
y `sm` en Tailwind es 640 px, que es un ancho de ventana y no de letra: con el
texto al 200 % en un móvil de 390 px la rejilla sigue a una columna, así que ahí
no hay problema. Donde sí lo hay es en la **tabla del buscador**: `minAncho="52rem"`
= 832 px, y al 200 % son 1.664 px de arrastre horizontal para llegar a «Ahorro».

---

## 5. Mejoras, por orden

Ordenadas por lo que arreglan al usarla en la tienda. El coste es
`XS` (una tarde de una persona, un fichero), `S` (un día, una pantalla),
`M` (más de un día, o cambia el contrato con la API).

### 5.1 Lo que hay que hacer primero

**1. La letra pequeña del buscador y del grupo no se lee**

    pantalla  buscar, escáner, grupo, ficha, panel
    fichero   Escaner.tsx:189, ui.tsx:173,329, Grupo.tsx:240,255,582,588,596,630,
              Producto.tsx:217, TablaResultados.tsx:110,126, Chispa.tsx:107
    cambio    `text-neutral-500 dark:text-neutral-400` → `text-tinta-suave`
    porque    es el texto que dice de cuándo es un precio y de dónde sale un sello.
              Si no se lee, la regla de no dejar decidir a un precio viejo deja de
              existir en la práctica: nadie va a leer una fecha que no ve.
    coste     XS
    medida    contraste 4,35 → **7,17** en claro (y 7,11 en oscuro, que ya cumplía)

**2. El botón principal, en oscuro, no llega al mínimo de contraste**

    pantalla  escáner, buscar (chips), ajustes (chips), panel (pestañas)
    fichero   ui.tsx:28 (`dark:bg-sky-600`), Escaner.tsx:272,
              FiltrosBusqueda.tsx:96,178, Panel.tsx:68
    cambio    `dark:bg-sky-600` → `dark:bg-sky-700`
    porque    es el botón que se pulsa en el pasillo (buscar el código, marcar una
              cadena) y en oscuro se lee peor que en claro, que es lo contrario de
              lo que uno espera.
    coste     XS
    medida    contraste blanco/sky-600 **4,10 → 5,93** blanco/sky-700.
              Medido en el navegador: 4,10 en `/escaner` y `/panel` en oscuro

**3. El límite de un campo de texto casi no se ve**

    pantalla  buscar, escáner, entrar, cesta, ajustes, compartir
    fichero   ui.tsx:236,264; Buscar.tsx:113; Escaner.tsx:170;
              FiltrosBusqueda.tsx:123; Cesta.tsx:89,99,156,168,180,786
    cambio    el borde pasa al token nuevo `campo-borde` (`#737373` claro,
              `#a3a3a3` oscuro)
    porque    con una mano y el carro en la otra, un campo cuyo borde da 1,48:1 se
              confunde con el fondo y se pulsa donde no está.
    coste     XS
    medida    contraste del borde **1,48 → 4,74** en claro y **1,94 → 6,00** en
              oscuro. El mínimo que pide WCAG 1.4.11 es 3:1

**4. El texto del buscador no se lee, y es su única etiqueta**

    pantalla  buscar, escáner
    fichero   Buscar.tsx:110, Escaner.tsx:169 (el color del placeholder sale del
              preflight de Tailwind; no hay corrección en estilos.css)
    cambio    un color de placeholder propio, con el token `tinta-suave`
    porque    el `<label>` del buscador es `sr-only` (`Buscar.tsx:102-104`): en
              pantalla, lo único que dice para qué es el campo es el ejemplo
              tecleado, y está a 2,54:1.
    coste     XS
    medida    contraste **2,54 → 7,17**. Medido en el navegador

**5. La cesta no separa «lo que queda» de «lo que ya llevo»**

    pantalla  cesta
    fichero   Cesta.tsx:882-903 (un solo `<ul>`, y el recuento al final)
    cambio    dos secciones, «Por coger» y «En el carro», cada una con su cuenta
              en el encabezado, en el orden que ya manda la API
              (`ORDER BY en_carrito, anadido_en`), y el total pegajoso arriba
    porque    es la regla que el proyecto escribió dos veces y la única que no
              está hecha: `docs/PANTALLAS.md:126` («Dos secciones, no una lista
              tachada... si lo tachado sigue en medio, hay que leerlo todo para
              descartarlo») y `docs/UX-MOVIL.md:30-36`, que dice que es lo mejor
              que tenía QueFalta y que se copió tal cual. Hoy el orden pone lo
              cogido al final, pero sin encabezado: hay que leer los nueve nombres
              para saber cuáles quedan.
    coste     S
    medida    con 9 líneas y 4 en el carro: hoy **9 nombres** leídos para
              encontrar los 5 que quedan; con secciones, el encabezado dice
              «Por coger 5» y no hay que leer ninguno. Y el total, que hoy está
              dentro de la tarjeta de arriba (Cesta.tsx:829), deja de necesitar
              un desplazamiento para verse

**6. Ajustes, sin sesión, es un callejón sin salida**

    pantalla  ajustes
    fichero   Ajustes.tsx:42-48
    cambio    el mismo botón que la cesta: la puerta de entrada, o al menos un
              enlace a `/cesta`
    porque    dice «hacen falta tus listas» y no da la forma de entrar. Medido:
              **cero** elementos interactivos en el contenido de esa pantalla.
              Y a la pantalla no se llega por ningún enlace (mejora 7), así que el
              camino es escribir una dirección, leer un aviso y escribir otra.
    coste     XS
    medida    0 → 1 control en el contenido de la pantalla

**7. Favoritos y Ajustes no tienen ni un enlace en toda la aplicación**

    pantalla  buscar, panel
    fichero   FiltrosBusqueda.tsx:104-108 (la frase que habla del ajuste) y
              Panel.tsx:47-55 (la cabecera del panel)
    cambio    un enlace a `/ajustes` en la frase que dice «o tus cadenas de casa
              si las tienes guardadas», y uno a `/favoritos` en el panel
    porque    dos pantallas escritas y probadas solo se abren escribiendo la
              dirección a mano. Y «las cadenas que tengo cerca» es el único ajuste
              que cambia lo que devuelve el buscador.
    coste     XS
    medida    0 → 2 enlaces. Buscado `to="/favoritos"` y `to="/ajustes"` en el
              front: cero coincidencias

**8. Un precio viejo se enseña igual que uno de hoy, en el buscador**

    pantalla  buscar, favoritos
    fichero   TablaResultados.tsx (la fila entera, 211-256); Favoritos.tsx:107-111
    cambio    la etiqueta de meta en la fila cuando el último día de esa cadena no
              es `fecha_datos`: «del <fecha>», como ya hace la tarjeta de una
              cadena en `/grupo` (Grupo.tsx:304-308)
    porque    el buscador es donde se decide qué se compra, y hoy no distingue.
              El dato ya está en `/api/estado` (`cadenas[].ultimo_dia`), que el
              grupo ya usa.
    coste     M
    medida    hoy **0 de 7 columnas** dicen la fecha del precio; pasan a 1

**9. Los objetivos de pulsar por debajo de 44 px**

    pantalla  todas
    fichero   Cabecera.tsx:24 (43×28), Cabecera.tsx:61 (358×24),
              Favoritos.tsx:48 (46×19), Panel.tsx:49-54 (130×20),
              App.tsx:48 (173×39), ui.tsx:380 (32), Grupo.tsx:612,622 (36),
              VistasGuardadas.tsx:53 (≈26 de ancho)
    cambio    `min-h-[44px]` (y `min-w-[44px]` en el `×`), como ya hace
              `Boton` (ui.tsx:52) y `Casilla` (ui.tsx:195)
    porque    la regla del proyecto es de 44 px y estos ocho sitios no la cumplen.
              El `summary` de la cabecera, a 24 px de alto, es el peor: es el
              desplegable que dice qué cadena va con retraso.
    coste     XS
    medida    ocho sitios, medidos en el navegador. Ninguno por encima de 44
              (el peor: 19 px de alto)

**10. El buscador, la cesta y los ajustes no tienen encabezado**

    pantalla  buscar, cesta, ajustes, favoritos
    fichero   Buscar.tsx (no hay h1), Cesta.tsx:781, Ajustes.tsx:62,
              Favoritos.tsx:77; index.html:8
    cambio    un `<h1>` por pantalla —en el buscador, «Buscar»— y el `<title>` del
              documento por ruta
    porque    medido: `h1=0` en las cuatro, y el `<title>` es «Cesta» en las
              nueve. Un lector de pantalla no sabe en qué pantalla está.
    coste     XS
    medida    h1 por pantalla: **0 → 1** en cuatro pantallas; títulos distintos:
              **1 → 9**

### 5.2 Después

**11. El orden de tabulación pone la barra de abajo la última.** `App.tsx:26,56` →
`NavAbajo` antes del `<main>` (ya es `fixed`, no cambia nada visual). Coste XS.
Medida: la barra pasa de la parada 12 a la 1 en `/`, de la 10 a la 1 en `/cesta`.

**12. El total de la cesta no se anuncia.** `Cesta.tsx:893-903` →
`aria-live="polite"`. Coste XS. Medida: `aria-live` en la aplicación: 0 → 1.

**13. Dos pantallas dicen el error y no dejan reintentar.** `Cesta.tsx:759-763` y
`Favoritos.tsx:54-60` → `Fallo` en vez de `Vacio` (ui.tsx:280-293 ya lo hace).
Coste XS. Medida: 2 botones «Volver a intentarlo» que hoy no existen.

**14. **Salir** está dentro de la cesta.** `Cesta.tsx:793-800`: un texto pequeño a
la derecha de la cabecera de la lista, en la pantalla que más se usa, que cierra
la sesión. Se quita de ahí; ya está en `Ajustes.tsx:65-73`. Coste XS. Medida: la
cesta deja de tener un control destructivo a un toque del pulgar en la única
pantalla que se usa de pie.

**15. En el escáner no se puede llegar al botón sin escribir.** `Escaner.tsx:173`:
el `disabled` se cambia por la comprobación que ya hay al enviar
(`Escaner.tsx:146-149`). Coste XS. Medida: paradas de tabulador en el contenido
del escáner: **0 → 1** (hoy el campo tiene el foco y la siguiente pulsación ya
está en la barra de abajo).

**16. Las tablas tienen siete anchos mínimos.** `Panel.tsx:135,198,226,318,392,
432,524`, `TablaResultados.tsx:172`, `Producto.tsx:293`, `Escaner.tsx:293`,
`PanelMatching.tsx:112,195` → tres: `24rem`, `34rem`, `52rem`. Coste XS.

**17. Y en la tabla del buscador, el orden de las columnas.** `TablaResultados.tsx:52-158`:
«Ahorro» y «Por unidad» a la izquierda, «Marca» y «Dónde» al final. Coste S.
Medida: la tabla pide 52rem = **832 px** y la ventana mide 390, así que «Ahorro»
está hoy fuera de la pantalla y hay que deslizar para llegar a la columna que
decide.

**18. El mismo papel, tres radios.** `Buscar.tsx:113` y `Escaner.tsx:170`
(`rounded-xl`), `ui.tsx:236,264` (`rounded-lg`), `Cesta.tsx:89,99,156,168,180,786`
(`rounded-md`) → `rounded-lg` en todos los campos. Coste XS.

**19. La cifra grande, tres formas.** `Cesta.tsx:251,302,829` y `Escaner.tsx:261`
(`text-2xl`), `Grupo.tsx:508` (`text-lg`) → `text-2xl font-semibold`. Coste XS.

**20. Cinco niveles de jerarquía en la ficha del producto.** `Producto.tsx` +
`ui.tsx:173` → la etiqueta de `Dato` pasa a meta (`text-xs text-tinta-suave`, sin
`uppercase` ni `tracking-wide`). Coste S. Medida: escalones visibles **5 → 4**.

**21. Cuatro cajas blancas seguidas antes del primer resultado.** `Buscar.tsx:101-133`:
el campo, los filtros y las vistas guardadas van dentro del mismo bloque; se quita
la tarjeta del medio. Coste S. Medida: bordes de caja antes del primer resultado:
**3 → 1** (calculado: la tarjeta sobre el fondo de página da 1,09:1 de relleno y
1,16:1 de borde).

**22. La acción principal de `/grupo` está arriba a la derecha.** `Grupo.tsx:212-218`
→ barra pegajosa encima de la barra de abajo, con el precio por unidad de la que
gana y el botón de añadir. Coste M. Medida: distancia desde el borde inferior de
la ventana al botón de añadir: de ~640 px (arriba) a ~115 px (encima de la barra),
en una ventana de 844.

**23. El hueco de la barra de abajo sobran 55 px.** `App.tsx:26` (`pb-28` = 112 px)
→ `pb-[64px]`. Coste XS. Medida: la barra mide 57 px (medido: 91×56 por destino más
el borde). Hueco muerto al final de cada pantalla: **55 → 7 px**.

**24. «Sin conexión con casa» no existe como estado de la cesta.**
`Cesta.tsx:815-827` (solo el error de la mutación) y `Cabecera.tsx:30-34` (habla
de las fechas) → un aviso en la cesta que diga la verdad de esta implementación:
no se guarda lo que hagas ahora. Coste S. Medida: medido con `/api/**` cortado:
hoy la cesta no dice nada sobre la lista.

**25. El estado vacío de favoritos dice qué son y no cómo añadir uno.**
`Favoritos.tsx:63-72` + `Favoritos.tsx:10-12` (añadir no está implementado desde
la interfaz nueva) → o se pone el botón en `/grupo` (donde ya está
`BotonFavorito`), o el estado vacío dice la verdad. Coste S. Lo pide
`docs/PANTALLAS.md:198`.

**26. Las pestañas del panel son un `tablist` a medias.** `Panel.tsx:57-74` →
seis botones con `aria-pressed`, o un `tablist` completo con `tabpanel`,
`aria-controls` y flechas. Coste S.

**27. El `×` de una vista guardada se recorta el foco.** `VistasGuardadas.tsx:39`,
`overflow-hidden` → quitar el `overflow-hidden` (el `rounded-lg` se mantiene con
`rounded-lg` en los dos botones de dentro). Coste XS.

**28. El icono de «Cesta» es un gráfico de líneas.** `Nav.tsx:22` usa
`IconoGrafica` (`iconos.tsx:80-86`) para la lista de la compra. Coste XS. Un icono
de línea de tendencia en el destino que se pulsa cien veces por visita dice
«panel», que es justo lo que está al lado.

**29. El total de la cesta no está pegajoso.** `Cesta.tsx:826-847`: está en una
tarjeta normal, al principio. Buscado `sticky` en el front: solo dos sitios, la
cabecera (`Cabecera.tsx:22`) y la cabecera de tabla (`ui.tsx:370`). Y «el total,
pegajoso» está en la lista de `docs/USABILIDAD.md:89-100` de «lo que ya está bien y
conviene no romper», con el motivo escrito («es lo que se mira mientras se anaden
cosas»), y en `docs/UX-MOVIL.md:42-45`. Se queda arriba al desplazar. Coste S.
Medida: con 9 líneas y 4 en el carro, hoy el total está a más de una pantalla del
punto donde se tacha la última línea; pasa a estar siempre visible.

**30. Los textos del escáner hablan del servidor de desarrollo.**
`Escaner.tsx:236-241`: en la pantalla se lee, literalmente, que
`sin_ean_en_esa_cadena` «todavía no se da nunca: necesitaría un parámetro `cadena`
que no está implementado», y que el navegador no tiene `BarcodeDetector` porque no
lo tiene. Lo primero es una nota de programador en una pantalla de producción. Lo
segundo se puede decir («teclea o pega el número»), sin nombrar la clase de
JavaScript. Coste XS.

**31. El peso de la primera carga es 526 kB de JavaScript.** Medido con
`npm run build`: `index-Dk8ySYvX.js` **526,47 kB** (166,36 kB gzip), CSS 24,85 kB
(5,38 kB gzip), y Vite avisa de que el trozo pasa de 500 kB. No se ha hecho nunca
una división por ruta. `/panel` y `/panel/matching` son de David, en casa; uPlot
(51 kB minimizado) solo lo usan `/grupo` y `/producto`. Coste M. Medida: lo que
baje la primera carga, a medir después. En el pasillo, con una barra de cobertura,
esto es lo que decide si la pantalla aparece.

**32. Falta el aviso legal y «Darme de baja».** `Ajustes.tsx` (el aviso de
`docs/PANTALLAS.md:291` y la tarea 7 de `docs/USABILIDAD.md:158-167`). Coste S. No
es una idea nueva: está pedido y sin hacer.

### 5.3 Lo que no se puede hacer todavía

**33. El mosaico de habituales.** `docs/PANTALLAS.md:50-65` y
`docs/USABILIDAD.md:24-36` lo piden, y sería la mejora de más valor del buscador:
añadir algo que compras siempre pasaría de **2 pulsaciones más teclear** (escribir,
abrir el grupo, «Añadir a la cesta») a **1 pulsación**. Está bloqueado: el endpoint
`GET /api/habituales` está escrito en el contrato (`docs/API.md:380-388`) y en el
backlog (`docs/BACKLOG.md:571`) pero **no existe en `plataforma/api`**. Buscado
`habituales` en `plataforma/api`: cero coincidencias. Sin endpoint no hay mosaico, y
el diseño de la cuadrícula de 3 columnas ya está en `docs/PANTALLAS.md:57-62`.

---

## 6. Lo que NO se adopta de los tres recursos, y por qué

### 6.1 `vibeui.online` — 92 plantillas de composición

Es una librería de 92 prompts de maquetación en 15 categorías (auth, precios,
hero, bento, dashboards, onboarding, testimonios, blog, contacto, CTA, barras de
estadísticas, barras de navegación…). Cada prompt acaba siempre con la misma
coletilla, que es la instrucción de fondo de toda la librería:

> «Match the visual style, colors, typography, and overall aesthetic of the UI
> shown in my screenshot.»

**Eso se descarta, y es el motivo del descarte de casi todo lo demás.** Copiar el
aspecto de otra pantalla es exactamente lo contrario de lo que hace este proyecto:
los colores aquí **significan** cosas (`docs/APP.md:345-358`) y hay una prueba
(`test_interfaz.py::test_colores_conocidos`) porque un nombre de color que no está
definido se omite en silencio. Una paleta copiada de una captura rompe las dos
cosas.

Lo demás, por categorías:

    auth (6)            «Split-screen with visual» (auth-1), «Social-first stack»
                        (auth-4), «Magic link only» (auth-5), «Multi-step wizard»
                        (auth-6). Hay UNA pantalla de entrar, con usuario y clave, y
                        no hay registro abierto ni contraseñas olvidadas
                        (docs/PANTALLAS.md:33-40). «Minimal single-column» (auth-3)
                        es lo que ya está hecho (Cesta.tsx:206-230): una línea.
    pricing (8)         «Classic 3-tier cards», «Monthly/annual toggle», «Usage
                        slider», «Credit pack grid», «Free vs Pro split». No hay
                        precio, ni plan, ni pago, ni suscripción. Nada que adoptar.
    hero (8)            «Video background», «Animated gradient mesh», «Terminal/code
                        hero», «Floating UI elements», «Big bold typography». Son
                        recursos de página de aterrizaje y aquí no hay página de
                        aterrizaje: la app **es** la herramienta y una pantalla de
                        bienvenida está prohibida (docs/PANTALLAS.md:316). Además un
                        fondo animado son bytes y batería en el pasillo, con una
                        barra de cobertura.
    bento (8)           «Bento grid» (ft-2) y «Icon wall» (ft-7): mosaicos de
                        tamaños distintos para enseñar características de un
                        producto. Aquí un mosaico sí tiene sentido, pero solo para
                        una cosa —lo que compras siempre, y con foto— y no hay
                        endpoint (mejora 33). «Accordion list» (ft-5) y «Tabbed
                        features» (ft-3): ya se usan donde hacen falta
                        (`<details>` en FiltrosBusqueda.tsx:64, Panel.tsx:57). Una
                        línea.
    testimonios (8), blog (4), contacto (3), CTA (7), estadísticas (7)
                        Muebles de marketing. «3-column quote cards», «Tweet wall»,
                        «Logo cloud», «Full-bleed gradient banner», «Horizontal
                        4-column numbers». Cesta la usan dos personas que se
                        conocen; no hay nada que probar a nadie.
    dashboards (6)      «Sidebar + main content» (ds-1), «Three-pane layout»
                        (ds-3), «Kanban board» (ds-4). Medido: la ventana del móvil
                        mide 390 px y una barra lateral se come un tercio. El kanban
                        es para cosas con estados de un proceso; aquí no hay ninguna.
                        «Metric cards + chart» (ds-5) ya es lo que hace el panel
                        (Panel.tsx:252-265). «Top nav + content» (ds-2) ya es el
                        armazón (App.tsx:22-57). Una línea.
    nav (8)             «Bottom mobile nav» (nv-8): ya está (Nav.tsx:75-90), con
                        cuatro destinos y `safe-area`; no se toca
                        (docs/USABILIDAD.md:89-107). «Command-palette nav» (nv-7,
                        ⌘K): el buscador ya está siempre visible y no hay teclado
                        físico. «Mega menu» (nv-3), «Floating pill nav» (nv-5),
                        «Transparent over hero» (nv-6): no hay hero ni submenús.
    onboarding (4)      «Checklist onboarding», «Tour tooltips», «Video walkthrough
                        modal», «Illustrated empty state». Lo primero que un
                        onboarding supone es que hay algo que explicar:
                        docs/PANTALLAS.md:316 («Pantalla de bienvenida o tutorial. Si
                        hace falta explicarla, esta mal hecha») y
                        docs/USABILIDAD.md:11-18. Lo que sí se adopta de aquí es
                        «un CTA claro para empezar», y ya está hecho con los tres
                        ejemplos pulsables (Buscar.tsx:145-152).

**Lo único que sí se adopta de `vibeui.online`** es la colocación de «Sticky bottom
bar» (cta-3) para la acción principal de `/grupo` (mejora 22), y se adopta a
medias a propósito: sin mensaje de venta, sin «descartar» y sin poder cerrarla.

### 6.2 `styles.refero.design` — DESIGN.md de sitios reales

Es un directorio de 24 DESIGN.md extraídos de webs reales (Mercury, Linear, Stripe,
ElevenLabs, Apple, Notion, Duolingo…), con su paleta, su escala de tipo, su
espaciado, sus componentes y su lista de «Do's and Don'ts». El propio recurso dice
cómo usarlo:

> «Use these examples as references, not templates to copy.»
> «Copy the system, not the website.»

**Se adopta la forma**: un documento con tokens, reglas y una lista de lo que no se
hace, con el valor al lado del papel. Que es este documento. **Se descartan las
fuentes**, y aquí está el detalle, porque es donde se ve por qué no valen.

Leído entero el de **Mercury** (uno de los 24; `styles.refero.design/style/3172cd4d-118a-4a16-a259-6b634d32322e`),
que propone: tipo de display a **65 px**, hero a pantalla completa con fotografía a
sangre, «density: spacious», **72 px** entre secciones, **32 px** de relleno de
tarjeta, un solo acento cobalto reservado a la acción principal, radios de píldora
de **32-40 px**, cero sombras, y `#ededf3` en vez de blanco para el texto.

    el display de 65 px        el texto más grande que necesita esta app es un
                               precio a 24 px (`text-2xl`). En una ventana de
                               390 px, 65 px son unos cinco caracteres por línea.
                               No hay titular, y no debe haberlo.
    72 px entre secciones      medido: hoy el hueco entre tarjetas es `gap-4`, 16 px
    32 px de relleno de tarjeta  medido: hoy `p-4`, 16 px. Duplicarlos es una
                               tarjeta por pantalla en el pasillo. La medida que
                               importa aquí no es «la sensación premium», es
                               cuántas cosas se ven sin desplazar.
    radios de píldora 32-40 px el botón mide 44 px de alto (`ui.tsx:52`): con 32 px
                               de radio es una pastilla, y en una línea de la cesta
                               hay cuatro controles (−, cantidad, +, Quitar,
                               Cesta.tsx:378-403) que ya van justos de ancho. Se
                               queda a 8 px.
    fotografía a sangre        hay fotos de producto, del CDN de cada cadena y
                               `loading="lazy"`. Ninguna es decorativa.
    cero sombras               **esto sí**, y por un motivo medido y no de gusto:
                               en oscuro la sombra de una tarjeta `#262626` sobre
                               una página `#171717` no existe. Se quita
                               `shadow-sm` (ui.tsx:116). Ver 1.5.
    no usar varios acentos     ya se cumple: seis colores con significado y ninguno
                               decorativo (`tailwind.config.js:6-8`)
    `#ededf3` en vez de blanco para el texto en oscuro
                               se descarta: aquí el texto del cuerpo en oscuro es
                               `#f5f5f5` sobre `#171717`, **16,44:1**. Bajar el
                               valor del texto empeora la lectura para arreglar un
                               problema de dureza que no está medido en este
                               proyecto y que, de existir, se arreglaría por otra
                               vía.

Y un descarte de fondo, que vale para los 24: **ninguna de esas webs es una lista de
la compra que se usa de pie, con una mano y el carro en la otra.** Los DESIGN.md
extraídos describen cómo se ve una marca, que es un problema que aquí no existe: la
marca son dos personas y un PC de casa. Lo que sí traen y se queda es la
**estructura** del documento, que es la de este.

### 6.3 `github.com/context-dot-dev/designmd-supply` — el generador

Es una aplicación de Next.js que convierte cualquier URL en un DESIGN.md. Pide
cuatro endpoints de la API de **Context.dev** (styleguide, brand, screenshot y
markdown de la web), monta un prompt y lo manda a un modelo por el **Vercel AI
Gateway**, y lo cachea en **Turso**. El repositorio lo dice en su README:

> «It pulls brand identity, design tokens, a hero screenshot, and the live page
> Markdown, then composes them into a DESIGN.md file with YAML frontmatter and the
> canonical sections (Overview, Colors, Typography, Layout, Elevation, Shapes,
> Components, Do's and Don'ts).»

**Se descarta entero el mecanismo, y por las leyes del proyecto:**

    servicios externos   hacen falta una clave de Context.dev, otra del AI Gateway y
                         una base de datos Turso. No entra ningún servicio externo y
                         no se llama a ningún modelo desde el front
                         (docs/APP.md:56-105). Los datos se quedan en casa.
    genera los tokens    los saca de una captura y del styleguide de OTRA web. Los
    de una captura      tokens de aquí viven en `tailwind.config.js` y `estilos.css`,
                         y hay una prueba que compara los dos por un fallo real
                         (docs/APP.md:352-358). Un generador que reescriba la paleta
                         rompe esa prueba y vuelve a abrir el agujero.
    su catálogo          `lib/domains.ts` son 43 dominios del Fortune 500: Apple,
                         Microsoft, TSMC, ExxonMobil, Walmart, McDonald's. Ninguno es
                         una lista de la compra que se usa de pie en un pasillo. La
                         referencia que le falta a esta app no está en esa lista, y
                         ninguna extracción de styleguide la va a encontrar: la
                         pregunta aquí no es «qué fuentes usa esa web», es «4,35:1
                         basta para leer la fecha de un precio bajo la luz de un
                         supermercado». Eso no lo contesta ningún extractor.
    el frontmatter YAML  se descarta también, y este es el descarte fino: el
    y `version: alpha`   frontmatter solo lo lee una máquina, y en este repositorio la
                         única máquina que lee algo es `pytest`. Un segundo sitio con
                         los valores de los colores es exactamente el fallo que
                         `test_colores_conocidos` existe para cerrar. Los valores se
                         citan con su fichero y su línea, no se copian.
    la convención de nombres (`primary`, `secondary`, `neutral`, `surface`,
    `on-surface`, `error`; `headline-display`… `label-sm`)
                         se descarta: los nombres de aquí **dicen lo que
                         significan** (`tinta-suave`, `aviso`, `bien`,
                         `bien-suave`) y llamarlos `surface` o `error` saca el
                         significado del nombre. Sería renombrar 27 usos y tocar la
                         prueba.
    el modo de trabajo    el recurso está pensado para pegar un DESIGN.md en el
                         contexto de Cursor, Codex, v0 o Lovable. Aquí el front se
                         escribe a mano en `plataforma/web/app/src` y las decisiones
                         se apuntan en `docs/`. Lo que se queda de este recurso es
                         **el documento**, no el flujo.

**Lo que sí se adopta** de `designmd-supply`: el orden de secciones que codifica en
`lib/design-md.ts` (Overview, Colors, Typography, Layout, Elevation & Depth, Shapes,
Components, Do's and Don'ts) —que es el orden de este documento, con la sección de
estados añadida porque aquí los estados son la mitad del trabajo y en su lista no
están—, la tabla de tokens con valor y papel, y esta instrucción suya, que es la
misma regla que el proyecto ya tenía escrita en `docs/APP.md:147-166`:

> «If data is missing, infer conservatively and state uncertainty in prose, not in
> token values.»

Un dato que no tenemos es «no lo sé», y un token que no tenemos no se inventa: se
dice que falta.

---

## 7. Lo que no he podido comprobar

**Medido de verdad:** los contrastes de las tres tablas del punto 4.1 (los 41 que
cumplen y los 10 que no), las zonas de pulsar de las nueve rutas, el orden de
tabulación de las nueve rutas, el peso del build, el desbordamiento horizontal, y
que el estado «sin conexión» sale bien.

**Calculado y no observado en un navegador:**

    los fallos 3 al 5 y 8 al 10 de 4.1    colores que solo se pintan con datos
                                          reales o en una tarjeta concreta
    la cabecera en oscuro (#3)            `Cabecera.tsx:38` solo se pinta cuando
                                          `/api/estado` contesta, y en la medida la
                                          API estaba cortada
    los 13 sitios del fallo 1             solo uno (Escaner.tsx:189) se ve sin
                                          datos; los otros doce viven en tablas y
                                          tarjetas que necesitan la API
    las mejoras 22 y 17                   la distancia al botón de añadir de
                                          `/grupo` y el ancho de la tabla del
                                          buscador están calculados sobre el código
                                          y el `minAncho`, no medidos con
                                          resultados dentro

**Sin comprobar, y conviene saberlo:**

    la cesta con líneas dentro       no hay sesión ni API, así que las pantallas que
                                     más importan —la cesta con 9 líneas, el grupo
                                     con cinco cadenas, la ficha con histórico— se
                                     han medido solo en su estado de error. El
                                     recuento de paradas de tabulador de la cesta
                                     con líneas está **derivado**: 4 por línea
                                     (Cesta.tsx:878-891) más las 5 de Compartir.
    el modo oscuro con datos         los fallos de contraste en oscuro están
                                     medidos, pero la foto del oscuro es de
                                     pantallas vacías.
    un lector de pantalla de verdad  nada de 4.5 está probado con NVDA, VoiceOver ni
                                     TalkBack. Está deducido del HTML.
    la calle                         390 px de ventana es un móvil, pero no es la luz
                                     de un supermercado ni el pulgar de nadie. Lo
                                     único que se puede afirmar con números es el
                                     contraste, el tamaño y el orden de tabulación.
    `/api/habituales`                sigue sin existir: la mejora 33 está bloqueada
                                     por la API, no por el diseño.
