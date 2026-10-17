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


=== SEGUNDA MEDIDA: EL SERVIDOR SIRVE LO MISMO, LUEGO ES LA APLICACION ===

Pedido con Invoke-WebRequest a 8080:

  /compra                        status=200  bytes=892  bundle=index-uCotWUV6.js  <div id="raiz">
  /compra/productos/dia/147509   status=200  bytes=892  bundle=index-uCotWUV6.js  <div id="raiz">
  /compra/comparar/526           status=200  bytes=892  bundle=index-uCotWUV6.js  <div id="raiz">

MISMO documento, MISMO bundle, MISMO punto de montaje. Y el punto se llama `raiz`, no `root`
(-- de ahi el `hayRoot: False` del sondeo anterior, que era un error de mi sonda, no del
sitio --).

O sea que:
- NO es el servidor de ficheros: devuelve el mismo index.html en las tres rutas.
- NO es un chunk que falte en /srv/assets: el bundle que se pide es el mismo.
- ES LA APLICACION: arranca, y en esa ruta concreta no pinta nada.

Y se descarta tambien que el arranque falle, porque `/ruta-que-no-existe` SI pinta (79
caracteres): el armazon monta, el router resuelve, y hay una salida para lo que no casa. Lo
que no hay es salida para `/compra/productos/:fuente/:idFuente`.

=== LO QUE QUEDA, Y EL SIGUIENTE PASO EXACTO ===

De `App.tsx` se leyo: `tituloDe` (`:159`) solo calcula el titulo, y el `useEffect` (`:174`)
solo escribe `document.title` y `localStorage`. Ninguno de los dos puede vaciar la pantalla.
El arbol es `<Suspense fallback="Abriendo la pantalla...">` (`:191`) > `CocinaProvider`
(`:192`, diferido) > `Routes` (`:193`). Si `#raiz` queda VACIO, no se pinto ni el fallback.

Los tres siguientes pasos, por orden:
  a) Con el servidor de desarrollo levantado, pedir a mano
     `http://localhost:5173/src/paginas/Producto.tsx` y ver si Vite devuelve el modulo o un
     error de transformacion con su traza. (El log del servidor no lo registro, pero puede
     no haberse pedido nunca ese modulo.)
  b) Comprobar si el chunk de `Producto` esta en el build: `npm run build` lista cada chunk y
     su tamano; si `Producto-*.js` no sale, el `lazy` no resuelve y Suspense se queda
     esperando -- aunque entonces se veria el fallback, y no se ve.
  c) Mirar `Producto.tsx:133` (`if (consulta.isPending) return <Cargando ...>`) y `:144`
     (`if (!producto) { ... }`): si `producto` es `undefined` y ese bloque devuelve `null` en
     algun camino, el armazon SI deberia estar. Que no lo este es lo que no cuadra, y por eso
     (a) y (b) van antes que (c).

