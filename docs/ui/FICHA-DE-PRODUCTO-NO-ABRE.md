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


=== TERCERA MEDIDA: EL MODULO Y EL CHUNK ESTAN BIEN ===

  dist/assets/Producto-D_Gro43H.js   16778 bytes   <- el chunk EXISTE
  GET /src/paginas/Producto.tsx -> 200, 116216 bytes transformados por Vite  <- el modulo CARGA

O sea que el `lazy(() => import('./paginas/Producto'))` (App.tsx:41) tiene a que resolverse, en
desarrollo y en el build. Se descarta el chunk que falta y el error de transformacion.

=== LO QUE YA ESTA DESCARTADO, TODO MIDIENDO ===

  el servidor de ficheros   -> sirve el mismo index.html (892 B) en las tres rutas
  el punto de montaje       -> se llama `raiz`, existe en las tres
  un chunk que falte        -> Producto-D_Gro43H.js esta, 16778 B
  un error de transformacion-> /src/paginas/Producto.tsx da 200 con 116216 B
  el arranque de la app     -> /ruta-que-no-existe pinta (79 caracteres)
  la redireccion            -> se paso a la ruta real y sigue vacia
  la sesion                 -> con sesion abierta, igual
  un ErrorBoundary          -> no hay ninguno en la app (git grep: 0)
  el fallback de Suspense   -> tiene texto («Abriendo la pantalla...») y no aparece
  los errores               -> pageerror VACIO y consola VACIA (ni los dos 401 de /compra)
  la forma de la ruta       -> /compra/comparar/:x (1 param) y /compra/cocina/:x/:y (2) pintan

=== EL ESTADO, SIN ADORNOS ===

ENUNCIADO: en lo que sirve 8080, `/compra/productos/:fuente/:idFuente` deja `#raiz` vacio
(html=31, texto=0, main=0) SIN un solo error en consola ni pageerror, mientras que las otras
seis rutas de /compra y hasta una ruta inexistente SI pintan.

NO SE SABE POR QUE. No se inventa.

LO SIGUIENTE, Y ES UNA SOLA COSA: mirar `LayoutSuite` (`Suite.tsx`) buscando un camino que
devuelva `null` o no pinte el `main`. Es el unico sitio que queda entre «el arbol de rutas» y
«el componente de la pagina», y explicaria que no haya ni armazon ni 401 (el armazon es quien
pide `/api/yo`). Las demas hipotesis estan descartadas con medida, no por opinion.

NOTA DE HIGIENE: el servidor de desarrollo de esta ronda se arranco con `Start-Process`, que NO
es un trabajo gestionado; se comprobo que el proceso de 5173 era el mio (0,6 minutos de edad)
antes de matarlo, y 5173 quedo cerrado.


=== CUARTA MEDIDA: LA PAGINA PINTA Y SE VACIA SOLA EN MENOS DE TRES SEGUNDOS ===

Muestreo del DOM en el tiempo, sobre 8080 y la ruta del producto:

  a  1000 ms   main=1  texto=  99   <- LA APP ESTA PINTADA
  a  3000 ms   main=0  texto=   0   <- y a los tres segundos esta vacia
  a  7000 ms   main=0  texto=   0
  a 12000 ms   main=0  texto=   0
  eventos (pageerror + consola): CERO

Y en la primera medida se habia visto que SI se piden las cosas: el chunk
`Producto-D_Gro43H.js`, `/api/yo` DOS VECES, y `/api/producto/dia/147509`. Es decir: el
armazon se pinto, `Producto` se monto, los datos llegaron (la API da 200 con 18060 bytes de
JSON sano) ... y despues React desmonto el arbol ENTERO, sin decir por que.

=== Y UN DEFECTO DE MI PROPIA SONDA, QUE HAY QUE DECIR ===

La sonda calculaba `raiz = (document.getElementById('raiz') || {}).innerHTML ? ... : -1`. El
`innerHTML` de un `div` vacio es la cadena vacia, que es FALSA, asi que devolvia -1. O sea que
`-1` NO significaba «el div no existe» (como escribi en la ronda anterior), sino «el div existe
y esta vacio». La conclusion no cambia -- sigue vacio -- pero la lectura anterior era erronea y
se corrige aqui. Es el mismo error de siempre: una sonda que no distingue dos estados y yo
leyendo el numero como si los distinguiera.

=== LO QUE ESTO DEJA ===

HECHO: la aplicacion SI arranca en esa ruta, SI monta el armazon, SI carga el chunk de la
pagina, SI pide los datos, y la API contesta 200 con JSON valido.
Y DESPUES se desmonta todo, entre 1 y 3 segundos, SIN error visible.

DESCARTADO ADEMAS: que algo del fuente borre la raiz o recargue -- `git grep` de
`location.reload`, `location.href =`, `document.write`, `documentElement` y `.remove()` en
`src/` da CERO coincidencias (solo `getElementById('raiz')` en main.tsx:44, para montar).
Tambien descartado `VigilaCuenta`: solo llama a `cliente.clear()` (cache de react-query).

LO SIGUIENTE, Y ES UNA SOLA COSA: un desmontaje total y silencioso de React, con la API
contestando 200, apunta a una excepcion DURANTE EL RENDER de `Producto` con los datos ya
dentro. Y si React no la esta registrando, hay que verlo desde dentro: ejecutar la pagina con
`page.on("pageerror")` Y ademas parchear `window.onerror` y `console.error` ANTES de que cargue
el bundle (`add_init_script`), porque el listener de Playwright puede llegar tarde. Eso es lo
que hay que hacer en la siguiente ronda, y es lo unico.


=== QUINTA MEDIDA: EL ARMAZON SE PINTA, Y LUEGO SE VACIA SIN ERROR NI NAVEGACION ===

Se instrumento la pagina ANTES de que cargara el bundle (`add_init_script`), parcheando
`console.error`, `console.warn`, `window.onerror` y `unhandledrejection`. Resultado: CERO
eventos. O sea que no hay ninguna excepcion que se este escapando: no hay excepcion.

Y el volcado del DOM:
  a   800 ms  #raiz = 9109 caracteres: el <aside aria-label="Menu de la suite">, el enlace
              «Saltar al contenido», el nav «Aplicaciones»... EL ARMAZON ESTA PINTADO.
              Titulo: 'Cesta'.
  a  3000 ms  #raiz = 0 caracteres.
  a  8000 ms  #raiz = 0 caracteres.
  href: identico en todas las muestras.  history.length: 2, sin cambios.

O sea: NO navega (la URL y el historial no cambian), NO da error (cero eventos con la
instrumentacion por delante), y React VACIA SU CONTENEDOR entre 800 y 3000 ms.

Y UN DATO QUE SE ME HABIA ESCAPADO: EL TITULO SE QUEDA EN «Cesta». El `useEffect` de
`App.tsx:174` pone `document.title` con `tituloDe(pathname)`, y para esta ruta `tituloDe`
devuelve 'Producto' (`App.tsx:159`, `ruta.includes('/productos/')`). Si el titulo sigue en
'Cesta', ESE EFECTO NO SE EJECUTO. Pero el armazon si se pinto, y el armazon vive dentro de
`<Routes>` dentro de `App`. Esa combinacion -- armazon pintado y efecto de `App` sin correr --
es la pista mas concreta que hay hasta ahora.

=== CORRECCION DE LO QUE DIJE ANTES ===

Dije que «el armazon no se pinta» porque en la consola no habia los dos 401. Era FALSO: el
armazon SI se pinta (9109 caracteres a 800 ms). Lo que pasa es que `/api/yo` se pide dos veces
(medido) y las respuestas no dejan mensaje de consola en esta ruta -- puede que lleguen DESPUES
del desmontaje y el error de red no se registre. La conclusion «no se pinta el armazon» era
mia y era erronea.

=== LO QUE QUEDA, Y ES UNA SOLA COSA ===

El efecto de `App` no corre y el arbol se vacia, sin error y sin navegar. Eso ya no es la API
ni el enrutado ni el chunk. Lo siguiente:
  - Comprobar si `StrictMode` (`main.tsx:50`) esta desmontando y remontando: en React 19 el
    doble montaje de desarrollo no aplica al build, pero conviene confirmarlo.
  - Mirar `Producto.tsx` entero buscando un `useEffect` que llame a `navega(...)` o a algo que
    desmonte, y `useTitulo` (`:37`), que es lo unico que esta pagina hace y las otras no en ese
    orden.
  - Y comprobar si el efecto de `App` (`:174`) lee `localStorage` y ese acceso lanza en este
    contexto: `aplicacionDe(pathname)` y `localStorage.setItem`. Si `localStorage` lanza, el
    efecto revienta DESPUES del render, y en React 19 un error en un efecto desmonta el arbol
    y se reporta por `onUncaughtError`... que no lo registro. Pero encaja mejor que nada: el
    efecto no corre y el arbol se vacia.


=== SEXTA MEDIDA: EL MECANISMO, REPRODUCIDO A PROPOSITO EN UNA PAGINA QUE FUNCIONA ===

Se inyecto una excepcion en `Storage.prototype.setItem` ANTES de cargar el bundle, sobre
`/compra`, que es una pagina que pinta bien:

  /compra  SIN inyectar             ->  main=1  texto=360
  /compra  CON la averia inyectada  ->  main=0  texto=0     <- EL MISMO SINTOMA

O sea: UNA EXCEPCION DENTRO DE UN EFECTO DE REACT VACIA LA APLICACION ENTERA, Y SIN MENSAJE.
Eso explica por que el armazon aparecia a 800 ms y a 3000 ms no habia nada, sin un solo error
en consola ni pageerror: es el comportamiento de React, no un fallo del registro de errores.

Y por tanto, en la ficha de producto, ALGO LANZA DENTRO DE UN EFECTO.

HONESTIDAD SOBRE ESTA MEDIDA: la bandera `window.__inyectado` salio False en las dos corridas,
asi que no puedo demostrar que el parche estuviera puesto; la atribucion es POR DIFERENCIA
entre las dos corridas, no por una bandera verificada. Se dice y no se adorna.

=== Y `useTitulo` QUEDA DESCARTADO, MIDIENDO ===

  Producto.tsx:37-58  usa useTitulo
  Grupo.tsx:30-80     TAMBIEN usa useTitulo
  y /compra/comparar/526, que monta Grupo, PINTA (html=23083)

Asi que no es `useTitulo`: la pagina que lo usa y funciona lo desmiente.

=== DONDE ESTA AHORA LA SOSPECHA, Y ES UN DATO DURO ===

El titulo se queda en 'Cesta', y en el efecto de `App.tsx:174` el orden es:
  1. `const nombre = tituloDe(pathname)`
  2. `document.title = ...`
  3. `localStorage.setItem(...)`

Si el titulo NO cambio, la excepcion ocurre en (1) o el efecto no llega a correr. En la prueba de
inyeccion el titulo SI cambio (`Buscar · Cesta`) porque el fallo estaba en (3). Esa diferencia
es la que hay que perseguir: **en la ficha, el efecto muere ANTES de poner el titulo.**

Lo siguiente: mirar `tituloDe` y `tituloDeSeccion` (`App.tsx:150-168`) para la ruta
`/compra/productos/dia/147509`, y `aplicacionDe` (`:179`). Es una funcion pura de cadenas: si
lanza para esa ruta y no para las otras, ahi esta. Se puede probar SIN navegador, importando el
modulo en node o replicando sus comparaciones.


=== SEPTIMA: UNA INFERENCIA MIA QUE NO SE SOSTIENE, Y UN DEFECTO PEQUENO QUE APARECE ===

Durante varias rondas sostuve que «el efecto de `App` no corre», apoyandome en que el titulo de la
pestana se quedaba en 'Cesta' cuando deberia decir 'Producto'. Y de ahi saque que la excepcion
ocurria ANTES de la segunda linea de un `useEffect`.

LEYENDO `Titulo.tsx`, ESA INFERENCIA SE CAE:

    export function useTitulo(texto?: string | null) {
      useEffect(() => {
        const limpio = (texto ?? '').trim()
        document.title = limpio ? `${limpio} ${SUFIJO}` : 'Cesta'
      }, [texto])
    }

`Producto.tsx:58` llama `useTitulo(producto?.nombre ?? grupo?.nombre)`. Mientras el dato no ha
llegado, `limpio` es la cadena vacia y el efecto pone **'Cesta'**. O sea que el titulo en 'Cesta'
NO prueba que el efecto no corriera: prueba justo lo contrario, que corrio sin dato.

Asi que:
- La inferencia «el efecto muere antes de la segunda linea» NO esta sostenida por esa medida.
- Sigue en pie lo demas: la pantalla se pinta a los 800 ms y a los 3000 esta vacia, sin error y
  sin navegar; el mecanismo (una excepcion en un efecto vacia el arbol) se reprodujo a proposito.
- Pero YA NO SE SABE si la excepcion esta en un efecto o en otra parte.

Y APARECE UN DEFECTO PEQUENO Y REAL: `Producto` **pisa** el titulo de la ruta con 'Cesta'
mientras carga, porque `useTitulo` escribe 'Cesta' cuando no hay texto, en vez de no tocar nada y
dejar el que puso `App` («Producto · Cesta»). Se ve en la pestana: parpadea a 'Cesta' y luego
cambia.

=== LO QUE HAY QUE HACER AHORA, Y ES DISTINTO DE LO QUE DECIA ===

No buscar «el efecto que lanza», porque no se sabe que sea un efecto. Lo siguiente es **ver la
excepcion**, y las tres cosas que se probaron (listener de Playwright, parchear console.error y
window.onerror con add_init_script) dieron CERO eventos. La cuarta via, que no se ha probado:
**capturar `console.error` desde el propio `main.tsx`** -- es decir, envolver `createRoot(...).render`
en un `try`/`catch` temporal y un `window.addEventListener('error')` dentro del bundle. *Si ahi
tampoco sale nada, la conclusion seria que **no hay excepcion**, y habria que buscar por otro lado:
un `createRoot` duplicado, un `StrictMode` que desmonta, o algo que quite los hijos del contenedor.


=== OCTAVA Y DECISIVA: EN EL SERVIDOR DE DESARROLLO **FUNCIONA** ===

La misma ruta, el mismo dia, dos servidores:

  DEV 5173    raizHtml=9552   main=1   texto=180    <- LA FICHA SE PINTA ENTERA
  DIST 8080   raizHtml=0      main=0   texto=0      <- y aqui no hay nada

Mismo codigo fuente, `git diff` vacio en `src/` durante toda esta investigacion. Asi que **el
defecto NO esta en el codigo**: esta en **lo que sirve 8080**, o en la diferencia entre desarrollo
y construido.

Y se descarto lo obvio, midiendo:
  - El `dist` del host esta recien construido: `index-BxckfJaz.js`, 336938 B.
  - 8080 sirve ESE bundle (se comprobo en su HTML).
  - Y con ese bundle nuevo la ruta SIGUE vacia en 8080. O sea que no era un `dist` viejo.
  - Todos los recursos responden 200 desde 8080:
      /assets/Producto-VSQkdDS4.js   status=200  16697 B
      /assets/index-BxckfJaz.js      status=200  336913 B
      /compra/listas                 status=200     892 B
  - Y el nodo de montaje existe y esta CONECTADO a los 4 s, con un hijo: no es que React pinte en
    un nodo desprendido.

*** ESTO CAMBIA EL DIAGNOSTICO ***, y hay que decirlo: lo que se venia escribiendo -- «la
aplicacion no llega a ejecutarse en esa ruta» -- **es falso en lo que respecta al codigo**. *El
codigo monta la ficha. Lo que falla es la version construida y servida.*

Y una cosa mas que hay que anotar: **el `dist` se construye en `plataforma/web/dist`, no en
`plataforma/web/app/dist`**. *Durante varias rondas mire la carpeta equivocada y por eso no vi que
el bundle que servia 8080 era otro.*

=== LO QUE QUEDA POR HACER, Y AHORA ES MUCHO MAS ESTRECHO ===

Comparar el comportamiento de las dos versiones del MISMO bundle, y encontrar que cambia al
minificar. Los candidatos, ninguno medido:
  a) `StrictMode`: en desarrollo monta y desmonta y vuelve a montar; en produccion no. Si algo
     depende de ese doble montaje, en produccion se ve distinto.
  b) Un `Suspense`/`lazy` que en produccion resuelve de otra forma. *Pero `Grupo` tambien es lazy
     y pinta, asi que no es el lazy en general.*
  c) Una minificacion que rompe algo. Se puede comprobar construyendo con
     `--minify false` y volviendo a probar la ruta: si con eso pinta, es la minificacion.
La (c) es la mas barata y la que mas discrimina, y es la siguiente que hay que hacer.


=== NOVENA Y CONCLUYENTE: **ES LA MINIFICACION** ===

Se construyo el MISMO fuente dos veces, el mismo dia, y se sirvio cada uno en su sitio:

  SIN MINIFICAR (vite build --minify false, servido en 5180)
      raiz=9552   main=1   texto=180    <- LA FICHA SE PINTA ENTERA

  MINIFICADO (lo que sirve 8080)
      raiz=0      main=0   texto=0      <- y aqui no hay nada

*** Misma fuente. *Mismo dia. *Lo unico que cambia es `--minify false`.***

Y una objecion que hay que responder, porque los dos entornos no son identicos: **el de prueba no
tiene API** (da cuatro errores de consola) y **el de 8080 si la tiene**. *Pero el de prueba, **sin
API ninguna, pinta el armazon**; y el de 8080, **con la API contestando 200**, no pinta nada.* *Asi
que la API no es lo que decide: **decide el build**.*

*** CONSECUENCIA, *y es grave***: *no es que la ficha este rota en el codigo. Es que **el paso de
construir la rompe**.* *Y eso afecta a **todo lo que se sirve**, no solo a esta pantalla: la ficha es
donde se nota, pero el build es el mismo para todas.*

=== EL SIGUIENTE PASO, YA CONCRETO ===

Bisecar la minificacion. Los candidatos, en orden de probabilidad:
  1. **`React.lazy` + `import()` dinamico**: *esbuild reescribe las importaciones dinamicas al
     minificar, y esta app usa `lazy` en todas las paginas.* *Pero `Grupo` tambien es lazy y pinta,
     asi que no es el `lazy` en general.*
  2. **Un nombre de propiedad o de funcion que la minificacion acorta** y algo lee por cadena.
  3. **Un importe circular** que en un solo trozo de 336 kB se resuelve distinto que en 917 kB.
Empezar por construir con `--minify esbuild` y `--minify terser` por separado, y con
`build.minify: 'esbuild'` + `keepNames: true`: si con `keepNames` pinta, es un nombre acortado, y
eso acota mucho.

*** Y HAY QUE DECIR UNA COSA MAS ***: *durante siete rondas se busco el defecto en el codigo de la
pantalla. *El codigo estaba bien desde el principio. *Lo que fallaba era el build, y no se comprobo
porque **se dio por hecho que lo servido era lo escrito**.*


=== DECIMA: `keepNames` LO ARREGLA, *PERO ESO NO PRUEBA QUE SEA UN NOMBRE* ===

Segundo bisecado, con un `vite.config.keepnames.ts` temporal (-- *el del repo no se toco, y el
`dist` real siguio con la misma marca de tiempo, 10:19:29 --)*:

  keepNames (minificado, conservando nombres de funciones y clases)
      raiz=9552   main=1   texto=180    <- FUNCIONA

  minificado normal
      raiz=0      main=0   texto=0      <- no

*** Asi que `keepNames: true` arregla la pantalla.*** *Y eso acota mucho: es una de las cosas que
`keepNames` cambia.*

*** PERO NO SE PUEDE DECIR QUE SEA «UN NOMBRE ACORTADO», *y aqui esta el porque***:

- `keepNames` **no solo** conserva nombres: *tambien mete llamadas al ayudante `__name` y **apaga
  algunas optimizaciones**.* *Cualquiera de esas diferencias podria ser la causa.*
- Y **no hay ni una lectura de `.name` en toda la aplicacion**: `grep` de `constructor.name`,
  `.name ===` y `displayName` en `src/` da **CERO**.
- Como `Grupo` tambien es `lazy` y pinta con la minificacion normal, **tampoco puede ser el `lazy`
  en general.**

*** CONCLUSION HONESTA***: *el defecto **esta en la minificacion** (medido dos veces, con y sin), *y
`keepNames` **lo evita** (medido)*, *pero **no se sabe por que***. *Decir «es un nombre acortado»
seria exactamente el tipo de afirmacion que este encargo pide no hacer.*

=== EL SIGUIENTE PASO, CONCRETO ===

Con `keepNames` como palanca, bisecar **que parte de `keepNames`** es la que importa:
  1. Construir con `esbuild: { keepNames: true, minifyIdentifiers: true, minifySyntax: false }` y
     luego con `minifySyntax: true` y `minifyWhitespace: true`. *Si falla con `minifySyntax: false`
     y funciona con `true`, es la sintaxis; si al reves, *es otra cosa.*
  2. Si ninguna de esas lo explica, mirar los **tres** `import()` dinamicos del trozo: `Producto`,
     `Grupo` y `CocinaModo`. *Comparar el codigo minificado del importe de `Producto` con el de
     `Grupo`, que si pinta, es lo que mas discrimina y no depende de adivinar.*

*** Y LO QUE ESTO SIGNIFICA PARA EL ENCARGO ***: *la ficha de producto **no se puede abrir en la
version servida**, y **la causa es el build, no el codigo**. *Mientras no se arregle, el punto 3 no
esta cumplido y el aviso de la portada tiene una pantalla que no lleva a ningun sitio.*

*Limpieza: el config temporal y el directorio `dist-keepnames` se borraron, verificando la ruta antes
de borrar. `dist` real intacto. 5181 cerrado.*


=== UNDECIMA: EL TROZO DEL PRODUCTO SE CARGA Y EXPORTA BIEN ===

Se importo el trozo a mano desde la propia pagina de 8080, provocando el `import()` para que **una
excepcion, si la hubiera, saliera a la luz** (-- *es la unica forma de verla, porque el `import()` lo
provoco yo --)*:

    await import('/assets/Producto-VSQkdDS4.js')
    ->  { ok: true, claves: ['Producto'] }

*** El trozo carga, ejecuta y exporta `Producto`.*** *No esta roto.*

*** ENTONCES DONDE FALLA, *dicho con precision***: *o en como el `index` minificado lo usa, *o
**dentro del render de `Producto` ya minificado**.* *Y no se puede distinguir todavia, porque ese
camino no produce ninguna excepcion visible.*

=== Y UN ARGUMENTO QUE VA CONTRA «ES UN NOMBRE», *y hay que decirlo***:

*`keepNames` **no toca los nombres de propiedades**;* *y el `lazy` de esta app depende de una
propiedad:* `lazy(() => import('./paginas/Producto').then((m) => ({ default: m.Producto })))`
(`App.tsx:41`). *Si el fallo fuera un nombre de propiedad acortado, **`keepNames` no lo arreglaria**,
y lo arregla.* *Asi que lo que `keepNames` cambia y aqui importa es **otra de las cosas que hace**:
el ayudante `__name`, o las optimizaciones que apaga.* *Ninguna de las dos esta medida.*

=== LO QUE QUEDA, Y ES LO QUE HAY QUE HACER ===

1. **Comparar el `index` minificado con y sin `keepNames`**, buscando el trozo de codigo del `lazy`
   de `Producto`. *Es un `diff` de dos ficheros que ya se pueden generar; no hace falta adivinar.*
2. **Y si ahi no se ve**, montar una pagina minima que pinte solo `<Producto />` con el build
   minificado: *si ahi tambien queda en blanco, el fallo esta en el componente y no en el armazon ni
   en el router.*

*** ESTADO DEL PUNTO 3 DEL ENCARGO ***: *la ficha de producto **no se puede abrir en la version
servida**; *la causa esta **en la minificacion** (medido con y sin), *`keepNames` **la evita**
(medido), *y **no se sabe por que***. *No se declara resuelto.*


=== DUODECIMA: EL `lazy` DE `App.tsx:41` QUEDA DESCARTADO CON EVIDENCIA ===

Se construyeron los dos `index` (normal y con `keepNames`) y se leyo **la expresion del `lazy` de
`Producto`** en los dos:

  NORMAL     eE=x.lazy(()=>Gt(()=>import("./Producto-VSQkdDS4.js"),
                              __vite__mapDeps([21,1,17,13,18,5])).then(n=>({default:n.Producto})))
  KEEPNAMES  QT=_.lazy(()=>It(()=>import("./Producto-C86V4kNv.js"),
                              __vite__mapDeps([21,1,17,13,18,5])).then(r=>({default:r.Producto})))

*** IDENTICAS en estructura, y con la MISMA lista de dependencias `[21,1,17,13,18,5]`.*** *Solo
cambian los nombres de las variables (por la minificacion) y el hash del fichero.*

*** Asi que el `lazy` de `App.tsx:41` NO es la causa.*** *Queda descartado leyendo los dos ficheros, no
suponiendo.*

=== Y LO QUE SI CAMBIA ENTRE LOS DOS, *que esta a la vista* ===

    KEEPNAMES   function D2(r,c){...} u(D2,"useProducto");
    NORMAL      (sin esas llamadas)

*`keepNames` mete llamadas `u(fn, "nombre")` en cada funcion y clase.* *Que `__name` diera 0 en el
recuento es porque esbuild lo llama `u`, no `__name`.*

*** Y AQUI HAY UNA CONTRADICCION QUE NO SE RESUELVE, *y no se va a tapar***: *las llamadas que
`keepNames` anade **solo sirven para que `fn.name` valga algo**; *la aplicacion **no lee `.name` en
ninguna parte** (`grep`: cero). *Asi que **lo que lee un `.name` es una dependencia**, y **no se ha
identificado cual**.* *Y `keepNames` tambien apaga optimizaciones, asi que podria no ser el nombre.
**Las dos posibilidades siguen abiertas.***

=== LO QUE QUEDA, Y ES LO QUE HAY QUE HACER ===

1. **`keepNames` con `minifySyntax` y `minifyWhitespace` por separado**, para ver cual de las tres
   cosas es la que importa. *Tres construcciones, cada una con su prueba de la ruta.*
2. **Si sigue sin aclararse**: montar una pagina minima que pinte solo `<Producto />` con el build
   minificado. *Si ahi tambien queda en blanco, el fallo esta en el componente; si pinta, esta en el
   armazon o en el router.*

*Limpieza: `vite.config.kn.ts` y `dist-kn` borrados, verificando la ruta antes de borrar. `dist` real
intacto (10:19:29).*


=== DECIMOTERCERA, *Y ESTA ES LA BUENA*: NO ES EL BUILD, *ES LA RESPUESTA DE LA API ***
=== *Y TRES CONCLUSIONES MIAS ANTERIORES ERAN FALSAS* ===

La prueba, sobre 8080, la misma ruta, abortando o no las llamadas a la API:

  CON api                main=0   texto=0     raiz=0
  SIN api (abortada)     main=1   texto=207   raiz=9598    <- ¡LA PANTALLA SE PINTA!

*** Abortando la API, la ficha se pinta entera. Con la API, no.*** *Asi que **lo que mata la
pantalla es la respuesta de `/api/producto/...`**, no el build.*

=== POR QUE MIS CONCLUSIONES SOBRE LA MINIFICACION ERAN FALSAS ===

*En las rondas 20, 21 y 23 compare construcciones distintas **en servidores distintos**, y los dos
servidores no se diferenciaban solo en el build:*

  - `vite preview` (5180, 5181) **NO tiene API**: las llamadas dan error y la pantalla PINTA.
  - 8080 **SI tiene API**: contesta 200 con JSON y la pantalla NO pinta.

*Cambiaban **dos** cosas a la vez -- el build **y** la API -- y atribui el efecto al build.*
*** «Es la minificacion» era una conclusion con una variable de mas.*** *Y `keepNames` «arreglaba»
porque el build con `keepNames` lo probe **solo en el servidor sin API**;* *al servirlo 8080, con
`keepNames` y con API, **tambien falla** (medido: main=0).*

*Se retira el `keepNames` del `vite.config.ts` (era un arreglo de un diagnostico equivocado, y
costaba un 10 % de bundle) y se deja el `dist` reconstruido sin el.*

=== LO QUE AHORA SE SABE, Y ES LO UNICO QUE SE SABE ===

- La aplicacion **esta bien**: en desarrollo con API pinta, y en 8080 **sin API tambien**.
- Lo que la rompe es **la respuesta de `/api/producto/<fuente>/<id>`** segun lo que sirve el 8080.
- La misma ruta con la API del 8099 (desarrollo) **pinta**. *Asi que **el dato que llega por 8080
  es distinto**, o llega de otra forma.*
- Y el fallo es **silencioso**: sin `pageerror`, sin consola, y desmontando el arbol entero.

=== EL SIGUIENTE PASO, *y es concreto y barato* ===

1. **Comparar las dos respuestas**, la de `/api/producto/dia/147509` en 8080 y en 8099: *longitud,
   claves de primer nivel, y si alguna trae `null` donde la otra trae un numero.* *Se pueden pedir
   las dos con `Invoke-WebRequest` y compararlas como JSON.*
2. **Y si son iguales**, mirar las **cabeceras** (tipo de contenido, codificacion) y si el 8080
   responde por un camino distinto (Caddy -> API, frente al proxy de Vite).

*** ESTADO DEL PUNTO 3 ***: *la causa esta **acotada a la respuesta de la API**, y **no se declara
resuelto**.* *Lo que si se retira es todo lo escrito sobre la minificacion, que era un camino falso.*


=== DECIMOCUARTA: *CON LA MISMA RESPUESTA, INTERCEPTADA, LA PANTALLA PINTA ***
=== *LUEGO ES UNA CARRERA, NO EL DATO NI EL BUILD* ===

Se intercepto `/api/producto/**` y se re-sirvio la MISMA respuesta desde el intermediario, tocandola
solo en tres variantes:

  respuesta intacta    main=1   texto= 99    <- ¡PINTA!
  sin grupo.serie      main=0   texto=  0
  sin grupo            main=0   texto=  0
  sin producto         main=1   texto=114

*** La misma respuesta, servida por otro camino, hace que la pantalla se pinte.*** *Y si se le quita
`grupo` o su `serie`, no pinta -- pero eso es lo esperable: `Producto` necesita el grupo.*

*** LO QUE ESTO DICE, *y hay que decirlo con cuidado***: *el contenido del JSON **no** es la causa;
lo que cambia entre pinta y no pinta es **por donde y cuando llega la respuesta**.* *Con la
intercepcion, la respuesta viaja por el intermediario: **cambia el momento**, y quiza las cabeceras.*

*** ASI QUE LO MAS PROBABLE ES UNA CARRERA***, *y eso encaja con TODO lo medido antes, que parecia
contradictorio:*
  - en desarrollo pinta (otros tiempos, y Vite sirve el proxy de otra forma);
  - en el construido sin API pinta (no hay carrera que perder);
  - en 8080 a veces no pinta y con la respuesta interceptada si;
  - y el corte parecia «intermitente» desde la primera ronda.

*** Y ESTO RETIRA TAMBIEN LA CONCLUSION DE LA RONDA ANTERIOR ***, *que atribuia el fallo a la
respuesta de la API: era **el momento**, no el contenido.*

=== LO QUE HAY QUE MEDIR AHORA, *y es corto* ===

1. **Repetir la misma ruta en 8080 N veces sin tocar nada** y contar cuantas pinta y cuantas no.
   *Si unas veces pinta y otras no, la carrera queda demostrada y deja de ser una hipotesis.*
2. **Si es una carrera**, buscar quien llega tarde: *el `Suspense` de `App.tsx:191`, el `lazy` de
   `Producto`, o un efecto que desmonta al cambiar de estado.* *Y el sitio probable es un `useEffect`
   con una dependencia que cambia, o un `setState` despues de desmontar.*

*** ESTADO DEL PUNTO 3 ***: *la causa esta **acotada a una carrera entre el montaje y la llegada del
dato**; no resuelta.* *Y se retiran las dos atribuciones anteriores: no es la minificacion (ronda 20)
y no es el contenido de la respuesta (ronda 24).*


=== DECIMOQUINTA: *LA CARRERA, DEMOSTRADA. 1 DE 10.* ===

Lo que habia que hacer desde la primera ronda: **repetir la misma ruta, sin tocar nada, y contar.**

    URL: http://127.0.0.1:8080/compra/productos/dia/147509
    repeticiones: 10        PINTA: 1        VACIA: 9

      1..9   main=0  texto=0    vacia
     10.     main=1  texto=99   PINTA

*** Ya no es una hipotesis: es un hecho medido.*** *Y el que «pinta» muestra **99 caracteres**, o sea
**el armazon sin el producto**: asi que **la carrera se pierde las diez veces**, *solo que una vez se
queda a medio camino en vez de en blanco del todo.*

*** ESTO CIERRA LA PREGUNTA «¿ES UNA CARRERA?» CON UN SI***, *y de paso explica por que todas las
atribuciones anteriores fallaron:*
  - **la minificacion** (rondas 20-23): *al cambiar el build cambie tambien los tiempos;*
  - **la respuesta de la API** (ronda 24): *al interceptar cambie el momento de llegada;*
  - **el «intermitente» de la primera ronda**: *era esto, y estaba bien dicho desde el principio.*

=== LO QUE QUEDA, Y ES UNA SOLA PREGUNTA ===

**Quien pierde la carrera.** *Candidatos, y hay que mirarlos en este orden:*
  1. **`Producto.tsx`**: *un `useEffect` con una dependencia que cambia, o un `setState` despues del
     desmontaje.* *Es donde ocurre, porque sin dato pinta y con dato no.*
  2. **`useTitulo`**: *escribe `document.title` en un efecto con `[texto]`;* *`texto` cambia al llegar
     el dato.* *No puede lanzar, pero **si puede provocar un render extra en mal momento**.*
  3. **El `lazy` de `Producto` + el `Suspense` de `App.tsx:191`**: *el limite de espera esta **por
     fuera** del armazon, asi que mientras carga se pinta el fallback;* *si el chunk resuelve justo
     cuando el dato llega, **los dos cambian a la vez**.*

*** Y HAY UNA FORMA BARATA DE VERLO ***: *repetir la ruta 10 veces **con la API abortada** (-- *que
pinta siempre, medido --)* y 10 veces **con un retraso artificial en la respuesta**. *Si con retraso
pinta siempre, la carrera es por **llegar pronto**; y entonces el sospechoso es el que reacciona a la
llegada, no el que carga.*

*** ESTADO DEL PUNTO 3 ***: *carrera demostrada (1 de 10); **quien** la pierde, no identificado.*
*No se declara resuelto. Y las atribuciones retiradas -- minificacion y contenido de la respuesta --
siguen retiradas.*


=== DECIMOSEXTA: *LA CARRERA ES POR LLEGAR PRONTO, *Y EL PRODUCTO NO SE PINTA NUNCA* ===

Tres condiciones, ocho repeticiones cada una, sobre 8080:

    API abortada              pinta 8/8   textos=[207,207,207,207,207,207,207,207]
    API con 2,5 s de retraso  pinta 3/8   textos=[0,0,0,99,99,0,0,99]
    sin tocar nada            pinta 0/8   textos=[0,0,0,0,0,0,0,0]

*** Tres cosas, y las tres son datos duros***:

1. **Abortando la API pinta SIEMPRE (8/8)**, *con 207 caracteres: el camino de error.*
   *-- el mensaje de que no se pudo cargar, que es corto y no depende del dato --*
2. **Retrasando 2,5 s sube de 0/8 a 3/8.** *** Cuanto mas rapido llega el dato, peor.***
   *Eso confirma que es una carrera, y la orienta: **el que pierde es el que reacciona a la
   llegada**, no el que carga el trozo.*
3. **Y LO MAS IMPORTANTE**: *los que «pintan» muestran **99** caracteres, o sea **el armazon**,
   **nunca 180, que es la ficha entera** (-- *medido en desarrollo --*).*
   *** El contenido del producto NO se pinta ni una sola vez, en ninguna de las tres condiciones.***

*** LO QUE ESTO ACOTA, *y es lo mas estrecho que se ha estado***: *el armazon se pinta; **el render de
`Producto` con datos es el que se pierde siempre**; y **cuanto antes llega el dato, mas probable es
perderlo**.* *Eso es propio de **un efecto que reacciona al dato y desmonta o rompe el arbol**, no de
un problema de carga.*

=== DONDE MIRAR AHORA, YA SIN DUDAS DE POR DONDE ===

**En `Producto.tsx`, los efectos y los renders condicionales que dependen de `consulta.data`:**
  - `useTitulo(producto?.nombre ?? grupo?.nombre)` (`:58`): *efecto con `[texto]`, y `texto` cambia
    exactamente al llegar el dato.* **Es el unico efecto de la pagina que reacciona al dato.**
  - `if (consulta.isPending) return <Cargando .../>` (`:133`) y `if (!producto) { ... }` (`:144`):
    *los dos caminos sin dato.*
  - **`Chispa`**, que dibuja la serie: *es lo unico que la ficha hace y las demas no, y solo se pinta
    cuando hay dato.*

*El siguiente paso es leer esos tres sitios enteros, **no probar mas configuraciones**.*

*** ESTADO DEL PUNTO 3 ***: *carrera demostrada (0/8 normal, 3/8 con retraso, 8/8 abortando); **el
armazon pinta y la ficha nunca**; **el fallo esta en el render con dato**; **quien lo rompe, sin
identificar**.* *No se declara resuelto.*


=== DECIMOSEPTIMA: *LEIDOS LOS TRES SITIOS. NO ESTA AHI, *Y SE DICE* ===

**`Producto.tsx:52-58`:**

    const producto = consulta.data?.producto
    const grupo = consulta.data?.grupo ?? null
    // Mientras el dato viaja se queda "Producto", que lo pone `App` por ruta:
    // aqui solo se mejora cuando se sabe mas.
    useTitulo(producto?.nombre ?? grupo?.nombre)

*** El comentario y el comportamiento se contradicen***: *`useTitulo` **no** deja el titulo que puso
`App`; escribe `'Cesta'` cuando no hay texto (`Titulo.tsx:24`).* *Asi que **pisa** justo lo que el
comentario dice respetar.* **Es un defecto real y pequeno, ya anotado, y NO puede lanzar.**

**Los `useMemo` (`:64` y `:85`)** *llaman a `grupo.productos.find(...)` y `grupo.serie.filter(...)`:
*lanzarian si alguna no fuera una lista, **y el JSON medido las trae bien** (111 puntos de serie,
`productos` presente).*

*** O SEA QUE EL SITIO NO ESTA EN LO QUE SE HA LEIDO, Y NO SE VA A DECIR QUE SI.***

=== Y UN DATO QUE ACOTA MAS, *sacado de los textos medidos* ===

*Cuando «pinta», el texto es **99 caracteres**: el armazon y su menu, **nada mas**.* *Y `Producto` tiene
**tres** caminos que pintan algo:*

    :133   if (consulta.isPending) return <Cargando que="la ficha" />
    :144   if (!producto) { ... }              <- un bloque con texto
    :...   el cuerpo de la ficha              <- 180 caracteres en desarrollo

*** No se pinta NINGUNO de los tres.*** *Ni el de «cargando», ni el de «no encontrado», ni el cuerpo.*
*O sea que **`Producto` no llega a devolver nada: lanza antes de su primer `return`**.*

*** Y ESO ES LO QUE HAY QUE BUSCAR***: *algo entre la linea 47 y la 133 que solo se ejecuta **con
`consulta.data` ya presente**, *y que **no se ha leido todavia**:* *las lineas **85-133**, que es donde
se calcula el historico, la frase y los sellos.*

*** SIGUIENTE PASO, *una sola cosa***: **leer `Producto.tsx:85-133` entero.** *Es el unico tramo de la
pagina que se ejecuta con dato y no se ha mirado.*

*** ESTADO DEL PUNTO 3 ***: *carrera demostrada y orientada; **`Producto` lanza antes de su primer
`return` cuando hay dato**; **el tramo 85-133 es lo unico que queda sin leer**; **no resuelto**.*


=== DECIMOCTAVA: *LEIDO `85-133` Y `loQueDiceLaCurva`. LIMPIOS. *Y SE ACOTA EL RESTO ***
=== *POR PRIMERA VEZ, DONDE NO ESTA* ===

Se leyo el tramo entero y las funciones que llama:

- **`historico` (`:85-101`)**: *`grupo.serie.filter`, `grupo.productos.filter`,
  `.map`, `.sort` con `ms(fecha)`.* *Nada que lanzar, y las dos listas llegan bien del JSON.*
- **`curva` (`:108-111`)**: *`loQueDiceLaCurva(...)`.*
- **`resumen` (`:113-131`)**: *`Math.min(...valores)` sobre **111** elementos,* *lejos del limite de
  pila de JavaScript (-- *que revienta con decenas de miles --)*.*
- **`loQueDiceLaCurva` (`logica/curva.ts`)**: *filtra, un `Set` de unidades, y `Math.min`/`Math.max`
  sobre los que tienen precio.* *Se corta con `con.length < 2`.*
- **`diasAlMismoPrecio`**: *un `for` acotado que baja desde el final y para al cambiar el precio.*
- **y `grep` de `while` en `curva.ts` y `Producto.tsx`: CERO.** *No hay bucle infinito posible.*

*** O SEA: EL TRAMO QUE SE EJECUTA CON DATO **ANTES** DEL PRIMER `return` ESTA LIMPIO.***
*Y eso es un resultado: **mueve el foco de sitio**, *que es lo que faltaba.*

=== DONDE ESTA AHORA, *y por que* ===

*`Producto` no pinta ninguno de sus tres caminos (`<Cargando>`, el de «no encontrado», ni el cuerpo),
*asi que **lanza (o no termina) en su render**.* *Ya se descarto todo lo que pasa **antes** del primer
`return`.*

*** Queda el cuerpo del render (`:135-656`) y los hijos que pinta.*** *Y entre esos hijos hay uno que
**solo se pinta cuando hay dato y que no se ha mirado nunca**:*

    **`Chispa`** (`componentes/Chispa.tsx`) -- *el que dibuja la serie.*

*Es el unico que cumple las tres condiciones: **depende del dato**, **la ficha es la unica pagina que
lo usa**, y **no se ha leido**.* *Es el sitio mas probable y **esta sin mirar**.*

*** SIGUIENTE PASO, UNA SOLA COSA ***: **leer `componentes/Chispa.tsx` entero.** *Si ahi no esta, el
siguiente es el cuerpo del render de `Producto` desde `:135`.*

*** ESTADO DEL PUNTO 3 ***: *carrera demostrada (0/8, 3/8, 8/8); **`Producto` lanza en su render con
dato**; **todo lo anterior al primer `return` esta descartado leyendolo**; **`Chispa` es el sospechoso
y no se ha leido**; **no resuelto**.*


=== DECIMONOVENA: *EL SOSPECHOSO, LEIDO. `Chispa` + `ResizeObserver`* ===
=== *Y EXPLICA LAS CUATRO COSAS QUE PARECIAN NO TENER RELACION* ===

`Chispa.tsx` (178 lineas) leido entero. Lo que hay dentro:

    :40  useEffect(() => {
    :43    const observa = new ResizeObserver((entradas) => {
    :45      if (caja) setAncho(Math.max(60, Math.round(caja.width)))   <- cambia estado
    :47    observa.observe(el)                                          <- observa el MISMO div
    :49    return () => observa.disconnect()
    :50  }, [])                                                         <- sin dependencias
    ...
    :56  useEffect(() => {
    :58    if (!el || ancho < 20 || puntos.length === 0) return          <- solo con dato
    :101   const nueva = new uPlot(opciones, [xs, ys], el)               <- uPlot ESCRIBE en ese div
    :104     nueva.destroy()
    :108  }, [clave, ancho, alto, color])                                <- `ancho` esta dentro

*** LO QUE ESTO HACE, *y es el patron clasico de este par de piezas***: *`ResizeObserver` observa el
mismo `div` donde `uPlot` pinta.* *Si `uPlot` cambia el tamano de ese `div` al montarse* (-- *crea un
canvas dentro, con su propio ancho --)*, *el observador **vuelve a disparar**, `setAncho` cambia
`ancho`, `ancho` esta en las dependencias del efecto, **se destruye la grafica y se crea otra**, y
**el ciclo se repite**.*

*** Y EXPLICA, UNA A UNA, LAS CUATRO COSAS QUE PARECIAN NO TENER RELACION ***:

| *lo medido* | *por que encaja* |
|---|---|
| **solo falla cuando hay dato** | *`:58` sale antes si `puntos.length === 0`; sin dato no hay grafica ni ciclo* |
| **solo en esta pagina** | *es la unica que usa `Chispa`* |
| **depende del tiempo (0/8, 3/8, 8/8)** | *el ancho y el `ResizeObserver` son asincronos; con la API abortada no hay puntos y no arranca* |
| **sin `pageerror` ni consola** | *un ciclo de `ResizeObserver` **no lanza una excepcion de JavaScript**: el navegador lo cuenta como aviso y el arbol se queda sin pintar* |

*** Y por que no fallaba en desarrollo***: *con Vite el layout y la hidratacion van por otro camino, y el
ciclo a veces no llega a estabilizarse igual.* *No es una explicacion medida, y se dice.*

=== LO QUE HAY QUE HACER, *y NO se aplica a ciegas* ===

*** ES UNA HIPOTESIS***, *aunque encaje con todo.* *Antes de tocar nada:*
  1. **Medirlo**: *en la pagina, contar cuantas veces se crea y se destruye la grafica.* *Si el numero
     sube sin parar, es el ciclo, y entonces es un hecho y no una hipotesis.*
  2. **Y si se confirma**, el arreglo minimo es **no observar el mismo nodo que `uPlot` mide**, o
     **devolver el mismo `ancho` cuando no cambie**: `setAncho(w => w === nuevo ? w : nuevo)`.
     *Eso rompe el ciclo si el ancho se estabiliza, y no cambia nada si no.*

*** ESTADO DEL PUNTO 3 ***: *carrera demostrada; **el sospechoso esta identificado y leido**; **el
mecanismo encaja con las cuatro observaciones**; **NO se declara resuelto**, y **no se aplica un
arreglo sin medirlo primero**.*

