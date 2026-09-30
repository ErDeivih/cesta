# Cesta — la app en el movil, y que se aprende de QueFalta

Escrito el 17 de septiembre de 2026, despues de mirar QueFalta (quefalta.es) y
comparar con lo que teniamos.

---

## 1. Que hace QueFalta

Una lista de la compra compartida, y esta bien hecha. Lo que anuncia:

    grupos            "para tu pareja, familia o companeros de piso"
    sincronizacion    "cada cambio, al instante"
    catalogos         19 supermercados, con productos reales y fotos
    ficha             ingredientes, alergenos, nutricion, proveedor
    dos estados       "Por recoger" y "En el carrito", con total en vivo
    avisos            cuando alguien anade algo
    personalizacion   supermercados favoritos, tema, color, idioma

Lo que **no** hace, y es justo donde estamos nosotros: **no compara precios entre
cadenas**. Ensena el catalogo de un supermercado con su precio de referencia. La
pregunta "¿donde me sale mas barata esta lista?" no la responde.

---

## 2. Lo que hemos cogido de ahi, y por que

### 2.1 Dos estados, no una lista tachada

Esto es lo mejor que tienen y lo hemos copiado tal cual: **por coger** y **en el
carro**, como dos secciones separadas, no como una lista con cosas tachadas
mezcladas entre las que faltan.

La diferencia no es estetica. En el pasillo miras la lista veinte veces y lo que
necesitas saber cada vez es *que me queda*. Si lo tachado sigue en medio, hay que
leerlo todo para descartarlo.

Tecnicamente: `lista_linea.en_carrito`. Y como el movil viejo mandaba `tachado`,
las dos cosas se mantienen coherentes en el mismo `UPDATE`, para que una linea no
acabe "en el carro" pero sin tachar.

### 2.2 El total en vivo

Un numero grande arriba, pegajoso, que dice **lo que va a costar**, mas cuanto
llevas ya en el carro y cuanto te queda, con una barra de progreso.

Nuestra version tiene una ventaja que la suya no puede tener: **coge cada cosa
donde este mas barata entre las cinco cadenas**. No es el calculo de "donde la
compro" — ese pide elegir tienda y tener en cuenta lo que le falta a cada una —
sino el numero que se mira mientras se anaden cosas.

Se recalcula **en el movil** al tocar algo, sin esperar al servidor. Un numero
que tarda dos segundos en cambiar hace que la app parezca rota.

### 2.3 Fotos

Estaban en bronze desde el primer dia y no llegaban a gold. Ahora si, y en las
cinco cadenas al 100 %.

Una foto ayuda mas que cualquier texto cuando buscas algo que conoces de verlo en
la estanteria. Se cargan perezosas (`loading="lazy"`), que en una busqueda hay
cuarenta, y **se enlazan, no se copian**: las sirve el CDN de cada cadena.

### 2.4 La ficha del producto

Media pantalla que sube desde abajo. El orden es deliberado, y es el orden en que
se mira algo en el pasillo:

    1. la oferta, si la hay        lo que cambia el precio
    2. precio y precio por kilo
    3. alergenos                   en rojo: es lo unico que puede hacer dano
    4. ingredientes
    5. Nutri-Score y NOVA          se entienden de un vistazo, van despues
    6. composicion / gama
    7. origen, codigo de barras

Con la distincion de siempre: **calidad** si la letra sale de leer ingredientes,
**gama** si sale de ordenar por precio.

### 2.5 Invitar por enlace

QueFalta invita por enlace o por @usuario. Pedirle a alguien que teclee
`@davidpeve01` es pedirle que se equivoque. Un enlace se manda por WhatsApp y se
pulsa.

Nuestra version caduca a los siete dias y sirve para tres personas, y se puede
anular. Un enlace que dura para siempre acaba reenviado en un grupo que no era.
El codigo sobrevive al login: si tu madre lo abre sin sesion, entra primero y se
mete en la lista despues.

### 2.6 Novedades

Ellos mandan notificaciones push. Nosotros no podemos: el PC se apaga, y las push
necesitan un servidor siempre accesible.

Lo que si se puede, y cubre el 90 % del caso: **al abrir la lista, se ensena lo
que ha tocado la otra persona desde que tu la miraste**. "Mama cogio la leche",
"Mama puso papel de cocina". Sin eso, una lista compartida es un sitio donde las
cosas aparecen y desaparecen solas.

### 2.7 Ajustes

Supermercados que tengo cerca (los que quites no salen ni deciden), si quiero que
proponga repartir entre dos tiendas, y cerrar sesion. El tema claro/oscuro sale
del sistema y no hace falta un interruptor.

---

## 3. Lo que hacemos nosotros que ellos no

No por presumir: por saber donde esta el valor de este proyecto y no diluirlo
copiando una app de listas.

**Comparar el mismo producto entre cinco cadenas.** 6.448 grupos comparables, con
un 19,3 % de diferencia mediana entre la mas cara y la mas barata.

**Decir donde comprar la lista entera**, en una tienda o repartida entre dos, con
lo que falta en cada una dicho por su nombre.

**Entender las ofertas como reglas.** "2a unidad -50%" no abarata el producto,
abarata el par. Eso cambia que cadena gana.

**No mentir con la calidad.** El 76,9 % de nuestras letras salen de ordenar por
precio, y la app las llama gama, no calidad.

**Decir de cuando es cada precio**, y no dejar que uno de hace tres dias decida
en que tienda comprar.

**Los datos se quedan en casa.** No hay una nube con vuestra lista de la compra.

---

## 4. Las reglas de la interfaz en el movil

Las que han guiado el rediseno, por si hay que anadir una pantalla mas:

**Se usa con una mano y el carro en la otra.** La barra de navegacion abajo, no
arriba. Las areas de pulsar de 44 px para arriba. El circulo de meter en el carro
es de 30 px con margen alrededor.

**Nada espera al servidor para pintarse.** Anadir, tachar y cambiar cantidad se
ven al instante y se mandan despues. En el pasillo, un boton que tarda dos
segundos se pulsa tres veces.

**Lo que se hace sin cobertura no se pierde.** El identificador de cada linea lo
genera el movil, cada cambio viaja con la hora del movil, y la cola se sube sola
al volver la red.

**Si no hay conexion, se dice.** No una rueda girando para siempre: "sin conexion
con casa, esto es lo ultimo que vi".

**Un numero nunca aparece sin su contexto.** El total dice que es aproximado y de
que fecha son los precios. Lo que no tiene precio se cuenta aparte en vez de
contarse como cero.

**Ninguna tabla se desliza de lado: se apila.** Una tabla ancha se resolvia con scroll
horizontal dentro de su caja y un aviso («Desliza la tabla para ver todas las columnas →»), y
eso es una instruccion en vez de una respuesta: medido el 27 de septiembre de 2026 en un movil
de 390 px, **lo que quedaba fuera de la pantalla era la columna del precio** -- en el buscador
y en el panel. Por debajo de 640 px cada fila pasa a ser una linea propia, con las celdas
fluyendo debajo, y el nombre de la columna viaja **en cada celda** (`Td etiqueta="…"`) para los
numeros que no se explican solos. Lo hace `.tabla-scroll`, en un solo sitio, y lo vigila
`prueba_navegador.py` en catorce tablas de golpe.

**Y tampoco se sale la pagina entera.** Es la otra mitad, y la del material fue peor: un trozo
sin espacios -- una ruta, una URL, una lista entre llaves -- no se parte solo y **empuja la
pagina**, asi que hay que mover la pantalla de lado para llegar al final de cada linea. Medido
con `data/debug/quien_desborda.py`: dos documentos de la referencia medían **486 y 420 px en una
ventana de 390**. En el material se parte donde haga falta (`overflow-wrap: anywhere` en el
texto), y **el codigo no se parte: se desliza dentro de su bloque**, porque un comando con las
lineas rotas deja de ser el comando que se copia. Lo vigilan las dos puertas: `prueba_navegador`
en **todas las pantallas de la aplicación** (y en las diez pestañas del panel) y
`prueba_produccion` en las páginas del material. Aquí decía «trece pantallas» y se quedó viejo el
30 de septiembre de 2026, cuando la pasada sumó el buscador, favoritos y la pantalla de «esa
pantalla no existe»: **en este documento un número que se puede contar mejor no se escribe**.

**Los numeros que se leen pasan por `numero`, `euros` o `porcentaje`.** No por `toFixed`, que
escribe el punto decimal en ingles: «Te aviso si baja de 3.89 €», «8.5 de 100», «2.3 g», todos
medidos el 27 de septiembre de 2026 y todos al lado de precios con coma. En español el decimal
es una coma, y un numero escrito en otro idioma se lee como un error. Lo vigila
`tests/test_ui_movil.py` leyendo el codigo, porque eso no se ve en una captura: una coma y un
punto se parecen demasiado a 390 px.

**Y la pantalla se puede recorrer sin verla.** Imagenes con texto alternativo, botones que se
llaman de algo, campos con su etiqueta y **un solo `h1`** con los niveles sin huecos. Medido el
27 de septiembre de 2026 con `data/debug/accesibilidad.py` en las dos superficies: salieron
cinco casos -- Inicio, Buscar y el caso vacio de favoritos sin `h1`, la lista con un salto de
`h2` a `h4`, y el documento de operacion con tres `h1` -- y el contraste del texto ya pintado,
que era lo unico que ya se medía. Lo vigila `prueba_navegador.py` en todas las pantallas que
recorre, y `prueba_produccion.py` en las del material.

**El gris secundario es `text-tinta-suave`, no un `neutral-500` escrito a mano.** Es la regla que
ya estaba en `estilos.css` («los colores con significado, en un solo sitio») y que se salto en
tres sitios: `#737373` sobre el fondo oscuro da **3,19:1**, por debajo del 4,5:1 del texto de
cuerpo, y en la ficha del grupo eran **veinte textos** de una misma pantalla (los pesos del «por
qué está en esta posición»). Con la variable son dos colores, uno por tema, y nadie tiene que
acordarse del par. La puerta mide el contraste **en los dos temas** en cinco rutas -- y la ficha
del grupo entró ahí justo por esto: la medida existía desde el 23 de septiembre, pero no miraba
esa pantalla.

**Y la cara sin sesion tambien se mide.** El instrumento entraba siempre, asi que las pantallas
como las ve quien no ha entrado no las habia mirado nadie: con `--sin-sesion` salieron cuatro
sin `h1` y **el fallo mas serio de la sesion**: en `/avisos`, `useAlertas` tiene
`enabled: hay usuario`, asi que sin sesion la consulta no se lanza nunca y se queda en
`pending` para siempre -- quien no habia entrado y tocaba «Avisos» en la barra **se quedaba
mirando un esqueleto eterno**. Ahora esa pantalla dice «Entra para ver tus avisos» y por donde
se entra, como la cesta, los favoritos y los ajustes. Lo vigila `prueba_produccion.py`, que
empieza sin sesion.
