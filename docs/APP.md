# Cesta — especificacion de la plataforma

Escrita el 14 de septiembre de 2026 y **rehecha entera el 15**, cuando se
decidio que los datos se quedan en el PC y que hay dos personas usando la app.
Lo que sigue esta **sobre los datos que existen**, no sobre los que nos gustaria
tener: cada decision de pantalla lleva al lado el numero que la sostiene.

Este documento describe **la app**. Sus companeros:

    docs/CADENAS.md      que publica de verdad cada supermercado
    docs/MODELO.md       los campos y las consultas
    docs/DESPLIEGUE.md   donde vive cada cosa y como se entra desde fuera
    docs/DASHBOARD.md    el cuadro de mando analitico

---

## 1. Para que es esto

Tres situaciones reales, en orden de importancia:

1. **Estas en el pasillo del supermercado** con el movil y quieres saber si eso
   que tienes en la mano esta mas barato en la tienda de al lado. Mala cobertura,
   prisa, una mano ocupada.
2. **Estas en casa preparando la compra** y quieres saber donde te sale mejor la
   lista entera, o si merece la pena partirla en dos tiendas.
3. **Quieres vigilar** unos pocos productos que compras siempre y enterarte
   cuando bajan de verdad, no cuando la cadena dice que bajan.

Todo lo demas es secundario. Si una pantalla no sirve a una de las tres, sobra.

---

## 2. Lo que hay (15 sep 2026)

    catalogo              51.781 productos de 5 cadenas
    grupos comparables     6.448  (19.235 productos dentro)
      con 2 cadenas        4.209
      con 3 cadenas        1.390
      con 4 cadenas          607
      con las 5              270
    historico            560.640 filas, 9 dias
    calidad A/B/C         11.754 productos (2.688 leyendo ingredientes)
    nota de composicion   11.559
    Nutri-Score            8.359
    NOVA                   7.728

**El numero que manda todo el diseno: solo 6.448 grupos son comparables.** De los
51.781 productos, 19.235 tienen con quien compararse y 31.853 no. La app tiene que
servir bien a los dos casos y no fingir que el segundo es el primero.

Por eso la interfaz no puede ser "un comparador": tiene que ser **un buscador que
compara cuando puede**.

---

## 3. Decision central: los datos se quedan en casa

La version anterior de este documento metia el catalogo entero en el telefono: un
paquete diario de unos 7 MB que se descargaba y vivia en IndexedDB. Funcionaba
sin cobertura, que era el problema que queria resolver.

**Se descarta.** Por tres razones, en orden:

1. Son 7 MB al dia por telefono, cada dia, para siempre. Dijiste que no.
2. Con dos personas, cada movil tendria su propia copia de las listas y los
   favoritos, sin forma de compartirlos. Una lista de la compra que no se
   comparte no sirve para hacer la compra entre dos.
3. El cuadro de mando no cabe en un movil: son 560.640 filas hoy, creciendo a
   52.575 al dia.

Lo que se hace en su lugar:

    los datos          en tu PC, en un contenedor Docker, siempre
    el movil           una web. Pide lo que esta mirando y nada mas.
    lo que se comparte listas de la compra, entre tu y tu madre
    lo que es de cada uno  favoritos, alertas, busquedas

`docs/DESPLIEGUE.md` cuenta el montaje completo. Aqui solo lo que se nota desde
la pantalla.

### Lo que se pierde y lo que se hace con ello

Lo que se pierde es funcionar sin cobertura, y el caso de uso numero uno ocurre
**dentro de un supermercado**, que es donde peor va. No se puede fingir que no
importa. Tres cosas lo amortiguan:

- **La lista de la compra se lleva entera.** Cuando abres la lista, el movil se
  guarda esa lista completa: los productos, los precios, la tienda elegida. Es lo
  unico que se guarda, son unos pocos KB, y es exactamente lo que necesitas
  mientras andas por los pasillos.
- **Lo que tachas sin conexion se sube luego.** Tachar un producto se apunta en
  el movil y se sincroniza cuando vuelve la red. Si tu madre tacha la leche en el
  Alcampo sin cobertura, cuando salga se te tacha a ti.
- **Lo demas dice la verdad.** Si no hay conexion con casa, la pantalla lo dice:
  "sin conexion con casa, esto es de hace 2 h". No una rueda girando para siempre.

### Y si el PC esta apagado

La app no funciona, salvo la lista que te llevaste. Es la consecuencia directa de
no querer un servidor de pago, y es una decision coherente: lo importante es
saber que se ha tomado. Esta en `DESPLIEGUE.md` punto 6.

---

## 4. El modelo, visto desde la app

Ver `docs/MODELO.md` para los campos exactos y las consultas, y `docs/CADENAS.md`
para lo que publica cada cadena. En resumen:

**Producto** es lo que vende una cadena. Tiene precio, formato, y a veces EAN,
calidad, Nutri-Score y origen.

**Grupo** es "la misma cosa" vista en varias cadenas, con dos niveles:
- *identico*: mismo EAN, o misma marca y mismo formato.
- *equivalente*: mismo producto de distinta marca. **Aqui esta el ahorro.**

**La unidad de la interfaz es el grupo**, no el producto. Cuando buscas "leche
entera" no quieres 40 filas: quieres una fila que diga "leche entera, 1 L, desde
0,83 EUR en Aldi" y que se abra.

Pero **32.486 productos estan solos en su grupo**, es decir, no tienen con quien
compararse. Para esos, la fila
es el producto y no hay comparacion que ensenar. La app no debe inventarse una.

---

## 5. Dos personas

Tu y tu madre. No es "multiusuario" en el sentido de un producto: son dos
cuentas que tu creas, sin registro abierto, porque no hay nadie mas.

Lo que cambia en la pantalla:

- **Las listas tienen dueno y pueden compartirse.** Una lista compartida se edita
  desde los dos moviles a la vez. Cuando uno tacha, al otro se le tacha.
- **Los favoritos no se comparten.** Tus productos vigilados son tuyos.
- **Las cadenas cercanas son de cada uno.** Si tu madre no tiene Aldi cerca, sus
  comparaciones no deberian ensenarselo como la opcion mas barata.
- **Nadie ve lo del otro salvo las listas compartidas.** No hay pantalla de
  administracion ni de "actividad": son dos personas, no una organizacion.

Lo que **no** cambia: el catalogo, los grupos y los precios son los mismos para
los dos y no se copian por usuario.

---

## 6. La regla que atraviesa toda la interfaz: de cuando es este precio

Las cadenas no siempre refrescan el mismo dia. El 11 y el 12 de sep Carrefour dio
403 y sus precios eran de dos dias antes. El 12, Alcampo se quedo sin capturar.

**Cada precio de la interfaz lleva su fecha cuando no es de hoy.** No en una nota
al pie, no en un ajuste: pegado al numero.

    Aldi        0,83 EUR/L
    Alcampo     0,85 EUR/L
    Carrefour   0,89 EUR/L   (del 12 sep)

Y un producto cuyo precio tenga mas de tres dias no entra en el calculo de "donde
sale mas barata la lista": se muestra, pero marcado, y no decide nada.

Esto no es escrupulosidad: es que una app de precios que muestra precios viejos
sin decirlo es peor que no tener app.

---

## 7. Las pantallas

Cinco. Ni una mas hasta que las cinco esten bien.

### 7.1 Buscar (inicio)

Lo primero al abrir. Un campo, un boton de microfono, y debajo lo ultimo que
buscaste.

- **Texto**: busca en nombre y marca de los 51.781 productos, agrupando por grupo
  cuando lo hay. Tolerante a plurales y acentos (ya resuelto en `core.matching`).
- **Voz**: la API del navegador (`SpeechRecognition`), gratis y sin servidor. No es
  un asistente: es un atajo para no escribir. "dos litros de leche entera" rellena
  el campo y, si detecta cantidad, la propone para la lista.
- **Resultado**: filas de grupo. Cada una con el nombre, el formato, el precio por
  unidad mas bajo y en que cadena, y cuantas cadenas lo tienen.

Filtros, siempre a la vista pero plegados:

    calidad      A / B / C / con nota
    nutricion    Nutri-Score A-B / sin D ni E / NOVA 1-2
    origen       ver el punto 8 -- tiene trampa
    cadena       solo las que tengo cerca
    formato      el tamano que compro

### 7.2 Ficha de grupo (el comparador)

La pantalla que justifica el proyecto. Al abrir un resultado:

**Arriba, la comparacion.** Una fila por cadena, ordenada por precio por unidad:
el nombre que le da cada una, la marca, el precio total, el precio por kilo o
litro, y la diferencia con el mas barato. Con su fecha si no es de hoy.

**Debajo, los equivalentes de otra marca.** Separados a proposito de los
identicos, porque no son lo mismo y mezclarlos es mentir. Cada uno con su letra de
calidad y su Nutri-Score, para que "mas barato" no sea el unico criterio.

**Despues, la composicion.** Nutri-Score, NOVA, la nota de composicion con las
senales que la formaron (cuantos aditivos, si lleva aceite de palma, el porcentaje
del ingrediente principal) y la lista de ingredientes. Con el origen del dato: de
la etiqueta de la cadena o de Open Food Facts.

**Al final, la curva.** El precio por unidad de cada cadena en el tiempo. Con 9
dias es corta; en tres meses sera la pantalla mas util de la app. Marca las
subidas previas a una "oferta", que es lo que detecta `oferta_sospechosa`.

Dos botones: **anadir a la lista** y **seguir**.

### 7.3 Lista de la compra

Se anaden grupos, no productos: "leche entera 1 L x6", no "leche entera Hacendado".
La cadena la decide la app, que para eso esta.

Y entonces la pregunta: **donde la compro**. La respuesta tiene dos partes y hay
que dar las dos, porque la buena depende del dia:

    TODO EN UNA TIENDA
      Mercadona    47,30 EUR     le faltan 2 de 14 productos
      Alcampo      48,10 EUR     los 14
      Carrefour    51,05 EUR     los 14

    REPARTIDO
      Alcampo + Mercadona    41,80 EUR    ahorras 6,30 EUR
      (9 productos en Alcampo, 5 en Mercadona)

El reparto se limita a **dos tiendas por defecto**, configurable. Un reparto entre
cinco tiendas que ahorra ocho euros no lo hace nadie, y ofrecerlo es ruido con
aspecto de recomendacion.

Los productos que a una cadena le faltan se dicen por su nombre, no como un
numero: "en Mercadona no encuentro: cafe en grano 1 kg, atun en aceite pack 6".

### 7.4 Favoritos

Los pocos productos que compras siempre. No es una lista larga: es una pantalla de
vigilancia.

Cada uno con su precio de hoy, su posicion en los ultimos 90 dias (que ya calcula
`gold/resumen.parquet`) y hacia donde va. Ordenados por lo que ha cambiado, no
alfabeticamente: lo que ha bajado arriba, lo que ha subido justo debajo, lo quieto
al final.

Y las alertas son pasivas: la app te lo ensena cuando la abres, no te manda
nada. Las notificaciones piden un servidor siempre accesible y permisos del
navegador, y no son para la primera version.

### 7.5 Explorar

La que menos importa y la ultima que se hace. Navegar por categoria para descubrir,
no para buscar. Requiere una categoria canonica que hoy no existe (punto 9).

---

## 8. El origen: lo que se puede prometer y lo que no

Pediste poder filtrar por producto nacional. Aqui el dato es flojo y conviene
decirlo antes de dibujar ningun filtro.

    origen declarado por la cadena    Mercadona 30 %, las otras cuatro 0 %
    y ademas viene sucio              "Espana", "ESPANA", "Producto de Espana",
                                      "Valencia, Espana.", "Cordoba"
    proveedor (domicilio social)      73-76 % en Mercadona y DIA
    prefijo del codigo de barras      81 % de los EAN empiezan por 84x

**El prefijo 84x NO significa que el producto sea espanol.** Significa que la
empresa que registro el codigo se dio de alta en GS1 Espana. Una marca espanola
puede envasar tomate chino y su codigo seguira empezando por 84.

Asi que el diseno es este, y es deliberadamente conservador:

- El campo se llama `origen_espana` y tiene tres estados: **si**, **no**, **no
  consta**. Nunca se rellena "no consta" con una suposicion.
- Cada valor viaja con **como se sabe**: `etiqueta` (lo declara la cadena),
  `externo` (Open Food Facts), `marca` (prefijo del codigo).
- En la interfaz, el filtro NO se llama "producto nacional". Se llama **"origen
  declarado en Espana"** y solo usa `etiqueta` y `externo`. El prefijo del codigo
  aparece como un dato mas en la ficha, con su nombre: "marca registrada en
  Espana".

Medido el 15 de septiembre: **1.444 productos de 51.781 tienen origen
declarado, el 2,5 %**, y todos son de Mercadona. Con eso, el filtro no se dibuja.

**Tarea pendiente que sube mucho la cobertura**: Open Food Facts publica
`origins_tags` y no lo estamos trayendo. Anadirlo a `CAMPOS` en `core/off.py` es
una linea, y cruza con los 12.835 productos nuestros que ya casan con OFF. Hasta
hacerlo y medirlo, el filtro de origen queda escondido, no a medias.

---

## 9. Lo que falta en el dato antes de que estas pantallas funcionen

Por orden de lo que mas bloquea:

1. **Categoria canonica.** Cada cadena tiene su arbol y no hay uno comun, asi que
   "Explorar" no se puede hacer y los filtros por seccion tampoco. OFF trae
   `categories_tags` en 133.644 productos espanoles: el grupo puede heredar la
   categoria del miembro que la tenga. Para los que no cruzan con OFF, un mapa a
   mano de unas 25 secciones.
2. **`origins_tags` de Open Food Facts** (punto 8).
3. **Imagenes.** Las cinco cadenas la publican y desde el 15 de septiembre las
   cinco la guardan (Alcampo no la copiaba, ver `CADENAS.md` punto 4). Falta que
   `imagen` llegue de bronze a gold. Una lista de la compra sin fotos se usa
   peor, sobre todo con una mano ocupada.
4. **Historico.** Nueve dias. La curva y la posicion de 90 dias no significan nada
   todavia. Esto no se arregla programando: se arregla esperando.
5. **Los 405 grupos con diferencias imposibles** (>200 %) son formatos mal leidos.
   Antes de ensenar comparaciones a nadie hay que revisarlos, porque son
   exactamente los que mas llaman la atencion en una pantalla.

---

## 10. Como se construye

**La interfaz se rehace con un stack especializado** (decision del dueno, 22 de
septiembre de 2026, en `docs/PLAN-UI-MATCHING.md`). Esto **sustituye** a lo que
decia antes esta seccion ("nada de framework pesado", "sin framework", "grafica
SVG a mano"), y se cambia aqui a la vez que en el codigo para que los documentos
no cuenten dos historias distintas.

Por que cambio: la interfaz actual **no son 6 KB de HTML**. Son `index.html`
6.663 B + **`app.js` 79.656 B** escritos a mano + `estilo.css` 29.063 B. Lo que
viene pide tablas con filtros combinables, columnas virtualizadas, un producto
comparado entre cinco cadenas y series de precio por fila; a mano eso son miles
de lineas mas y sin pruebas.

    api         FastAPI en Docker. Autentica y responde JSON. No sirve HTML.
    consultas   DuckDB sobre los parquet de gold, sin copiarlos.
    usuarios    PostgreSQL. Cuentas, listas, favoritos, alertas.
    cliente     Vite + React + TypeScript + Tailwind, servido por Caddy.
                Sin servidor nuevo: el build sale a plataforma/web/dist y Caddy
                lo sirve igual que servia la carpeta entera.
    tablas      TanStack Table: filtros, orden, agrupacion, virtualizacion.
    datos       TanStack Query: cache y estados de carga sin inventarlos.
    grafica     uPlot para las series de precio. SVG a mano solo donde no haya
                libreria que aporte nada.
    voz         SpeechRecognition del navegador. Cero dependencias.
    entrada     Tailscale. Ver DESPLIEGUE.md punto 4.

**Los colores con significado viven en dos ficheros que tienen que decir lo
mismo.** `tailwind.config.js` define los nombres (`text-tinta-suave`, `bg-fondo`,
`border-borde`, `text-aviso`, `border-bien`, `bg-bien-suave`) y
`src/estilos.css` les da valor, uno para el tema claro y otro para el oscuro. Son
variables de CSS y no hexadecimales porque estas clases se escriben sin el prefijo
`dark:`, y con un valor fijo el gris del texto secundario desaparece de noche.

Eso tiene prueba propia (`tests/test_interfaz.py::test_colores_conocidos`) por un
fallo real, no por gusto: los seis nombres se usaban **27 veces** y **no estaban
definidos en ninguna parte**. Tailwind, cuando no reconoce una clase, la omite en
silencio: ni error de compilacion, ni aviso en el navegador. `tsc` y `vite build`
tampoco podian verlo, porque una clase desconocida es una cadena de texto
perfectamente valida. La prueba compara lo que se escribe con lo que el tema
define, que es lo unico que cierra ese agujero.

Se mantiene lo que ya estaba decidido y no cambia:

- **Caddy sigue sirviendo la interfaz** y la API sigue sin servir HTML
  (`docs/API.md:336`). El `Caddyfile` ya hace `try_files {path} /index.html`, que
  es exactamente lo que necesita una aplicacion de una sola pagina.
- **Un solo origen** en `:8080`: sin CORS y sin cookies que se pierden.
- Lo que **no** debe haber sigue igual: ni tutorial, ni pantalla de actividad, ni
  valoraciones, ni publicidad (`docs/PANTALLAS.md:314-324`).
- **Calidad no es gama**: se devuelve `calidad` si sale de ingredientes y `gama`
  si sale del precio, **nunca las dos** (`docs/BACKLOG.md:46-49`).
- Movil desde el principio (`docs/UX-MOVIL.md`), y la barra de abajo no se toca
  (`docs/USABILIDAD.md:89-107`).

Cambio pendiente, para el dia que se toque el front y no antes: en
`plataforma/docker-compose.yml:61`, `- ./web:/srv:ro` pasa a
`- ./web/dist:/srv:ro`.

El orden de construccion, y cada paso sirve para algo por si solo:

1. **La API con dos consultas**: buscar y ficha de grupo, leyendo gold. Sin
   usuarios. Se prueba desde el propio PC con `curl`.
2. **Tailscale**, y comprobar que se abre desde tu movil.
3. **Las cuentas** y la base de usuarios. Tu primero, tu madre despues.
4. **Buscar y ficha de grupo** en pantalla. Con esto ya se puede usar en el
   supermercado, que es el caso numero uno.
5. **Lista de la compra**, el reparto entre tiendas, y compartirla.
6. **Favoritos** y la curva.
7. **Escritura sin conexion** en el movil.
8. **Categoria canonica** y Explorar.
9. **El cuadro de mando** (`DASHBOARD.md`).

Los pasos 1 a 3 son lo que hay que tener antes de ensenarselo a nadie.

---

## 11. Lo que este documento NO propone, y por que

- **Registro abierto.** Son dos cuentas que creas tu. El dia que haya una
  tercera persona se anade a mano, y eso es todo.
- **Notificaciones push.** Necesitan servidor accesible y permisos, y con nueve
  dias de historico no hay nada que notificar todavia. Las alertas de la fase 1
  son pasivas: la app te las ensena cuando la abres.
- **Recomendaciones automaticas.** "Te puede interesar" con este volumen de datos
  es adivinar.
- **Comparar la cesta con el IPC o con precios historicos oficiales.**
  Interesante, pero es otro proyecto.
- **Publicarlo para otra gente.** Cambia todo: licencia de Open Food Facts (ODbL,
  hay que citarla), condiciones de uso de las cadenas, proteccion de datos. Se
  decide cuando funcione para vosotros dos.
- **Un servidor de pago.** Se descarto a proposito, y el precio es que la app no
  funciona con el PC apagado. `DESPLIEGUE.md` punto 6.
