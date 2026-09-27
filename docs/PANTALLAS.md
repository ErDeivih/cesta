# Cesta — las pantallas, una por una

Especificacion funcional de la interfaz. Que se ve, que pasa al tocar, y **que se
ve cuando algo falla**, que es la mitad que se olvida siempre.

Complementa `docs/UX-MOVIL.md` (las reglas generales) y `docs/API.md` (los
contratos). Lo que ya esta hecho se marca **[hecho]**; lo que falta, **[falta]**
con la tarea de `BACKLOG.md` que lo cubre.

---

## Las reglas que valen para todas

**Se usa con una mano y el carro en la otra.** Navegacion abajo. Areas de pulsar
de 44 px para arriba. Nada importante en la esquina superior.

**Nada espera al servidor para pintarse.** Anadir, tachar y cambiar cantidad se
ven al instante y se mandan despues. En el pasillo, un boton que tarda dos
segundos se pulsa tres veces.

**Cada pantalla tiene cuatro estados, y los cuatro se disenan**: cargando,
con contenido, vacia, y rota. La vacia dice **que hacer**, no "no hay datos". La
rota dice **que ha pasado**, no una rueda girando.

**Un numero nunca sin contexto.** El total dice que es aproximado. Lo que no
tiene precio se cuenta aparte, no como cero. Un precio de otro dia lleva su
fecha.

**Ninguna tabla se desliza de lado: se apila.** Por debajo de 640 px, cada fila es una linea y
las celdas van debajo; el nombre de la columna va **en la celda** (`Td etiqueta="…"`) cuando el
valor no se explica solo. Antes se deslizaba dentro de su caja con el aviso «Desliza la tabla
para ver todas las columnas →», y lo que quedaba fuera era el precio (medido el 27 de
septiembre de 2026, en el buscador y en el panel). Lo hace `.tabla-scroll` en un solo sitio.
Ver `docs/UX-MOVIL.md` §4.

---

## Inicio — la primera pantalla

**[hecho] el 27 de septiembre de 2026.** Es lo primero que se ve al abrir, y existe por una
razon que esta escrita en `docs/PRUEBA-15-SEGUNDOS.md`: **las cuatro preguntas con las que se
abre la aplicacion no se contestaban desde la primera pantalla**. Habia que entrar en otra.

    1. «¿Que me falta comprar y donde lo compro?»   antes 1 toque    ahora 0
    2. «Esto que tengo en la mano, ¿esta caro?»     antes 1 toque    ahora 1 (escribir aqui)
    3. «¿Voy tachando bien?»                        antes 0 toques   ahora 0 (y en la barra)
    4. «¿Ha bajado algo de lo mio?»                 antes 1, o 3     ahora 0

No se ha quitado ninguna pantalla: se contesta **antes** de tener que ir. `/cesta`, `/buscar`,
`/avisos` y `/panel` siguen donde estaban, y la barra sigue llevando a las mismas seis. El
titulo de la pestaña sigue poniendose por ruta (`App.tituloDe`), con `/` = «Inicio».

    [ buscar…                            ] [ Buscar ]   <- la pregunta 2, sin salir de aqui

    Lo que te falta                                   <- preguntas 1 y 3
    7 cosas
    4 en Mercadona · 2 en Aldi · 1 en DIA
    Total estimado 43,18 € · con las ofertas te ahorras 2,40 €
    Ver la lista entera y tachar            -> /cesta

    Pendientes de coger                               <- las cuatro primeras, con lo que
    Leche entera · 1,05 € · en DIA                       cuestan donde conviene comprarlas
    …y 3 más en la lista

    Ha bajado de lo tuyo               3 bajadas      <- pregunta 4, y el detalle -> /avisos
    Leche entera Lauki   -8,7 %
    DIA  1,15 €/l  1,05 €/l

    Precios del 2026-09-27. Se comparan cinco cadenas y se enseña el precio por unidad.

### Lo que se ve cuando algo falla

Va mas alla de las cuatro reglas de arriba, porque es la primera pantalla y es la que se ve
rota el primer dia:

    sin cuenta          una tarjeta que dice que hace la aplicacion y lleva a /ajustes. No
                        se enseña un cero ni un reparto vacio: no hay lista, no hay cero.
                        La tarjeta de bajadas se titula **«Lo que más ha bajado»**, no «de lo
                        tuyo»: el campo `solo_mios` de la respuesta dice si el servidor filtro
                        de verdad, y sin sesion no filtro
    sin lista           «Todavia no tienes lista» y «Ver lo de siempre y añadir». **Antes
                        decia «Lo que te falta: 0 cosas»** y un enlace a una lista vacia:
                        medido en un movil el 27 sep 2026, con una cuenta recien creada. Un
                        cero no es una respuesta, es un hueco con forma de respuesta
    todo cogido         «No te falta nada», en vez de un cero
    el reparto no
      ha cargado        se enseña el nombre de la linea y **nada mas**: ni cadena ni precio.
                        Un hueco es mejor que una cifra inventada
    no esta en el
      catalogo          la linea lo dice en vez de callarse: *«sin comparar: no está en el
                        catálogo»*, que es un dato, no un fallo
    sin bajadas         la tarjeta lo dice con la fecha de los precios a la vista y con la
                        regla (7 dias, solo lo tuyo), no con una pantalla en blanco. Sin
                        lista no dice «nada de tu lista ha bajado» -- eso es verdad y no
                        sirve: dice que todavia no hay nada que mirar

### Decisiones que se ven en el codigo

  - **El numero manda sobre el adorno.** «Te faltan 7 cosas» sale grande y con la cifra en
    ancho fijo (`.cifra`), que es la regla del proyecto para todas las cifras.
  - **No se tacha desde aqui.** Los pendientes **enlazan** a la lista. Tachar en el pasillo
    sin cobertura funciona porque `Cesta.tsx` tiene la cola del movil (`estado/cola.ts`);
    traer el boton aqui sin esa cola seria un boton que a veces no hace nada, que es peor que
    no tenerlo. Cuando la cola se pueda reutilizar entera, este es el sitio.
  - **Lo de arriba es lo unico que cambia de sitio.** El buscador estaba en `/buscar` y ahora
    esta en las dos: en `/buscar` sigue el de siempre, con sus filtros y su mosaico, y el de
    Inicio solo escribe la direccion. Dos buscadores con la misma logica en dos ficheros es
    como se acaba con dos comportamientos; por eso el de Inicio no busca, navega.
  - **La pantalla se diseño con Stitch** (proyecto `15743377346721964880`, pantalla «Cesta ·
    Pantalla Principal», `.stitch/DESIGN.md`), y se porta a mano a React/Tailwind. El HTML de
    Stitch **no se pega**: trae Tailwind por CDN y dos `<script>`, y la CSP de Caddy
    (`script-src 'self'`, `style-src 'self'`) lo tumba. Stitch da la composicion; los tokens,
    la CSP y las areas de 44 px los pone el codigo.

Lo comprueba `plataforma/prueba_produccion.py` en cada pasada («la primera pantalla contesta
las cuatro preguntas»): que el resumen, las bajadas y el buscador **estan ahi y con datos**, y
que la barra lleva a Inicio. Si se entienden a la primera lo dice la prueba de los quince
segundos, que no la puede cerrar quien escribe el codigo.

---

## 1. Entrar

**[hecho]**

Usuario, contrasena, y el nombre de la app. Nada mas: no hay registro, no hay
"he olvidado mi contrasena" (las cuentas las crea David desde el contenedor).

    error   "Usuario o contrasena incorrectos." Sin decir cual de los dos.
    tras    si habia una invitacion pendiente en el enlace, se aplica ahora
            y se avisa: "Ya estas en «Casa»"

---

## 2. Buscar

**[hecho]** el buscador, los filtros de cadena, los resultados con foto, **el mosaico de
habituales** (`componentes/Mosaico.tsx`, 23 sep 2026)
**[falta]** la voz (tarea 3), el escaner en el buscador (tarea 8; el escaner tiene su
propia pantalla desde antes)

### Los resultados, en un movil: dos lineas, y el precio a la vista

**Rehecho el 27 de septiembre de 2026, y la razon es una medida.** Hasta ese dia esta pantalla
era una tabla de seis columnas con `min-width: 52rem` dentro de una caja con scroll horizontal
(`TablaScroll`), con el aviso *«Desliza la tabla para ver todas las columnas →»*. En un movil de
390 px eso significa que **se veian «Producto» y «Cadena», y el PVP y el €/L quedaban fuera de la
pantalla**. Lo dijo una captura, no una prueba: la tabla estaba entera en el HTML, con sus
`scope="col"` y su `aria-sort`, y aun asi la respuesta a *«¿esto esta caro?»* no se veia sin
deslizar. Un aviso que pide deslizar es una instruccion, no una respuesta.

Por debajo de 640 px se pintan **filas de dos lineas** (`componentes/TablaResultados.tsx`,
`FilaCompacta`), y por encima sigue la tabla de siempre:

    PRODUCTO                              PVP        POR UNIDAD
    ┌────┐ Leche entera Hacendado       0,96 €        0,96 €/l
    │foto│ mercadona · Hacendado                   hasta 1,29 €/l
    └────┘ ahorras un 34,4 %
           [oferta solo con tarjeta] [comparable · 5 cadenas] [C]

    ORDENAR POR  Lo de siempre ▸        <- plegado: abierto son cinco botones de 44 px

Lo que se decide ahi, y por que:

  - **El precio no se va de la pantalla.** Nombre, cadena, ahorro y sellos a la izquierda; PVP y
    precio por unidad a la derecha, los dos con `cifra` (ancho fijo) para que se lean en columna.
  - **El ahorro sube al lado del nombre** (`SelloAhorro`): era una columna mas de la tabla y en
    dos lineas no cabe, pero es la respuesta corta a la pregunta 2. Y **`0.0` no es un cero**:
    es el centinela de «no comparable» o «dudoso» y se dice con palabras, no con un 0 %.
  - **Las cinco cadenas, encima de los resultados y a un toque.** Estaban solo dentro del panel
    de filtros, que va plegado: para mirar «leche entera» en una sola cadena habia que abrir un
    panel y saber que ahi estaba. Comparar entre cadenas es la razon de ser de la aplicacion.
    **Sin cuentas por cadena**: la API no las manda, y contar estas cuarenta filas no da el
    numero del catalogo (el diseño de Stitch las ponia, y se han quitado por eso).
  - **El orden va plegado, y el `summary` dice cual hay puesto**: abierto son cinco botones de
    44 px, dos filas y 110 px, y en un movil cada 110 px de controles es una fila de resultados
    menos en la primera pantalla.

Medido despues del cambio, con la puerta mecanica: **nada que deslizar** (390 px de ancho en una
caja de 390), **0 de 8 cifras fuera** de la pantalla, las cadenas a un toque (5) y filtrando de
verdad (filtrando por `alcampo`, las 8 primeras filas son de Alcampo y ninguna de otra cadena).

### Lo que se ve al abrir, con el buscador vacio

**Ojo con el titulo de esta seccion: desde el 27 de septiembre la aplicacion no abre aqui**,
abre en Inicio (arriba). A `/buscar` se llega escribiendo en el campo de Inicio o desde la
barra. Lo que sigue es lo que se ve al abrir **esta** pantalla, con el buscador vacio, que
era aqui donde estaba la mejora mas grande que quedaba por hacer. Hoy:

    [ buscar...                          🎤  📷 ]     <- la voz, todavia no
    [ Alcampo ][ Aldi ][ Carrefour ][ DIA ][ Merc ]

    Lo de siempre
    Un toque y a la lista. Lo tocado se cambia en la cesta.
    ┌──────┐ ┌──────┐ ┌──────┐
    │ foto │ │ foto │ │ foto │      cuadricula de 3 columnas
    │Leche │ │Atun  │ │Papel │      un toque = a la lista
    │0,95 €│ │3,45 €│ │2,10 €│      12 tarjetas por defecto
    │Añadir│ │Añadir│ │Añadir│
    └──────┘ └──────┘ └──────┘

Sale de `GET /api/habituales`, con **tres escalones** en el campo `origen`: lo que ha
comprado esta persona (`tuyo`), lo mas comprado por todos (`de todos`) y una compra
basica fija (`basico`), para que la cuadricula **no se vea vacia el primer dia**. El
`origen` viaja **en cada tarjeta** desde el 23 de septiembre de 2026 -- una cuadricula
puede mezclar escalones y no valen lo mismo -- y la cuadricula lo dice cuando mezcla,
que es cuando hay algo que decir.

**Y sin historial no sale la cuadricula: sale la tarjeta de la primera vez**
(`componentes/LoQueSeCompra.tsx`, cuatro productos que compra todo el mundo con su
diferencia de hoy). Es la decision que evita el peor primer dia: 24 recuadros de compra
basica no explican para que sirve la aplicacion; cuatro precios con su diferencia, si.
Primero se entiende, despues se usa. El que decide entre las dos es `Mosaico`, en un solo
sitio: con la condicion en dos sitios, el dia que una cambie se pintan las dos cosas.

### Lo que has buscado

Debajo de los ejemplos, y solo con el buscador vacio, van **las ultimas busquedas** (ocho,
las mas recientes primero, sin repetir) como chips que lanzan la busqueda de un toque. La
compra se repite cada semana y "leche entera" es la misma busqueda que la de la semana
pasada: escribirla otra vez, de pie y con una mano, es el trabajo que hay que quitar.
Viven en el aparato (`estado/busquedasRecientes.ts`), no viajan, y se apuntan con un
segundo de calma y solo si la busqueda encontro algo -- si no, la lista se llena de "l",
"le", "lec" y de busquedas que no sirven.

El titulo de la pestaña se pone por ruta (`App.tituloDe`) y la ficha y el grupo lo mejoran
con **el nombre del producto**: con diez pestañas abiertas, "Producto" no distingue una de
otra.

**Y mientras carga, un hueco con la forma de lo que viene** (`Esqueleto`, `ui.tsx`): filas
del alto de una fila para los resultados y para las líneas de la lista, y una cuadrícula de
tres columnas para el mosaico. Antes era una línea de texto, y al llegar cuarenta
resultados todo lo de abajo bajaba de golpe -- en una pantalla que se usa de pie y con una
mano, con el pulgar ya camino de un botón.

**Esto cambio el 23 de septiembre, y se cuenta en vez de borrarse.** Antes decía:

> ~~Si no hay historial, no se pinta nada y se ve solo el buscador. No se rellena con
> "populares": no es lo mismo y no sirve.~~

El encargo de ese dia (`Claude outputs/ENCARGO-UX-23SEP.md` §5) pidio lo contrario, y
con una razon que gana a la de antes: **una pantalla en blanco es el peor momento de
la aplicacion y el unico que todo el mundo ve**, y es justo el momento en que alguien
decide si vuelve. Lo que se mantiene del criterio viejo es la parte que importaba:
**no se mezclan sin decirlo**. Por eso `origen` viaja en la respuesta y la pantalla
puede decir *«todavia no se lo que sueles comprar»* mientras ensena lo de todos.

## 2. Avisos

**[hecho] el 23 de septiembre de 2026.** La pantalla del punto 6 del encargo, y una de las
cinco de la barra de abajo. Existe porque la alerta **ya no salta solo si entras a mirar**:
la mira el vigilante de la API en cuanto cambia gold, y esto es lo que se ve cuando salta.

    Ha bajado
      Aceite de oliva virgen extra
      esta al precio mas bajo de los ultimos 90 dias: 3,89 EUR/l en alcampo

    Salio y ya no esta a ese precio
      Cafe molido
      ha bajado un 18,0 % desde 2026-09-16: 2,50 EUR/kg en dia
      Salto hace 2 dias · 23/09/2026

    [ Ya los he visto (2) ]

    Esperando
      Pan de molde            Te aviso cuando este en su precio mas bajo de 90 dias

**La frase la escribe el servidor, no la pantalla**: `por_que` para las que se cumplen hoy
y `salto_texto` para las que saltaron. La guardada **no se recalcula** -- se midio contra
el gold de aquel dia, y gold es otro cada manana -- porque un aviso que cambia de texto al
dia siguiente no es un aviso, es un rumor. Y una promesa no se escribe como un hecho: lo
que no se ha cumplido va aparte, debajo.

El punto del icono cuenta **lo que ha saltado y nadie ha visto**, no lo que hay: abrir la
pantalla en el autobus no puede dar por leido nada, asi que se apaga con «Ya los he visto».
La campana, para pedir un aviso, esta en la ficha del producto (`componentes/Campana.tsx`).

Si el nombre del producto no llega, la pantalla **no afirma nada**: dice *"Un producto que
sigues"* y enlaza a la ficha. Pueden ser dos cosas -- que el grupo ya no este en el catalogo
o que la API que corre sea mas vieja que la pantalla --, y decir la primera cuando pasa la
segunda seria mentir sobre un producto que existe.

### Sin seguir ningun producto (27 de septiembre de 2026)

    No sigues ningún producto
    Esto sirve para que la aplicación te busque a ti en vez de que tú entres a mirar:
    te aviso cuando lo que sigues esté en su precio más bajo de 90 días, y sale aquí,
    con la frase que lo explica.

    [ Buscar un producto ]  [ Ver lo que ha bajado esta semana ]

    En la ficha de un producto, el botón se llama «Avisarme si baja».

**Antes eran dos cajas que se contradecian.** Medido en una captura de un movil el 27 de
septiembre de 2026, con una cuenta que no seguia nada: la pantalla decia *«Esperando ·
Todavia no se ha cumplido. Te aviso yo.»* con **cero** avisos y, dentro de esa misma tarjeta,
la caja que decia *«No sigues ningun producto»*. Una tarjeta que dice «esperando» cuando no se
espera nada no informa: confunde, y encima tapa la que si valia. Ahora la tarjeta «Esperando»
solo se pinta si hay algo que esperar (y si todo ha saltado ya, la tarjeta lo dice:
*«Ninguno esperando: los que sigues ya han saltado»*).

**Y el caso vacio da por donde empezar.** Acababa en «abre la ficha de un producto y pulsa
"Avisarme si baja"»: es correcto y es un callejon sin salida, en la pantalla que esta a un
toque de la barra de abajo. Ahora lleva al buscador y a lo que ha bajado esta semana, que son
las dos cosas que se pueden hacer en ese momento.

---

### Los resultados

Una tarjeta por grupo: foto, nombre, cuantas cadenas, el ahorro si lo hay,
precio desde. Se abre y salen las filas por cadena, ordenadas de barata a cara,
con su barra de color.

    vacia   "Nada con «xxx». Prueba con una palabra mas corta, o vuelve a
             activar alguna cadena."   <- dice que hacer
    rota    "No llego a casa ahora mismo. Tu lista sigue disponible en la
             pestana Lista."           <- dice que si funciona

### El microfono **[falta — tarea 3]**

`SpeechRecognition` del navegador. Rellena el campo de busqueda y ya. **No es un
asistente.** Si el navegador no lo soporta, **el boton no se dibuja**. No se
dibuja y falla al pulsarlo: no se dibuja.

### El escaner **[falta — tarea 8]**

Abre la camara a pantalla completa con un marco en el centro. Al reconocer un
codigo, vibra (`navigator.vibrate`, si existe) y abre la ficha del punto 6.

    sin camara o sin permiso   el boton NO SE DIBUJA
    sin HTTPS                  tampoco: getUserMedia no funciona sin el
    codigo desconocido         pantalla 3 del punto 6, con salida al buscador

---

## 3. La lista

**[hecho]** las dos secciones, el marcador, las novedades, compartir
**[falta]** notas (tarea 5), agrupar por pasillos (tarea 1), cerrar compra
(tarea 10)

### Lo que se ve

    Casa
    9 por coger · 4 en el carro

    ┌─────────────────────────────────────────┐
    │ VA A COSTAR              23,40 € en el  │
    │ 47,30 €                  carro          │
    │ aproximado, cogiendo      23,90 € por   │
    │ cada cosa donde este      coger         │
    │ mas barata                              │
    │ ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░               │
    └─────────────────────────────────────────┘

    POR COGER                               9

    ○ [foto] Leche entera 1 L        1,90 €
             lo puso Mama             0,95 c/u
             [−] 2 [+]

    EN EL CARRO                             4

    ● [foto] ~~Atun en aceite~~      3,45 €
             lo cogio Mama

    DÓNDE COMPRO CADA COSA                   <- desde el 27 sep 2026, debajo de la lista
    ...                                        (antes iba arriba y tapaba lo que hay que tachar)

**Dos secciones, no una lista tachada.** En el pasillo miras la lista veinte
veces y lo que necesitas saber cada vez es *que me queda*. Si lo tachado sigue en
medio, hay que leerlo todo para descartarlo.

**Y la lista va antes que el reparto por tiendas, desde el 27 de septiembre de 2026.** La
tarjeta «Dónde compro cada cosa» (`componentes/RepartoEnTiendas.tsx`) estaba justo debajo del
total, con una razon escrita: *«es la pregunta que sigue a "¿cuanto cuesta?", que es "¿y donde
lo compro?"»*. La razon es buena y el sitio estaba mal, y lo dijo una medida: en un movil de
390 x 844 esa tarjeta mide **592 px** y empujaba la primera cosa que se puede tachar hasta
**1.269 px**, con la banda util en 109..787. O sea que en la pantalla donde se tacha **no se veia
nada que tachar sin desplazar**, y eso es la condicion (a) rota. Ahora la lista manda y el
reparto va debajo; la pregunta «¿y donde lo compro?» sigue contestada en la primera pantalla
(`Inicio`), que ademas es donde se hace antes de salir de casa. Medido despues del cambio: la
primera linea de la lista esta a **661 px**, dentro de la banda.

### Agrupar por pasillos **[falta — tarea 1]**

Dentro de "Por coger", subtitulos por seccion, en el orden en que se recorre una
tienda:

    fruta y verdura · carniceria · pescaderia · lacteos y huevos · panaderia ·
    despensa · desayuno y dulces · aperitivos · congelados · bebidas ·
    droguería y limpieza · higiene y belleza · bebe · mascotas · hogar

Lo que no tenga seccion va al final, bajo "otros". **No se inventa una seccion**
para que no quede feo.

### Las novedades

Al abrir, si la otra persona ha tocado algo desde tu ultima visita:

    "Mama cogio la leche · Mama puso papel de cocina"

Sin esto, una lista compartida es un sitio donde las cosas aparecen y desaparecen
solas.

### Sin conexion

    "Sin conexion con casa. Esto es lo ultimo que vi; lo que cambies se
     guardara y se subira al volver."

Y si hay cola pendiente: "3 cambios por subir". Al volver la red se suben solos
y sale un aviso flotante.

### Cerrar la compra **[falta — tarea 10]**

Un boton al final: "He terminado la compra". Guarda lo que iba en el carro como
una compra, lo quita de la lista, y deja lo que no se cogio. Es lo que genera el
historial del que vive todo lo de diciembre.

---

## 4. Donde la compro

**[hecho]**

    TODO EN UNA TIENDA
      Alcampo        48,10 €     tiene los 14
      Mercadona      47,30 €     no encuentro: cafe en grano 1 kg, atun pack 6
      Carrefour      51,05 €     tiene los 14
                                 las ofertas te quitan 3,15 €

    REPARTIDO
      Alcampo + Mercadona    41,80 €
      9 en Alcampo, 5 en Mercadona
      ahorras 6,30 € yendo a dos sitios

**Lo que falta se dice por su nombre.** "Le faltan 2" no sirve para decidir.

**Si el reparto ahorra poco, se dice y no se propone**: "Repartir entre dos
tiendas solo ahorra 0,80 €. No compensa el viaje."

---

## 5. Favoritos

**[hecho]** la lista basica
**[falta]** ordenar por lo que ha cambiado (necesita mas historico)

Los pocos productos que se compran siempre. **No es una lista larga: es una
pantalla de vigilancia.** Ordenados por lo que ha cambiado, no alfabeticamente:
lo que ha bajado arriba, lo que ha subido debajo, lo quieto al final.

    vacia   "Todavia no sigues nada. Busca un producto, abrelo y pulsa Seguir."

---

## El grupo: la pantalla que se abre al buscar

**[hecho]** desde el primer dia; **reordenada el 27 de septiembre de 2026**

Es la pantalla a la que se llega **buscando** (`/grupo/<id>`), y la que contesta la pregunta 2 de
la barra (a): *«esto que tengo en la mano, ¿esta caro?»*. No tenia seccion propia en este
documento hasta hoy, y es la que mas se usa: el apartado 6 de abajo es la hoja del producto
(`/producto/<cadena>/<id>`), que es otra cosa.

    ‹ Volver   | 📷 Escanear un código

    [foto]  Leche entera                    <- foto de 72 px, al lado del nombre
            [ Añadir a la cesta ] [ Guardar ]
            [ Avisarme si baja ]
            5 productos · 5 cadenas · por l
            [datos del 27 sept 2026]

    Es la mas barata de las 5 cadenas: te ahorras 0,33 € frente a la mas cara.
    ALTERNATIVA QUE GANA CONTIGO ......... Aldi · 0,96 €/l
    DIFERENCIA ENTRE LA MAS CARA Y LA MAS BARATA ... 34,4 % · 0,33 € por unidad
    PRECIOS QUE DECIDEN .................. 5 de 5
    DATOS DEL ............................ 27 sept 2026

    ALDI        la mejor contigo · al día
      Leche entera Milsani 1 L        0,96 €   0,96 €/l
    CARREFOUR
      Leche entera Lauki 1 L          1,15 €   1,15 €/l

    ▸ Ver las otras 3 cadenas   Alcampo · Dia · Mercadona

**El orden no es negociable**: la respuesta (la frase) antes que los numeros y antes que la
tabla, y la tabla antes de la ficha tecnica. Lo que si se ha cambiado es **cuanto se enseña de
golpe**, y lo dijo una medida del 27 de septiembre de 2026 en un movil de 390 x 844: la pantalla
entera medía **3.592 px, 4,3 pantallas**, y **1.600 de esos píxeles eran las cinco tarjetas de
cadena una debajo de otra**. Se cambiaron dos cosas:

  - **La foto ya no se lleva su propia linea.** Medía 96 px y la columna de texto exigia 16rem
    (256 px), asi que en 390 px no cabian juntos: la foto se iba arriba y **el nombre caia a
    297 px**, con la frase detras. Ahora la foto mide 72 px, el texto usa `min-w-0`, y el nombre
    esta a **185 px**.
  - **Dos cadenas a la vista y el resto plegado**, con las otras dichas en el resumen («Ver las
    otras 3 cadenas · Alcampo · Dia · Mercadona»). Lo que se viene a saber es donde esta mas
    barato, y eso lo dicen la primera y la segunda: `columnas` ya viene ordenado por lo que
    conviene a esta persona. Medido despues: **2.383 px, 2,8 pantallas**.

La comprueba la puerta en cada pasada: dos cadenas visibles sin pedirlas, el nombre por encima de
300 px, el resto plegado y **que al abrirlo salgan las cinco**.

---

## 6. La ficha del producto

**[hecho]** la hoja con foto, precio, alergenos, ingredientes, Nutri-Score
**[falta]** la nota nueva (tarea 9), "hay uno mejor y mas barato" (bloqueado)

Media pantalla que sube desde abajo. **El orden es el orden en que se mira algo
en el pasillo**, y no es negociable:

    1  la oferta, si la hay          lo que cambia el precio
    2  precio y precio por kilo
    3  alergenos                     EN ROJO: es lo unico que puede hacer dano
    4  ingredientes
    5  Nutri-Score y NOVA            se entienden de un vistazo, van despues
    6  la nota / la gama
    7  origen, codigo de barras
    8  "verlo en <cadena>"

### Apuntarlo y seguirlo, desde la ficha (27 de septiembre de 2026)

**La pantalla `/producto/<cadena>/<id>` no tenia ni «Añadir a la cesta» ni la campana**, y a
ella se llega **escaneando el codigo de barras**: el caso *«lo conozco y puedo comparar»* de
abajo, que termina en «+ ficha + anadir», obligaba a volver al grupo a buscarlo con el paquete
en la mano. Ahora lleva las dos cosas, en el mismo sitio que la ficha del grupo (debajo del
nombre y de la linea de datos, antes de la frase), y con **el mismo componente**
(`componentes/BotonAnadirACesta.tsx`, sacado de `Grupo.tsx` ese dia): dos copias del boton
habrian acabado en dos comportamientos.

Dos reglas mas que se ven en esta pantalla y que costaron una captura:

  - **Lo que se lee lleva tildes y los nombres van como se llaman.** La frase decia «Cuesta un
    41 % mas que en mercadona.»: sin tilde en «más» y con la cadena en minusculas, mientras el
    resto de la aplicacion escribe «Todavía no tienes lista» y «Mercadona». Es **la frase que
    mas se lee de toda la aplicacion** -- es la respuesta a la pregunta 2 -- y se juzga contra
    alguien que lee español, no contra el codigo (`logica/frase.ts`).
  - **La etiqueta de una celda apilada lleva su espacio dentro del texto.** El nombre de la
    columna se pinta en cada celda cuando la tabla se apila, y con el espacio solo en el margen
    (`mr-1`) se leia «precio1,95 €»: un lector de pantalla lee `innerText`, no margenes.

### Cuando no hay datos

    nota sin datos   "no lo se", nunca un cero ni una nota gris
    sin alergenos    no se pone la fila. No se pone "sin alergenos conocidos",
                     que se lee como "no lleva" y no es lo que sabemos.

### Las cuatro respuestas del escaner **[falta — tarea 8]**

La misma hoja, entrando por codigo de barras:

    1  LO CONOZCO Y PUEDO COMPARAR   (42 %)
       "3,45 € aqui. En Alcampo 2,89 (-16 %)" + ficha + anadir

    2  LO CONOZCO, UNA SOLA CADENA
       "Lo tengo en DIA a 3,45 €. No lo encuentro en las demas."
       No inventar una comparacion que no existe.

    3  NO LO CONOZCO                 (lo normal en Alcampo y Aldi)
       "No tengo este codigo. Puede ser marca propia de Alcampo o Aldi,
        que no publican codigo de barras."
       + buscador por nombre. No un callejon sin salida.

    4  SIN NUTRICION                 (54 % de los que conozco)
       El precio se ensena igual. Donde iria la nota, "no lo se".

---

## 7. Compartir

**[hecho]**

    "Mandale este enlace. Al abrirlo entra en la lista y puede escribir en ella.
     Caduca en 7 dias y sirve para 3 personas."

    [ https://cesta:8080/unirme/abc123 ]  [ Copiar ]

    QUIEN ESTA DENTRO
    David  @david        creo la lista
    Mama   @mama         escribe

    [ Anular los enlaces que haya dado ]

**Por enlace, no por @usuario.** Pedirle a alguien que teclee `@davidpeve01` es
pedirle que se equivoque.

Si el navegador no deja copiar al portapapeles, el texto se queda seleccionado y
el boton pone "Copialo". Nadie se queda sin el enlace.

---

## 8. El panel

**[hecho]** cadenas, movimiento, marca propia, lo que falta por historico
**[falta]** secciones (bloqueado por tarea 1 y 2), productos

Es para David, no para su madre, y por eso va en su propia pestana.

**Cada numero lleva al lado de donde sale y de que fecha es.** Un panel que
ensena un 19,3 % sin decir sobre cuantos grupos no es un panel, es una opinion
con tipografia.

**El aviso de la calidad se ensena siempre** en la pantalla de marcas: dice que
porcentaje de las letras salen del precio. Sin el, el estudio se lee al reves.

**Lo que aun no se puede medir se dice, con la fecha**: "tendencia_30d — faltan
18 dias". No se dibuja una linea plana con doce puntos y se la llama tendencia.

### El panel de matching (`/panel/matching`), 27 de septiembre de 2026

Es la pantalla que **audita el emparejador**, y desde hoy tiene su composicion propia (diseñada
con Stitch, proyecto `15743377346721964880`):

    Panel de matching            [datos del 27 sept 2026] [pasada 20260927-120959]

    Esta pantalla no valida nada
      No hay botón de aprobar ni de rechazar equivalencias... Lo que se puede hacer aquí
      es auditar por qué el emparejador aceptó un par.

    Última pasada — Versión 2026-09-22.1 · umbral 0,55
      EJECUCIÓN 20260927-120959 · PRODUCTOS 53.014 · UMBRAL 0,55 · PASADAS GUARDADAS 28
      Huella del catálogo: 8bbfbc46… Dos pasadas con la misma huella se pueden comparar.

    Métricas de la pasada
      enlaces                     valor 22.801   antes 22.774   cambio ↑ 27
      grupos_comparables          valor  8.808   antes  8.829   cambio ↓ 21

    Muestra de pares aceptados — los primeros 20 de esta pasada
      PRODUCTO A  Bebida de melocotón Granini pack 3 minibrik de 20 cl.  carrefour:538002036
      PRODUCTO B  Bebida de zumo de melocotón Granini pack 3 x 200 ml    dia:2225
      [mismo código de barras]  método ean  confianza 1
      ▸ Por qué: 8 rasgos

Tres decisiones que se ven en la pantalla:

  - **Los pares son tarjetas, no una tabla de seis columnas.** Era una tabla con 52rem de ancho
    minimo, y en un movil de 390 px habia que deslizar de lado para ver el metodo o la
    confianza, con los dos nombres de producto aplastados. Una tarjeta por par: los dos
    productos, sus tres datos en una tira corta y los rasgos debajo, que es lo que se viene a
    auditar. La pantalla queda mas larga (8,9 pantallas con 20 pares) y se lee por pares, que es
    como se audita: un par cada vez, y el selector para pedir mas.
  - **La flecha dice el sentido; el color no dice nada.** El «Cambio» iba en verde si subia y en
    rojo si bajaba, y eso es un veredicto que esta pantalla no puede dar: subir no es bueno ni
    malo (`grupos_comparables` arriba es mejor; `grupos_dudosos_ud` arriba es peor), y el aviso
    de arriba dice justo que aqui no se valida nada. En este proyecto el color dice algo (bueno,
    aviso, dudoso); si no lo puede decir, no se pinta.
  - **«Muestra», y con el numero que se ha pedido.** La API no manda el total de pares de la
    pasada, asi que decir «los 20 pares» afirmaria que solo hay veinte. Son los primeros N.

Y dos cosas que se arreglaron midiendo: el umbral se pintaba como sale de la API («0.55») tres
lineas encima de su propio dato («0,55»), y los enlaces a los productos de un par median **21 px**
de alto y el desplegable de la respuesta en crudo **332 x 20** (los dos, con la puerta mecanica).

---

## 9. Ajustes

**[hecho]** cadenas cercanas, reparto, salir
**[falta]** el aviso legal (tarea 5)

    SUPERMERCADOS QUE TENGO CERCA
    Los que quites no salen en las busquedas ni deciden donde comprar.
    Si no tienes un Aldi al lado, no tiene sentido que te diga que es el mas
    barato.

    [ Alcampo ][ Aldi ][ Carrefour ][ DIA ][ Mercadona ]

    LA APP
    Repartir entre dos tiendas                              [====O]
    Cerrar sesion                                          [ Salir ]

    Los precios son orientativos y pueden variar. Cesta no esta afiliada,
    asociada ni patrocinada por ninguno de estos supermercados.
    Los datos viven en el ordenador de casa y no salen de ahi.
    Informacion nutricional de Open Food Facts, bajo licencia ODbL.

El tema claro/oscuro sale del sistema. No hace falta un interruptor, y no hacen
falta siete colores de acento.

---

## 10. Lo que no hay, y no debe haber

**Pantalla de bienvenida o tutorial.** Si hace falta explicarla, esta mal hecha.

**Pantalla de actividad.** `anadido_por` y `tachado_por` en cada linea bastan.
Una pantalla de actividad es un producto de equipo, no una lista de la compra.

**Valoraciones ni comentarios de productos.** Sois dos.

**Publicidad ni patrocinados.** Ni ahora ni nunca: el dia que un producto suba
en la lista por dinero, la app deja de servir para lo que se hizo.
