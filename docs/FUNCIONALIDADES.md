# Cesta — catalogo de funcionalidades, con veredicto

Una fila por idea, con **lo que costaria**, **lo que aguantan nuestros datos** y
**que hacemos con ella**. Sirve para decidir rapido y para no volver a discutir
lo ya decidido.

Los numeros estan medidos el 17 de septiembre de 2026. `docs/COMPETENCIA.md`
explica de donde sale cada idea.

Leyenda del esfuerzo, contando a alguien que ya conoce el proyecto:

    XS   menos de media jornada
    S    una jornada
    M    dos o tres jornadas
    L    una semana
    XL   mas de una semana

---

## A. Hacerlo ya

### A1 · Secciones comunes y lista ordenada por pasillos

    esfuerzo   M   (el fichero ya esta al 97 %)
    datos      849 claves; propuesta automatica cubre el 95,9 % de productos
    bloquea    Explorar, panel de secciones, analisis por linea de producto
    de donde   QueFalta, Bring!, Listonic: las tres lo tienen

Lo que mas se nota andando por el supermercado. Ver `BACKLOG.md` tarea 1.

### A2 · Mosaico de lo habitual

    esfuerzo   S
    datos      ya los tenemos: lista_linea guarda anadido_por y anadido_en
    riesgo     ninguno; si no hay historial, no se pinta
    de donde   Bring! ("tiles"), Listonic ("suggestions from shopping history")

Cuadricula con foto de lo que esa persona mas ha anadido, a un toque, cuando el
buscador esta vacio. Anadir pasa de escribir-buscar-abrir-pulsar a un toque.

### A3 · Voz para buscar

    esfuerzo   XS
    datos      ninguno; es del navegador
    riesgo     en iOS solo Safari y pide permiso
    de donde   Listonic

`SpeechRecognition` del navegador. **No es un asistente**: rellena el campo de
busqueda. Si el navegador no lo soporta, **el boton no se dibuja**.

### A4 · Escaner de codigo de barras

    esfuerzo   M
    datos      23.312 codigos reconocidos
               42 % permiten comparar precio
               46 % traen algo de nutricion
               0 % de la marca propia de Alcampo y Aldi
    riesgo     ALTO si no se avisa de la cobertura
    de donde   Yuka, El CoCo, y el "lector de precios" de Mi Carrefour

Nuestra funcion diferencial. Ver `BACKLOG.md` tarea 3 para el detalle tecnico y
las cuatro respuestas que tiene que saber dar.

### A5 · La oferta mientras anades

    esfuerzo   S
    datos      hechos: core/promos.py, 10 pruebas en verde
               3.078 productos de Alcampo y 1.144 de Carrefour con texto de oferta
    de donde   Tiendeo

Mejor que ellos porque sabemos la mecanica: no "hay promo" sino "llevando dos,
1,50 EUR menos por unidad".

### A6 · Notas por linea

    esfuerzo   XS
    datos      el campo `nota` ya existe en lista_linea y la interfaz no lo usa
    de donde   Bring!, Listonic

"la de cristal", "si hay del grande".

### A7 · El aviso legal

    esfuerzo   XS
    de donde   QueFalta, y es correcto

*"Los precios son orientativos y pueden variar"* y *"Cesta no esta afiliada,
asociada ni patrocinada por ninguno de estos supermercados"*.

### A8 · Traer de Open Food Facts lo que no traemos

    esfuerzo   S
    datos      nutrientes 11.723 · categorias 10.209 · sellos 8.055
               (sin gluten 2.667, ecologico 1.205, vegano 763, sin lactosa 717)
    no sirve   el origen: techo realista 3,7 % del catalogo

Tres lineas en `CAMPOS` de `core/off.py`. Los sellos son el hallazgo util.

---

## B. Despues de arreglar los grupos anchos

Todas estas **producirian resultados vergonzosos hoy**. No es que falte
programarlas: es que darian respuestas malas.

### B1 · "Hay uno mejor y ademas mas barato"

    esfuerzo   S  (despues de los grupos)
    datos hoy  189 grupos con un par mejor-y-mas-barato, 50,6 % de diferencia
    problema   los ejemplos actuales mezclan patatas de bolsa con patatas
               congeladas. Es el error que la OCU le achaca a Yuka.
    de donde   Yuka

### B2 · Pantalla de secciones del panel

    esfuerzo   S
    problema   el agua con gas sale con un 167 % de diferencia porque el grupo
               mete Perrier con la marca blanca. Mide la anchura del grupo, no
               el ahorro.

### B3 · Explorar por categoria

    esfuerzo   S  (despues de A1)
    problema   sin secciones no hay por donde navegar

---

## C. La nota de producto, rehecha

### C1 · Puntuacion absoluta estilo Yuka

    esfuerzo   M
    formula    60 % Nutri-Score · 30 % aditivos · 10 % ecologico
               (publicada por Yuka; si hay un aditivo de riesgo alto, tope 49/100)
    datos      22,6 % de nuestros productos tienen con que calcularla
    arregla    el problema de raiz de nuestra letra actual

**Por que merece la pena cambiar.** Nuestra letra A/B/C de hoy es una posicion
**dentro del grupo**, y cuando no hay ingredientes cae a ordenar por precio: el
76,9 % de las letras son el precio disfrazado. Una nota absoluta no se puede
confundir con el precio, se explica sola, y es la del sector.

**Lo que hay que conservar.** El campo de procedencia. Un producto sin datos no
saca un cero: saca **"no lo se"**, que es distinto y es lo que la OCU echa en
falta en Yuka y El CoCo.

**Lo que ya esta bien y no hay que tocar.** Nuestro contador de aditivos exige
"E" + tres o cuatro digitos, asi que **no cuenta los aromas como aditivos**,
que es justo el error que la OCU documenta en Yuka y MyRealFood. Comprobado: 2
falsos positivos en 400 productos.

---

## D. Cuando haya historial (diciembre en adelante)

### D1 · Despensa deducida

    esfuerzo   M
    datos      hace falta que se use la app unos meses
    de donde   la idea es de NoWaste, pero sin el inventario a mano

Cuando marcas algo "en el carro" y cierras la compra, ya sabemos que lo
compraste. De ahi sale, **sin que nadie teclee nada**, el historial que alimenta
"sueles comprar leche cada nueve dias, y hace once que no la pones".

Es el 20 % de una app de despensa que aporta el 80 % del valor. Las apps de
despensa se abandonan porque meter el inventario a mano es trabajo.

**Lo unico que hay que hacer ahora**: guardar el cierre de compra. Una tabla
`compra` con fecha, lista, quien y las lineas que iban en el carro. Cuesta poco y
sin ella, en diciembre no habra historial que mirar.

### D2 · Sugerencias del historial

    esfuerzo   S   (despues de D1)
    necesita   30 dias de listas hechas, minimo

### D3 · Aviso de caducidad

    esfuerzo   M
    condicion  solo si D1 demuestra que se usa

---

## E. Lo que se llena solo

Nada que programar. Se apunta para que nadie lo de por roto:

    tendencia_30d       necesita 30 dias   →  5 de octubre
    oferta_sospechosa   necesita 45 dias   →  20 de octubre
    posicion_90d        necesita 90 dias   →  diciembre
    estacionalidad      necesita un ano    →  septiembre de 2027

---

## F. Mas adelante

### F1 · Recetas a lista

    esfuerzo   XL
    de donde   Bring!
    por que no ahora  es un modulo entero: guardar recetas, sacar ingredientes,
                      y casarlos con productos del catalogo, que es el problema
                      del emparejador otra vez

### F2 · Clasificador de texto para las secciones

    esfuerzo   M
    condicion  solo si tras A1 quedan restos sin colocar
    datos      10.209 ejemplos etiquetados gratis en Open Food Facts
    como       TF-IDF y regresion logistica. Con ese volumen, una red neuronal
               seria absurdo.

### F3 · Modelo para el emparejador

    esfuerzo   L
    datos      1.748 pares verdaderos gratis (mismo EAN entre cadenas)
    riesgo     que aprenda de los productos que tienen EAN (marcas conocidas) y
               falle justo en marca blanca, que es lo que importa. Hay que medir
               los dos casos por separado antes de creerselo.
    condicion  **despues de arreglar los grupos anchos**, que eso no lo arregla
               un modelo

### F4 · App nativa y widget

    esfuerzo   XL
    por que no ahora  hoy somos una web servida por Caddy. Un widget pide app
                      nativa y eso es otro proyecto.

---

## G. Descartado, con motivo

Para no volver a proponerlo dentro de tres meses.

    Amigos por @usuario          sois dos; es burocracia
    Varios carritos activos      una lista de casa y alguna suelta bastan
    7 colores de acento          es bonito y no cambia nada
    Tarjetas de fidelizacion     son datos personales, algunas dan acceso a
                                 saldo, y solo ahorran abrir la cartera
    Inventario a mano            ver D1: la version deducida es mejor
    Pago con QR, cupones         hay que ser la cadena
    Escaneo de tickets por foto  reconocimiento optico sobre papel arrugado, con
                                 un formato por cadena, que se rompe cada vez
                                 que cambian el disenio. Si algun dia hace falta,
                                 la puerta es el **ticket digital** que ya dan
                                 Mercadona y Carrefour.
    "Enviar al supermercado"     automatizar una compra en su web en nombre del
                                 usuario. Ni sencillo ni limpio.
    Mas cadenas                  las nuestras se comparan entre si. Anadir sin
                                 poder emparejar es cambiar lo que nos hace
                                 utiles por una lista mas larga.
    Notificaciones push          necesitan servidor siempre accesible y el PC se
                                 apaga. Las novedades al abrir cubren el caso.
    Resolver el CAPTCHA          no se hace, ni a mano ni automatizado
