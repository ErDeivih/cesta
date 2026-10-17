LA FICHA DE PRODUCTO NO SE ABRE EN LO QUE SIRVE 8080, Y NO ES UN TIMEOUT.

Sondeo directo con patchright sobre http://127.0.0.1:8080 (dist CONSTRUIDO), contexto limpio:
  /compra                          PINTA   html=18552  texto= 360  main=1  consola=2
  /compra/despensa                 PINTA   html= 8825  texto= 119  main=1
  /compra/favoritos                PINTA   html= 9073  texto= 184  main=1
  /compra/analisis                 PINTA   html=20651  texto=1093  main=1
  /compra/comparar/526             PINTA   html=23083  texto=1734  main=1   <- 1 parametro
  /compra/cocina/x/v1              PINTA   html= 8967  texto= 193  main=1   <- 2 parametros
  /compra/productos/dia/147509     VACIA   html=   31  texto=   0  main=0  consola=0
  /compra/productos/dia/141787     VACIA   html=   31  texto=   0  main=0

No es el armazon, ni los parametros, ni la API, ni un parametro doble: es ESA ruta y solo esa.
Y pasa TAMBIEN contra el dist construido, no solo contra Vite.

Y el dato que mas dice: en /compra la consola tiene DOS mensajes (dos 401, que es como la app
pregunta «hay sesion?»), y en la ruta del producto tiene CERO. Ni los 401. O sea que la
aplicacion NO LLEGA A EJECUTARSE en esa ruta.

DESCARTADO, MIDIENDO: no es la redireccion (se cambio a la ruta real y sigue vacia); no es la
sesion (con sesion, igual); no hay ErrorBoundary en la app; no es Vite (igual en el dist); no
es el fallback de Suspense (tiene texto y no aparece); no es un error de transformacion (tsc
pasa y el dev no registra nada); y no hay pageerror.

CORRIGE TRES COSAS: (1) el timeout NO era intermitente, era esta pantalla que no se abre; el
corte aparecia en sitios distintos porque la puerta seguia avanzando. (2) «la curva se pinta»
NO era falso positivo por negarse la app a dibujar: no hay lienzo porque no hay pantalla.
(3) la ficha de producto es un defecto EN LO SERVIDO, no de la prueba.

ABIERTO: por que la app no ejecuta en /compra/productos/:fuente/:idFuente. Siguiente paso:
pedir esa URL con Invoke-WebRequest y mirar el HTML que devuelve el servidor; compararlo con
/compra; y si es el mismo index.html, comprobar que el chunk de Producto esta en /srv/assets.
