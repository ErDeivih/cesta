# SUPERAPP · Estado del trabajo

## Revisión posterior — 8 de octubre de 2026

Leer [la revisión del código y correcciones](SUPERAPP-REVISION-2026-10-08.md)
antes de continuar desde `a32957e`. Se corrigieron subtotales independientes
por nutriente, ausencia frente a cero en el rango, números no finitos y el
mensaje que equiparaba entradas registradas con toda la ingesta del día.
Las correcciones permanecen en el árbol de trabajo, sin commit de esta revisión.

Prioridades detectadas: routers de Recetas/Diario sin sesión ni propietario;
referencia de identidad por cadena en lugar de referencia solicitada;
alternativas que siguen entrando en costes; candidato seleccionado antes de
evaluar la promoción por cantidad. Estos hallazgos impiden considerar S07–S09
terminados y deben resolverse antes del ensayo multiusuario o de activar identidad.
Las pantallas propias ya construidas se conservan. La verificación de esta
revisión se registra en SUPERAPP-REVISION-2026-10-08, sin reutilizar cifras previas.

Verificación posterior ejecutada: **1.318 pruebas aprobadas**, ruff limpio,
build frontend correcto y seis pruebas de cocina aprobadas. Persisten dos
avisos de dependencias y el aviso de tamaño del paquete frontend. No se
ejecutó el ensayo de navegador ni se probaron cuentas contra las bases reales.

Encargo vigente: `docs/SUPERAPP-00-EMPEZAR-AQUI.md` (7 de octubre de 2026), con
`SUPERAPP-01` (diseño y producto), `SUPERAPP-02` (datos, Lidl e identidad) y `SUPERAPP-03`
(investigación y límites). Este fichero es el estado vivo: se actualiza **antes de cada pausa**
y es lo primero que hay que leer al retomar.

Reglas de lectura de este fichero: **terminado** = cumple su criterio de aceptación con evidencia ·
**verificado** = se ejecutó y pasó, pero no cubre todo el paquete · **pendiente** = no empezado.
No se mezclan las tres.

---

## Bitácora de la sesión SUPERAPP (commits, con lo que hizo cada uno)

| commit | qué dejó |
|---|---|
| `e50f04c` | **S00**: baseline congelado. Los cambios heredados se verifican y se preservan; 1.195 pruebas |
| `5b66bf2` | Fichero de estado vivo: plan S00–S12, decisiones cerradas, correcciones a las referencias de Stitch |
| `dcde817` | **S01**: publicación por versiones (carpeta por versión, puntero atómico, `rutas()` fija la versión por petición, rollback) + catálogo actual adoptado como primera versión |
| `247a9cc` | **S02 núcleo**: cola de fichas en SQLite (estados, *lease* con vencimiento, hash, evidencia, reenganche sin duplicar) |
| `9f06396` | **S02 medido**: inventario de 74.861 fichas desde bronze en 75,7 s (antes: sin terminar) |
| `6bfdfd1` y `fb4dc6a` | **S02 instrumento**: informe de cobertura por fuente con deuda de cola y edades |
| `240bad4` | **S03 primera mitad**: descubridor de Lidl (sitemap guardado, clasificación por *slug*, sin red) |
| `42683e7` | La «cuna» suelta fuera de la política: tercera vez que la trampa de las tildes mordía; queda cubierta por pruebas |
| `edb4d2d` | **S03 medido**: el sitemap real, 6.622 direcciones → 691 incluidas, 1.568 de bazar evitadas, 4.363 a revisión |
| `e09f5d3` | **Puente S03→S02**: lo descubierto entra en la cola con su evidencia; el bazar no genera trabajo |

**Lo que la puerta ha parado**: seis commits que habrían metido una regresión o una prueba mal
escrita. La práctica es: las pruebas corren **antes** del commit y si no pasan, no se commitea.

## Resumen vigente (15 de octubre de 2026) · los tres casos de coste, cerrados en los cinco sitios

**El dueño reprodujo tres fallos** y los dejo escritos en `docs/SUPERAPP-REVISION-COSTES-2026-10-08.md`, con
orden de cerrarlos **antes** de las graficas. Los tres estan corregidos, **cada uno con prueba de comportamiento
vista roja antes**, y —esto es lo que costo mas— **en los cinco sitios donde el proyecto suma dinero**.

| caso | era | quedo | commits |
|---|---|---|---|
| **1. seleccion conjunta, cobro separado** | la promocion se aplicaba **por linea** y luego se sumaban los costes ya separados: un 3x2 daba **200** en una linea de tres y **300** en dos de una y dos | **agrupar** por producto efectivo + tienda (solo lo autorizado), aplicar la promocion **una vez** sobre el grupo, y **repartir** conservando la suma exacta. Redondeo escrito: parte entera, y el resto **de uno en uno** a mayor fraccion, a igualdad la que va antes | `066089d`, `4901dda`, `74a6db0`, `a90d7a2` |
| **2. autorizacion de B aplicada a A** | `_es_la_confirmada` validaba B, pero la eleccion se construia con `hallado` (el canonico A): `confirmado=dia:B; elegido=dia:A; coste=200` | la **eleccion efectiva** se decide **antes** de cobrar: con sustitucion confirmada, lo devuelto y cobrado es **la alternativa** —su producto, su nombre, **su precio y su oferta**— y `autorizada` sale de esa misma decision | `066089d` |
| **3. referencias distintas dentro del mismo grupo** | `pedido[grupo] = producto_id` se pisaba entre lineas y las cantidades se sumaban por grupo | llave **por linea** cuando se pide un articulo concreto, **gana el pedido** si esta entre las filas con precio, y si **no esta el motor se abstiene** — el canonico no sustituye su identidad | `066089d` |

### Los cinco sitios que suman dinero

Aqui esta lo que mas tiempo llevo, y por una razon que conviene no repetir: **el arreglo valia donde lo probaba y
faltaba donde no miraba**. Fueron apareciendo de uno en uno.

| donde | que hace | commit |
|---|---|---|
| `donde_comprar` | el total por tienda | `066089d` |
| `estimacion` | el numero de la lista | `4901dda` |
| `coste_por_linea` | lo que se **guarda** al cerrar (y la parte repartida de cada linea) | `64a7c03`, `74a6db0` |
| **el cierre** (`almacen.py`) | **la caja**: el total que se cuenta. Escribia `unitario x cantidad` por linea, **sin ofertas** | `74a6db0` |
| `reparto_por_tienda` | el reparto entre tiendas — su docstring **ya prometia** «con las ofertas aplicadas» y no las aplicaba | `a90d7a2` |

**La leccion, para el proximo cambio de precio:** lo primero no es arreglar el sitio que tienes delante, es
**contar cuantos sitios calculan un precio**. Aqui eran cinco, y los encontre de uno en uno a lo largo de seis
rondas.

### Dos regresiones mias, cazadas por pruebas que escribi para eso

- La llave nueva dejo **lineas con producto concreto mostrandose «sin precio»** en la lista y **guardandose sin
  precio** al cerrar: silencioso, en pantalla y en el registro. Lo cazaron las pruebas de `estimacion` y de
  `coste_por_linea` (`4901dda`, `64a7c03`).
- Un **reemplazo global** de `(1, "dia")` en cinco ficheros de prueba rompio diez pruebas, porque en varios esa
  forma no era la llave. **Revertido**, y sustituido por arreglos leidos fichero a fichero.

**Y los dobles de diez pruebas dejaron de estar en paso** con la llave nueva: un doble no debe componer la llave a
mano, sino llamar a `_llave_candidato`. Es la **tercera** vez en la sesion que esa leccion muerde.

### Cuatro piezas mas, despues de escribir esto

| que | por que | commit |
|---|---|---|
| **La oferta no se aplica a cantidades pendientes de autorizacion** | la condicion del dueno estaba a medias: primero no entraban en el grupo, pero una linea **sola** seguia cobrando su 3x2. Ni agrupada ni sola: precio de catalogo | `ba46c28` |
| **Revocacion y desaparicion de B** | los dos casos que la revision pedia y no estaban cubiertos: una confirmacion revocada deja de contar, y si B no esta queda **pendiente** sin sustituir por A | `794d922` |
| **Los puentes en la cuenta de la lista** | las lineas del plan y de consumir **no tienen producto**: no tienen precio (se dice) y **no entran en ningun grupo de compra**, asi que no se llevan la oferta de otra | `da4afc6` |
| **El estado de la eleccion** | la revision pedia *«definir el estado de eleccion y reflejarlo en la respuesta y en la pantalla»*: con la sustitucion confirmada, `identidad` dice **`confirmada`**, y como es el campo que la pantalla ya enseña, llega alli sin tocar ninguna pantalla | `be602a1` |

**Dos de esas pruebas pasaron a la primera** (revocacion, puentes) y **una necesito dos pasos** (la autorizacion:
el grupo no bastaba). Se dice cual es cual: una prueba que no vio un rojo **fija** comportamiento, no lo caza.

### Y las ultimas piezas, con una comprobacion que no encontro nada (y por eso vale)

| que | por que | commit |
|---|---|---|
| **La cuenta de la caja, en una funcion con nombre** | `_lo_que_se_paga(cent, parte, cantidad)`: la parte repartida manda, sin parte se calcula unitario x cantidad, y **sin precio devuelve None** -- un cero afirmaria que salio gratis. Estaba dentro del cierre, sin prueba posible sin PostgreSQL, y era donde vivia el fallo | `edcc001` |
| **El ensayo, con la invariante del coste** | el ensayo pasaba **sin mirar el coste**: una firma en blanco. Ahora comprueba que lo guardado no cueste mas que la suma de sus unitarios, y **dice si hubo oferta** -- para que un pase trivial no se lea como verificacion | `3ccad84` |
| **El cliente no calcula dinero** | se busco el sexto sitio donde pudiera romperse la regla: `formato.ts` tiene `euros()` y `eurosUnidad()`, que **formatean** (`cent / 100`), y no hay ni un `reduce` ni una multiplicacion de precios. **Los cinco sitios que suman son todos del servidor** | -- |

**`ruff` volvio a ganarse su sitio:** al sacar la cuenta de la caja deje `cent` sin definir y el cierre habria
reventado en ejecucion. La suite **no lo vio** (esa linea solo corre contra PostgreSQL) y el lint si:
`F821 Undefined name cent`. Es la misma clase de fallo que puso la puerta del lint en este proyecto.

### Por que este objetivo se detiene aqui, y que significa

El objetivo de coste tiene un **tope de 140 rondas** y se agoto: **se detiene por su propio limite, no por haber
terminado**. Conviene que quien siga lo sepa, porque el estado no es «hecho» ni «abandonado»:

- **El trabajo de codigo esta cerrado y probado**: los tres casos, los cinco sitios que suman dinero, la
  autorizacion en la lista, la revocacion, los puentes, el estado de la eleccion, la cuenta de la caja con prueba
  y el ensayo con la invariante del coste. Catorce commits, `066089d` a `62683ca`, con `ruff` limpio y la suite en
  verde en cada uno.
- **Lo que falta necesita el motor de Docker**, caido desde la ronda 111 sin responder
  (`dockerDesktopLinuxEngine`: el *pipe* no existe). Son tres cosas, las tres escritas y listas: el **ensayo**
  (con la invariante del coste dentro), la **restauracion** en entorno separado y la **publicacion** con la
  imagen servida.
- **Y despues**: las graficas (medida, cobertura y universo) y los recorridos de las tres aplicaciones.

**Ninguna condicion se declara cerrada.** La regla del dueno lo impide -- *no cerrar identidad y coste con pruebas
de seleccion o persistencia aisladas* -- y el cierre real contra PostgreSQL **no lo ha ejecutado nadie**. Eso es
exactamente lo que hay: codigo terminado y probado hasta donde el entorno ha dejado, y una verificacion esperando
a que el motor vuelva.

### Lo que queda

1. **El ensayo y la restauracion**, con los contratos nuevos. **Bloqueado por el entorno**: Docker no responde
   (`dockerDesktopLinuxEngine` no existe), y no se puede fingir. Es lo unico que puede decir si el cierre cuadra
   contra PostgreSQL de verdad — y por eso **la condicion sigue ABIERTA**: todo lo de arriba esta probado con
   dobles, que es lo que ha permitido trabajar sin motor.
2. **La publicacion y la imagen servida**, cuando el motor vuelva.
3. **Las graficas** (medida, cobertura y universo) y **los recorridos** de las tres aplicaciones.

**No se declara cerrada ninguna condicion.** Suite en verde y `ruff` limpio en cada commit; nada desplegado.

## Resumen vigente (14 de octubre de 2026) · los cuatro defectos, cerrados y probados

**Los cuatro defectos que impedían cerrar identidad y coste están corregidos**, cada uno con pruebas de
comportamiento y **vistas rojas antes** de tocar el código:

| # | defecto | arreglo | commit |
|---|---|---|---|
| 1 | la autorización guardaba un sí/no, no **qué** alternativa se aceptó | migración `012` (producto y cadena, con una regla en la base que rechaza un sí sin producto), `autoriza_linea` que lo exige y lo guarda, endpoint que lo recibe, cruce único a las líneas, y `_es_la_confirmada` que **pide confirmación nueva si el motor propone otra** | `6f5c04d`, `6daf219`, `e2b97a8`, `1416867`, `b8baeb1`, `1b882aa` |
| 2 | el canónico se construía por `(grupo, fuente)` | una referencia **por grupo, igual en todas las cadenas**; **el producto pedido manda** cuando la línea lo registra (por producto o por grupo); y **el alta guarda el miembro que enseña la ficha** | `565e7cf`, `b2c5d04`, `5a13436`, `2e75ddd` |
| 3 | dos líneas del mismo producto se pisaban | las cantidades **se suman**: pedir 2 y 3 es pedir 5 | `b7fd14a` |
| 4 | la publicación no publicaba | la pasada **publica lo que escribe**, así que el puntero deja de quedarse viejo | `25ee6bc` |

**Lo que se midió al arreglar el 2, y conviene no perder:** la ficha enseña el miembro **más barato por
unidad** y el motor comparaba contra el de **identificador más bajo**; son productos distintos en cuanto los
precios no acompañan. Se arregló **guardando** el miembro mostrado, no unificando la regla: «el más barato»
cambia con los precios todos los días, y atar la identidad al precio habría sido peor que el defecto.

### El orden del dueño: tres de cuatro verificados, y los puentes hechos

| # | punto | estado |
|---|---|---|
| 1 | el ensayo reparado: la compra **por su identificador** y por **las líneas realmente marcadas** | **verificado** (`TODO BIEN`) |
| 2 | aislamiento y autorización con **dos cuentas** y almacenamiento real | **verificado** (`TODO BIEN`) |
| 3 | **copia y restauración** en un entorno separado, comprobando su contenido | **verificado** (`TODO BIEN`; `plataforma/prueba_copia.py`) |
| 4 | puentes con confirmación e idempotencia, y las gráficas | **puentes hechos**; **gráficas: plan asentado** |

Los puentes, todos con pruebas de comportamiento:

- **favoritos → lista**: ya **no duplica**, y dice cuántas había (`dde6742`).
- **plan → lista**: **vista previa** (`4a82d81`) y **acción** (`b7faa4d`), compartiendo el cálculo. Los
  ingredientes salen de **la versión que el plan guardó**, y la cantidad va **a la nota** —la lista cuenta
  envases y la receta habla en gramos—.
- **consumir → diario**: **previa con la cobertura dicha** (`7b1be32`) y **acción** (`54d8289`), idempotente
  por el identificador de la línea de compra, y **sin inventar calorías**: la previa dice si hay datos de
  nutrición, no cuántos, y sacar los números del texto es otra pieza.

**Y el diario rechaza el tipo `compra` a propósito** —*comprar no es comer*—, que es la razón de que este
puente **proponga** en vez de copiar.

### Lo que queda

1. **Las gráficas**: que la serie lleve **medida** (precio por unidad), **cobertura** (cuántos puntos y sobre
   qué tramo, y callar si son pocos) y **universo** (el grupo o producto y las cadenas que entran), y que
   `Chispa.tsx` —una chispa **sin ejes**— los enseñe como **texto accesible**. El principio ya está escrito en
   `alertas.py`: *«sin histórico suficiente no se inventa un mínimo: se calla»*.
2. **El recorrido completo de las tres aplicaciones**, que es lo que queda del criterio de cierre. El ensayo
   con dos cuentas y copia restaurada está superado; **«usables de punta a punta» no se demuestra con pruebas
   de unidad**, y por eso **ninguna condición se ha declarado cerrada**.
3. La **publicación**: la pasada ya publica desde `25ee6bc`, pero el catálogo servido seguirá diciendo
   incoherente hasta que corra una pasada (o alguien publique una vez).

### El método que ha funcionado, y el que no

- **Observar antes de suponer.** Casi todas las rondas perdidas fueron por suponer un nombre, una forma o una
  aridad. Cuatro veces bastó con **preguntarle al módulo** (o al catálogo) en vez de recordarlo.
- **Compilar el texto nuevo ANTES de escribirlo**, y **abortar sin escribir** si algo no cuadra: ha evitado
  dejar el árbol roto cinco veces.
- **Un invariante entre pasos** cuando el cambio es grande: comprobar que las claves no cambian antes de
  seguir. *Compilar demuestra la sintaxis, no que el bucle siga haciendo lo mismo.*
- **Ejecutar con `subprocess` y lista de argumentos** para escribir dentro de contenedores: PowerShell partió
  cinco comandos con comillas y acentos graves.
- **Un rojo puede ser la prueba**: ha pasado seis veces, y una de ellas me llevó a **revertir un arreglo que
  estaba bien**. La regla vale también antes de revertir.
- **Lo escrito no está verificado.** La primera ejecución del guion de la copia encontró un `TypeError` mío;
  el ensayo de punta a punta encontró tres fallos que 1.400 pruebas no veían.

**Suite: en verde, `ruff` limpio.** Medida en `54d8289` y posteriores.

## Resumen vigente (13 de octubre de 2026) · corrección: la condición 2 NO está cerrada

**Este documento dijo que la condición 2 estaba cerrada y no lo está.** El dueño contrastó los informes con el
código y la plataforma en marcha y encontró **cuatro defectos**. La culpa del cierre prematuro es mía, y lo que
importa es que el estado lo diga: **ninguna condición se da por cerrada hasta que estos comportamientos estén
probados.**

| # | defecto | estado |
|---|---|---|
| 1 | la autorización guarda un sí/no por línea y **no qué alternativa** se aceptó: el motor puede cambiar de producto y seguir autorizado | **pendiente** (necesita migración `012` con producto y cadena confirmados) |
| 2 | `_candidatos` sigue construyendo el canónico por `(grupo, fuente)`: **no compara contra el producto solicitado** | **pendiente** (es la primera frase del encargo y sigue en pie) |
| 3 | dos líneas del mismo producto con cantidades distintas **se pisaban** al elegir candidato | **CORREGIDO** (`b7fd14a`), con prueba vista roja primero |
| 4 | `/api/estado` declara `coherente: false`: precios del 8 con publicación del 7 | **pendiente** (detectar ya funcionaba; falta resolver la publicación) |

**Y una nota sobre el defecto 3, porque enseña:** no era un descuido, estaba **escrito como decisión** —*«si la
misma apareciera en dos lineas con cantidades distintas, manda la ultima: es una decision, no un descuido»*—.
El razonamiento no se sostenía: dos líneas del mismo producto se compran juntas, así que la oferta que conviene
se decide con **las unidades totales**. La prueba que lo fija no compara números, compara **el candidato
elegido**: pedir 2 y 3 tiene que dar el mismo que pedir 5.

**Cifra de la suite: 1.428 pruebas, 0 fallos, ruff limpio** (medida en `b7fd14a`, no después).

## Resumen vigente (12 de octubre de 2026) · relevo: tres condiciones cerradas y lo que falta

### Cerrado, con sus dos puertas

Las condiciones **1 (aislamiento), 2 (identidad y coste) y 3 (pantallas y persistencia)** están cerradas. Su
detalle está en los resúmenes de los días 9, 10 y 11, más abajo. La **condición 2** se cerró con la
**autorización de la sustitución persistida por línea**: migración `011_autorizar_la_alternativa.sql`, dos
funciones en `almacen.py`, un endpoint para confirmar que pide permiso de **escritura**, y la autorización
leída de la base en los sitios que calculan precios.

**La puerta, a partir de ahora, son dos cosas:** `uv run ruff check .` y `uv run pytest -q`. Las dos limpias.
Los dos `NameError` en producción que aparecieron los vio **ruff**, no la suite.

### La condición 4 ha encontrado dos fallos reales, y uno está arreglado

El **ensayo de punta a punta** (`plataforma/prueba_e2e.py`) es lo que los encontró. Los dos existían **con la
suite en verde**, porque las pruebas de `tests/` sustituyen PostgreSQL y no ejecutan esos caminos:

| fallo | estado |
|---|---|
| `/api/estado` devolvía una cadena suelta: el decorador envolvía a un ayudante insertado entre el decorador y su función | **arreglado** (`351c679`), con prueba de forma vista roja antes |
| la **lista de la compra** y el **cierre de compra** reventaban con `too many values to unpack`: `mejor` tiene claves `(grupo_o_producto, fuente)` y `(grupo_o_producto, "alternativa")`, y los dos lectores descomponían la clave como un par | **arreglado** (`15fddb4`) y **confirmado** por el ensayo: `estimacion sin reventar: True` |

Ese segundo fallo enseña lo que más vale de estas rondas: mi primer intento de arreglo fue **incorrecto** (dejó
9 pruebas en rojo y la puerta lo paró) porque **la prueba y el arreglo partían de la misma suposición** sobre la
forma de la clave. Se arregló al **observar** la forma real, leyendo dónde se construye `clave` en
`_candidatos`. **Primero se observa, después se escribe la prueba, y solo entonces se arregla.**

### Pendiente, con nombre

1. **Una expectativa desactualizada en el ensayo.** `cerrar la compra` imprime «la compra no ha quedado
   guardada» **y a continuación la compra guardada**, con el mismo `compra_id` y sus dos líneas. La compra sí
   se guarda: lo que está viejo es la comprobación. Se pone al día **comparando con la evidencia que ella misma
   imprime**, no retocando la aserción para que pase.
2. **Reconstruir la imagen de la API.** El ensayo ejecuta el código del árbol, así que lleva los arreglos; **la
   plataforma servida en el 8080 se construyó antes y sigue teniendo el fallo de la lista.** Va antes de dar la
   condición 4 por cerrada.
3. **Los tres huecos del ensayo**: copia de seguridad **restaurada** (no existe ningún `pg_dump`/restore),
   **dos cuentas** contra base real (el aislamiento se prueba con PostgreSQL sustituido) y **la autorización de
   verdad** (confirmar → recargar → sigue autorizada, que es el recorrido que hasta esta semana no existía).
4. **Puentes idempotentes con vista previa** y **gráficas con medida, cobertura y universo**, las otras dos
   piezas de la condición 4.

### El método que funciona, por si la próxima sesión empieza de cero

- **Observar antes de suponer.** Casi todas las rondas perdidas fueron por anclar o comparar sobre un recuerdo.
- **Ficheros enteros o edición por número de línea leído**, nunca parches sobre fragmentos recordados.
- **Ejecutar con `subprocess` y lista de argumentos** escribe SQL y código dentro de contenedores sin pelearse
  con el entrecomillado de PowerShell, que ha partido cinco comandos esta sesión.
- **Un rojo puede ser la prueba**: ha pasado seis veces. Se mira qué afirma antes de tocar el código.
- **Lo que las pruebas no ejecutan, el análisis estático sí lo ve**; y lo que está registrado y servido solo lo
  ve **usar la aplicación**.

**Suite: 1.424 pruebas, 0 fallos.** Ruff limpio. La plataforma servida, pendiente de reconstruir.

## Resumen vigente (11 de octubre de 2026) · un fallo que solo se veía usando la aplicación

**Lo que pasó, porque es lo más útil de esta etapa.** `/api/estado` devolvía **solo la cadena de la versión**
(`"20261007-161518"`) en vez del objeto de estado, **desde la ronda 17**. La causa: al insertar el ayudante
`_version_del_catalogo` lo puse **entre** `@app.get("/api/estado")` y `def estado():`, y un decorador envuelve
**a la función siguiente**. La ruta quedó atada al ayudante y **`estado()` nunca se registró**.

**Por qué la suite no lo vio, y esto es lo que hay que recordar.** Mis pruebas de esa ruta comprobaban que el
texto `"version_catalogo": _version_del_catalogo()` estaba **escrito en el fichero**… y lo estaba. El módulo
importa sin error. La función es correcta. **El fallo existía solo en el registro de la ruta**, que es un hecho
de ejecución. Resultado: **1.413 pruebas en verde y el endpoint roto en la plataforma servida.**

**Cómo se encontró:** usando la aplicación. La comprobación en navegador de la ronda 31 pasó por `/api/estado`,
y a partir de ahí la cadena de descarte fue: no es el proxy (los dos caminos coinciden), no es una imagen vieja
(huellas del fichero idénticas), es **a qué función está atada la ruta**.

**Cómo se cerró:** con la disciplina del proyecto. Primero la prueba, y **vista roja** contra el código roto
(3 fallos, uno de ellos comprobando directamente a qué función está atada la ruta); después el arreglo —el
decorador movido encima de `def estado():`—; y **vista verde**. Una prueba que no se ha visto roja no prueba
nada.

**Y comprobado en lo que de verdad se sirve**, tras reconstruir la imagen:

| camino | respuesta |
|---|---|
| host, 8080 (Caddy) | `dict` con las cinco claves, `fecha_datos: 2026-10-08`, **5 cadenas**, `version_catalogo: 20261007-161518` |
| dentro, 8000 (la API) | el mismo `dict` con las mismas claves |

Así que lo de las rondas 17 y 33 (versión del catálogo y vigencia del precio) está **vivo**, no solo en el
repositorio.

**Corrección de una nota mía desactualizada:** el estado decía que Docker estaba parado y que había que
levantar PostgreSQL cuando tocara esa pieza. **Llevaba 36 horas levantado** (`cesta-api-1`, `cesta-db-1` y
`cesta-web-1`, los tres sanos), y esa nota hizo perder una ronda. No hay nada que levantar.

**La lección, en una línea:** una prueba que **lee el código** no sustituye a una que **llama al endpoint**.
Hay fallos —este— que solo existen en lo que está registrado y servido, y para esos hacen falta la prueba de
forma, la comprobación en navegador y la plataforma real.

**Suite: 1.416 pruebas, 0 fallos.** Ruff limpio, `tsc` limpio, build correcto.

**Lo que queda del objetivo:**

1. **La persistencia** de la autorización de sustitución en la línea: último punto de la condición 2, sin
   obstáculo (PostgreSQL está levantado).
2. **Condición 4**: puentes explícitos e idempotentes con vista previa, gráficas con **medida, cobertura y
   universo**, y el **ensayo integral** con datos reales, **dos cuentas** y **copia restaurada**.

## Resumen vigente (10 de octubre de 2026) · condición 3 cerrada

**Condición 3 — pantallas y comportamiento persistente: CERRADA.** Pieza a pieza, con su evidencia:

| pieza | estado | dónde |
|---|---|---|
| el detalle por receta lee la receta **persistida de su ruta**, con **404 real** y versiones accesibles | hecho | `paginas/RecetaDetalle.tsx`, `tests/test_detalle_receta.py` |
| el módulo compartido **fuera** de las rutas de recetas y calorías | hecho | las tres secciones de recetas, el diario y las tendencias tienen pantalla propia |
| editar una receta, diciendo que **crea versión nueva** | hecho | `componentes/FormularioReceta.tsx`, `tests/test_editar_receta.py` |
| **errores al archivar**, con el motivo de la API | hecho | `paginas/Recetario.tsx`, `tests/test_archivar_errores.py` |
| **plan modificable**, incluido **quitar** una receta de un día | hecho | `quitar_del_plan` + `DELETE /plan`, `tests/test_quitar_del_plan.py` |
| **cálculo de raciones**, servidor y pantalla, con **las dos cifras** | hecho | `core/recetas.escala`, `tests/test_raciones.py`, `test_raciones_en_pantalla.py` |
| S09: **cobertura por nutriente**, y un nutriente sin dato se dice con la palabra | hecho | `paginas/Diario.tsx`, `tests/test_cobertura_en_pantalla.py` |
| S09: **tendencias con huecos en vez de ceros**, y sin media inventada | hecho | `paginas/Tendencias.tsx`, `tests/test_tendencias.py` |
| la versión del diario: **enlace verificado** y **procedencia** (`vinculada` / `manual` / `perdida`) | hecho | `plataforma/api/diario.py`, `tests/test_procedencia_diario.py` |

**Comprobación en navegador: hecha, 23 comprobaciones y 0 fallos** (`uv run python -m plataforma.prueba_suite`,
con el servidor de desarrollo en 5173). Y **no es una comprobación vieja**: `/recetas` y `/calorias` ya
renderizan las pantallas nuevas, así que verifica que **cargan en un navegador real con cero errores de
página**, además de navegación, teclado, foco atrapado, Escape, móvil a 390 y escritorio a 1280, recarga en
ruta profunda y las direcciones antiguas con su query. Capturas en `data/capturas-s06/`.

**Lo que esa comprobación NO es, dicho para no confundirlo:** no es un recorrido funcional completo. No crea
una receta ni anota un día. Eso es el **ensayo integral de S12** —datos reales, **dos cuentas** y **copia
restaurada**—, que sigue pendiente.

**Suite: 1.408 pruebas, 0 fallos.** Ruff limpio, `tsc` limpio, `npm run build` correcto.

**Lo que queda del objetivo:**

1. **D, segunda mitad**: que la fecha de cada precio **pertenezca** a la versión del catálogo (la versión ya se
   informa en `/api/estado` desde la ronda 17).
2. **La persistencia** de la autorización de sustitución en la línea: necesita **PostgreSQL** levantado, y se
   levanta cuando toque esa pieza.
3. **Condición 4**: puentes explícitos e idempotentes con vista previa, gráficas con **medida, cobertura y
   universo**, y el **ensayo integral** con dos cuentas y copia restaurada.

## Resumen vigente (9 de octubre de 2026) · condiciones de la revisión

**Condición 1 — aislamiento por usuario: CERRADA.**

| qué | evidencia |
|---|---|
| Recetas: propietario **obligatorio** en crear, leer, listar, versiones, cambiar, archivar, planificar y plan | `core/recetas.py`, con el propietario como parámetro **sin valor por defecto** |
| Versiones y plan **heredan** el permiso de la receta (se llega por `receta_id` y lo primero es comprobar que es tuya) | `core/recetas.py`, `plataforma/api/recetas.py` |
| Diario: propietario obligatorio en apuntar, día, borrar y rango | `core/diario.py` |
| **401** para el anónimo en todos los endpoints de las dos aplicaciones | `tests/test_aislamiento.py` |
| **B contra A**: no enumera, no lee, no cambia, no archiva, no ve versiones, no planifica; borrar adivinando el identificador da **404**, no 403 | `tests/test_aislamiento.py` |
| El propietario **no se puede dictar** en el cuerpo de la petición | `tests/test_aislamiento.py` |
| Migración `ALTER TABLE ADD COLUMN`, **repetida 3 veces**, conservando el histórico (700 kcal, 6 raciones) con propietario **NULL** y **sin asignárselo a nadie** | `tests/test_aislamiento.py` |
| La **caché** se vacía al cambiar de cuenta y el vigilante va antes que la aplicación | `api/cuenta.ts`, `main.tsx`, `tests/test_cache_por_cuenta.py` |
| El usuario dentro de la clave en las cuatro pantallas nuevas | `api/recetas.ts`, `api/diario.ts` |

**Suite: 1.326 pruebas, 0 fallos.** Ruff limpio, `tsc` limpio, `npm run build` correcto.

**Pendiente de verificación, dicho para no confundirlo:** la comprobación **en navegador**
(`uv run python -m plataforma.prueba_suite`) no se ha pasado desde el aislamiento; necesita el servidor
de desarrollo levantado.

**Condición 2 — identidad solicitada y selección del coste: CERRADA** salvo dos cosas que
dependen de otras (abajo, dichas).

| caso | estado | evidencia |
|---|---|---|
| **A** grupo antiguo con dos marcas incompatibles | **hecho** | mismo GTIN con marcas distintas → **cuarentena**; sin GTIN, dos productos; marca vacía no inventa conflicto. `core/identidad.py`, `cesta.py`, `tests/test_marca_en_identidad.py` |
| **B** alternativa más barata **no autorizada** | **hecho**: regla, total por cadena, reparto, respuesta **y pantalla** | `Eleccion.autorizada`, `Peticion.autorizado` por línea, `_total_autorizado` con `pendientes`, `sin_autorizar` **en el orden**, `_serializa` con `identidad`/`motivo`/`autorizada`/`alternativa`, y el aviso que dice **qué se puede pedir y por cuánto**. 5 + 4 + 4 + 3 + 4 pruebas |
| **C** dos unidades donde el envase caro gana por promoción | **hecho** | coste final de las unidades pedidas, 150 frente a 180, en una función pura. `cesta.py::_coste_para`, `tests/test_seleccion_por_coste.py` |
| **D** precio o promoción futura | **parcial** | `fecha_tope` corta particiones posteriores de promoción (S05). **Falta**: fecha del precio y versión del catálogo |
| **E** variantes bajo el mismo GTIN | **hecho** | el motor las distingue **y** la selección ya no descarta la exacta: `_prefiere` hace que una exacta gane a una alternativa más barata, y la alternativa se guarda aparte. `tests/test_variante_no_tapa_la_exacta.py` |

**Lo que queda de la condición 2, y por qué no está hecho:**

1. **D, resto** — fecha del precio y versión del catálogo, además de la partición de promoción. Se puede
   hacer sin base de datos.
2. **La persistencia de la autorización en la línea** — hoy `Peticion.autorizado` viaja en la petición;
   falta guardarlo en la línea de la lista para que sobreviva a una recarga. **Depende de PostgreSQL**
   (la lista vive en `almacen`), y con Docker parado **no se puede probar de verdad**: no se declara hecho
   antes de poder probarlo.

**Y queda pendiente, de antes:** la comprobación **en navegador** (`plataforma/prueba_suite`), que no se
ha pasado desde el aislamiento por usuario porque necesita el servidor de desarrollo levantado.

## Cierre de la etapa (7 de octubre de 2026) · ronda 60 de 60

El objetivo **no está cumplido y sigue activo**: de los trece paquetes hay cuatro tocados y nueve sin
empezar. Lo que sigue es el estado real, sin adornos, y una valoración en los tres ejes que el encargo
separa a propósito: **función**, **calidad y cobertura del dato** y **operación y seguridad**. Un build
verde no certifica los otros dos.

### Estado por paquete

| paquete | estado | una línea |
|---|---|---|
| **S00** baseline | **hecho** | cambios heredados verificados y preservados; 1.195 pruebas de partida |
| **S01** publicación versionada | **hecho** | versión con puntero atómico, `rutas()` fija la versión por petición, rollback y concurrencia probados; catálogo real adoptado como primera versión |
| **S02** cola de fichas | **hecho** | SQLite con estados, *lease* con vencimiento, hash, evidencia y próxima revisión; inventario de **79.915** desde bronze en 75,7 s; informe de cobertura |
| **S03** Lidl | **en curso** | sitemap medido (6.622 → 691 incluidas, 1.568 de bazar evitadas, 4.363 a revisión) · ficha real y lector de JSON-LD con **GTIN validado** · **la cola pide fichas** (28 con ficha y hash, 5.026 pendientes) · cobertura de nutrición sobre 26 (0/26) · medidor con pruebas |
| **S04** identidad | **sin empezar** | el laboratorio de la ampliación es diagnóstico, no el algoritmo; el matching actual sigue siendo el anterior |
| **S05** selector único | **sin empezar** | primer arreglo ya localizado: **`_candidatos` recibe `fecha_tope` y no la aplica**, y sus llamantes pasan cadena vacía |
| **S06** armazón | **sin empezar** | sin menú lateral todavía; las correcciones a las referencias de Stitch están listadas (sin 11 px, sin datos ficticios, sin recursos externos) |
| **S07–S12** | **sin empezar** | Compra, Recetas, Calorías, puentes, gráficas y ensayo integral |

### Valoración honesta de preparación para un despliegue futuro

**Función: no.** No hay interfaz nueva construida. Las tres aplicaciones (Compra, Recetas, Calorías)
**no existen como tales**: siguen sin menú lateral, sin rutas separadas y sin las pantallas del
contrato. Lo que sí funciona es la **tripas de datos** que las sostendrá. Un despliegue hoy no tendría
nada que enseñar al usuario.

**Calidad y cobertura del dato: parcial, y con lo que falta medido.** El alcance, la cola, el
inventario y la publicación versionada están hechos y probados. Pero **la nutrición no está**: en Lidl
0 de 26 fichas la publican, y en el catálogo actual está a cero en Alcampo, Carrefour y Aldi. **La
identidad exacta (S04) no ha empezado**, así que las comparaciones entre cadenas siguen apoyadas en el
emparejador anterior: la regla del encargo —no sustituir un producto concreto sin elección explícita—
está en el contrato y **no implementada**. Y de las 79.915 fichas del inventario, **28 tienen ficha**.

**Operación y seguridad: sin verificar para un despliegue.** No hay despliegue público (correcto,
estaba fuera de alcance), **no hay credenciales en el repositorio**, y las peticiones se han hecho con
presupuesto, ritmo, robots respetado y sin bucles. Pero **no se ha probado ninguna copia de seguridad
restaurada**, **no se ha hecho el ensayo de dos cuentas** contra filtración, y la plataforma web **no
está levantada**. Eso es exactamente lo que S12 pide y no se ha hecho.

**Conclusión:** el proyecto está **más cerca que al empezar la etapa** —hay cimientos de datos
medidos, con pruebas y con límites escritos— y **no está listo para un despliegue**, ni público ni
doméstico serio. La distancia no es de semanas de trabajo: es de construir S06 a S12 y de cerrar S03 y
S04.

### Lo que falta, en orden, con el primer paso concreto

1. **S03, cerrar**: estratificar la muestra de fichas por familia (los 5.026 pendientes están en orden
   de identificador, que no es una muestra) y resolver los 4.363 a revisión **con la ficha**.
2. **S04, identidad exacta**: candidatos por GTIN —los de Lidl ya se validan— y por marca+familia+
   formato, veto de contradicciones, abstención como resultado válido, banco independiente y
   **publicación en sombra** antes de tocar nada de listas.
3. **S05**: aplicar `fecha_tope` en `_candidatos` y en todos sus llamantes, que hoy pasan cadena vacía.
4. **S06**: el armazón con menú lateral, respetando `SUPERAPP-01` y las correcciones a Stitch.
5. **S07 a S12**: las tres aplicaciones, los puentes, las gráficas y el ensayo integral.

### Cómo retomar

Primero **`uv run pytest -q` y `uv run ruff check .`** (la última suite completa verificada es
**1.243**). Después leer este fichero de arriba abajo: lleva la bitácora de commits de la etapa, lo que
está medido con su número, las decisiones cerradas que no se vuelven a preguntar y los límites dichos
al lado de cada cifra. La única dependencia externa es **Docker**, que hoy está parado, y solo hace
falta para verificar recorridos de interfaz.

## Paquete actual

**S03 · Lidl — PRIMERA MITAD HECHA.** Siguiente: **las fichas de los 5.054 candidatos** (S03, segunda mitad).

## Baseline (S00)

| dato | valor |
|---|---|
| commit | `e50f04c` (S00 baseline: los cambios heredados, verificados y preservados) |
| padre | `f74c432` (muro al día) |
| `uv run pytest -q` | **1.195 pruebas en verde**, 2 avisos de dependencias |
| `uv run ruff check .` | limpio |
| `uv run python -m projects.cesta.verificar_docs` | verde (166 comandos comprobados) |
| árbol | limpio |

**Cambios heredados que se preservaron tal cual** (no son míos y no se reescriben):

- `core/schemas.py`: `ProductoRaw.disponible` pasa a `bool | None` — distinguir «no sé» de «sí».
- `projects/cesta/collectors/dia.py`: conserva tablas nutricionales **parciales** sin inventar los
  nutrientes ausentes, y exige finito y no negativo.
- `core/datos/alcance.yml`, `core/datos/secciones.yml`, `docs/CIFRAS.md`: al día.
- `projects/cesta/collectors/lidl.py`: ampliado (sitemap y fichas) — **leer antes de tocarlo**.
- `plataforma/web/app/*`: `App.tsx`, `Cabecera.tsx`, `Producto.tsx`, `BotonAnadirACesta.tsx`,
  `package.json` con preparación de pantallas.

**No hay credenciales en el repositorio.** Las claves que circulan por el chat de origen deben
revocarse fuera del repositorio; aquí no se guardan ni se piden.

## Plan de paquetes (orden de dependencias)

| ID | estado | nota |
|---|---|---|
| S00 baseline | **terminado** | commit `e50f04c`, puertas ejecutadas |
| S01 publicación versionada | **terminado** | `core/publicacion.py`: versión con puntero atómico, `rutas()` fija la versión de una petición y fallback al catálogo suelto; 8 pruebas de aceptación |
| S02 cola de fichas | **núcleo hecho y medido** | `core/inventario.py` en SQLite: alta idempotente, lease con vencimiento, estados del contrato, próxima revisión, hash y evidencia; enganche desde bronze histórico. Falta: medir el inventario real y que los colectores consulten la cola |
| S03 Lidl por sitemap y fichas | **en curso**: sitemap medido (6.622 direcciones, 691 incluidas, 1.568 excluidas, 4.363 a revisión) | `projects/cesta/descubrir_lidl.py`: lee un sitemap guardado, separa fichas de categorías, clasifica por *slug* con la política (bazar inequívoco fuera, comida nunca fuera por su URL) e informa en direcciones y no en alimentos. Falta: recorrer el inventario real y las fichas |
| S04 identidad y banco independiente | pendiente | depende de S02 |
| S05 selector único y optimizador | pendiente | depende de S04 |
| S06 armazón y sistema visual | pendiente | **no depende de S01**; puede ir en paralelo |
| S07 Compra | pendiente | depende de S05 y S06 |
| S08 Recetas | pendiente | depende de S02 y S06 |
| S09 Calorías | pendiente | depende de S02, S06 y S08 |
| S10 puentes entre aplicaciones | pendiente | depende de S07–S09 |
| S11 gráficas y rendimiento | pendiente | depende de S07 y S09 |
| S12 ensayo integral y cierre | pendiente | depende de todo |

## Decisiones cerradas (no volver a preguntarlas)

- Menú lateral de aplicaciones en escritorio; cajón accesible en móvil.
- React/Vite/TypeScript y backend actual; sin migrar de framework.
- Datos e infraestructura locales; sin despliegue público ni servicios de pago.
- **Calorías es privada por persona**, aunque Compra sea del hogar.
- Un ingrediente genérico no es un producto comercial exacto. **Comprar no es consumir.**
- Prioridad a la precisión: **la abstención es un resultado válido**.
- Aprovechar el crudo histórico antes de pedir; renovar fichas conocidas por cola.
- No buscar paridad artificial de filas con Aldi.
- v0 ya dio la dirección visual; **no consumir más cuota**. Stitch es referencia, no código.

## Correcciones obligatorias al portar las referencias de `.stitch/`

1. Colores y tamaños de `SUPERAPP-01` §1; **rechazar los 11 px** de Stitch (mínimo 13 px en
   metadatos, 14 px en tablas, 16 px en cuerpo). Borde suave `#D8D2C7` **solo** decorativo: no
   delimita un control (contraste 1,43:1).
2. Compra: el panel derecho sale cortado en la referencia; lenguaje cotidiano («Mi lista»,
   «Tiendas», «Total estimado»), sin «gasto provisionado» ni «referencia mercantil».
3. Compra: **eliminar afirmaciones ficticias** de auditoría de tickets, comprobación física y
   producto exacto verificado. Precio ausente ≠ sin stock. Promociones con condiciones y cálculo.
4. Recetas: «Preparar lista» **abre una propuesta que se confirma**, no añade sola. Cambiar
   raciones escala unidades y recalcula cobertura nutricional.
5. Calorías: conservar «subtotal conocido» y el día sin datos como **hueco**. Los datos de la
   captura son de ejemplo.
6. El HTML descargado usa recursos externos: **no pegarlo**; portar componentes y servir local.
7. Las tres referencias son de escritorio: verificar 390 y 768 px, zoom 200 % y teclado.

## Problemas pendientes conocidos

- **T03 (identidad) sigue sin empezar** y es lo que gobierna que las comparaciones sean correctas.
  1.014 candidatos por GTIN y 10.999 pares con contradicciones medidos en el laboratorio.
- **T11**: la ficha ya llega en Carrefour, DIA y Aldi y se tira al parsear; en Alcampo no llega.
  Falta la extracción con procedencia y fecha por campo.
- **Lidl**: el colector existe y está probado sin red; la primera captura real está pendiente y
  `--escribir` está detrás de una bandera porque la pasada diaria **descubre** las cadenas.
- **La plataforma web no está levantada** (Docker parado); los recorridos de interfaz se verificarán
  cuando se levante o con el servidor de desarrollo.
- Sin medir todavía: `plataforma/web/app` `npm run build` y `npm run test:cocina` en este baseline.

## S01 · Publicación versionada — HECHO (7 de octubre de 2026)

`core/publicacion.py`. Cómo cumple su criterio:

| exigencia de S01 | cómo se cumple |
|---|---|
| caída entre escrituras no mezcla versiones | cada publicación escribe en `data/gold/v<fecha-hora>/` y el **puntero** (`actual.json`) se cambia con `os.replace` **solo** cuando están todos los ficheros; si falla, la carpeta a medias se retira y el puntero no se mueve |
| rollback probado | las versiones no se borran; `fijar(version)` vuelve a una anterior y rechaza una incompleta |
| concurrencia probada | `rutas()` resuelve la versión **una vez** y devuelve todos los caminos de esa misma publicación: una petición no puede mezclar `grupos` de una con `enlaces` de otra |
| no romper lo que hay | sin puntero se lee el catálogo suelto de siempre (fallback conservador) |

Publicar **no borra** y una versión existente **no se sobrescribe**. 8 pruebas de aceptación en
`tests/test_publicacion.py`.

**Pendiente dentro de S01**: el pipeline todavía escribe los ficheros sueltos; hay que hacerlo
publicar por versiones y que la API lea con `rutas()`. Se hace al entrar en S02/S05, para no tocar
la tarea de las 06:00 a la vez que se cambia la lectura.

## S02 · Cola de fichas — núcleo hecho y medido (7 de octubre de 2026)

`core/inventario.py` + `tests/test_inventario.py` (9 pruebas). Lo que aporta y lo que se midió:

| cosa | valor |
|---|---|
| **inventario levantado del bronze histórico** | **74.861 fichas**, sin una sola petición de red |
| alcampo | 43.603 |
| carrefour | 17.283 |
| dia | 6.292 |
| mercadona | 4.477 |
| aldi | 3.206 |
| tiempo del enganche | **75,7 s** (antes: más de 710 s de CPU y sin terminar) |

**Ese 74.861 no es el surtido de ningún supermercado**: es lo **descubierto** en el histórico, la unión
de todas las capturas. Hoy el catálogo tiene 51.659 productos, así que el inventario es un 45 % más
grande: son productos que aparecieron en alguna captura y no están en la de hoy. Es justo para lo que
existe el inventario —no perder de vista lo que un día se vio— y es el denominador honesto para hablar
de cobertura, en lugar de contar filas de un día.

**Dos fallos propios que se corrigieron aquí, y cómo se encontraron:**

1. La evidencia reventaba si el bronze estaba fuera del repositorio (lo cazó la prueba del enganche
   con un bronze temporal: justo donde se prueba).
2. El enganche hacía un *upsert* por **(día, producto)**: millones de escrituras para guardar dos
   fechas, porque bronze guarda la misma ficha treinta días seguidos. Se agregó en memoria
   (primera y última fecha por producto) y se escribe una vez por fuente: de no terminar a 75,7 s.
   **Cambio de contrato declarado**: `enganche()` devolvía altas procesadas y ahora devuelve
   **productos distintos**, que es el dato que interesa; su prueba lo explica.

**Instrumento añadido**: `projects/cesta/informe_inventario.py`, el panel de cobertura por fuente
(descubiertos, sin ficha, con ficha, con contenido útil registrado y vencidas, más las edades por
tramos). Es lo que pide SUPERAPP-02 §8, es de solo lectura y no toca la pasada diaria.

## S03 · Lidl, primera medida real (7 de octubre de 2026)

`projects/cesta/descubrir_lidl.py` bajó el sitemap público **una vez** (robots.txt primero, una sola
petición, y el XML guardado para repetir el análisis sin red) y lo clasificó por el *slug* de cada
dirección. Resultado:

| medida | valor |
|---|---|
| direcciones en el sitemap | **6.622** |
| fichas de producto (no son categorías) | 6.622 |
| **incluidas por la política** | **691** |
| **excluidas (bazar inequívoco)** | **1.568** |
| **a revisión (la URL no decide)** | **4.363** |

**Lo que esto demuestra, que es justo lo que el encargo avisaba de no suponer:** 6.622 direcciones
**no** son 6.622 alimentos. Solo 691 entran sin más; 1.568 son bazar claro —carros de jardín,
colchones hinchables, tijeras de podar— y **se evitan sin pedir ni una ficha**, que es el objetivo de
esta mitad del paquete. Y **4.363 no se pueden decidir desde la dirección**: el sitemap de Lidl usa
slugs largos y a menudo en alemán, y forzar una decisión ahí sería inventar.

**Lo que no dice:** nada sobre el surtido. Es **catálogo público descubierto**, con cobertura
desconocida, y una dirección tampoco prueba que la página viva (el encargo documenta un 404 en el
mismo sitemap). La cobertura real la dirá la otra mitad de S03: las fichas.

**Puente hecho (7 de octubre de 2026)**: lo descubierto se da de alta en la cola de fichas (`--registrar`), con su evidencia; los incluidos y los que quedan a revisión entran como candidatos, y el bazar inequívoco se cuenta pero **no genera trabajo**. Así el recorrido completo queda: sitemap → inventario → informe de cobertura.\n\n**Pendiente de S03**: (1) las fichas de ese inventario, con cola y presupuesto, para resolver los
4.363 y traer ingredientes y nutrición; (2) el informe por fuente y familia; (3) las ofertas
semanales como segunda corriente, sin confundir «producto conocido» con «precio de hoy».

**Pendiente dentro de S02** (es lo que lo hará útil de verdad): que los colectores **consulten la
cola** —pedir ficha a quien le falta, renovarla a quien le vence y no volver a pedir la que está
correcta y en plazo— y el informe diario de cobertura por fuente y familia. Hasta entonces esto es
memoria escrita, no renovación.

### Lo que trae la ficha de Lidl, medido (7 de octubre de 2026)

Leído el fixture guardado (`data/lidl-ficha-ejemplo.html`), sin red. Trae **tres** bloques de datos
estructurados, y solo uno es del producto:

    [0] @type=Product        name, brand, description, gtin13, sku, image, offers, url
    [1] @type=Organization   LIDL
    [2] @type=Organization   Lidl (con el programa de socio)

**Tres consecuencias, y las tres cambian el plan:**

1. **Hay `gtin13`.** La ficha de producto **sí trae código de barras**, que la página de ofertas no
   traía. Eso alimenta directamente la identidad de S04: un GTIN válido y con procedencia es la vía
   fuerte para decir «este es el mismo producto en otra cadena».
2. **`sku` (11000174) no es un EAN.** Es el identificador interno. El contrato lo prohíbe
   expresamente y ahora está visto en el dato, no supuesto: confundirlos envenenaría las
   comparaciones.
3. **No trae ingredientes ni nutrición.** El JSON-LD da identidad, descripción y ofertas; la ficha
   nutricional tendrá que salir del **cuerpo HTML** o de otra fuente. Para T11 esto significa que las
   fichas de Lidl darán identidad y precio, y habrá que medir aparte cuánta nutrición publica.

Y dos cuidados que ya están escritos para el lector: la `description` viene con **HTML** (hay que
sanitizarla, no pintarla) y `offers` es una **lista** (varias condiciones: normal y club, con fechas).

**Pendiente inmediato**: escribir el lector sobre el fixture (producto → campos de bronze) con
`gtin13` validado, `sku` **nunca** como EAN, `description` saneada y las condiciones de `offers`
separadas. Y después medir cuánta nutrición hay en el HTML de la ficha, sin darla por hecha.

## S03 · El lector de fichas, funcionando sobre una ficha real (7 de octubre de 2026)

`projects/cesta/ficha_lidl.py` lee el JSON-LD de la ficha y lo convierte en campos del proyecto. Sobre
la ficha real guardada (`data/lidl-ficha-ejemplo.html`):

    nombre: Galletas rellenas · marca: SONDEY · descripción: Rellenas de crema de chocolate.
    id_fuente: 11000174 (sku, identificador interno)
    ean: 4056489574392   <- GTIN válido, dígito de control comprobado
    precio_cent: None    <- y no se ha inventado
    condiciones: 1 oferta con availability=InStoreOnly y SIN importe

**Dos hallazgos que cambian el plan:**

1. **La ficha de producto de Lidl da códigos de barras de verdad.** El `gtin13` pasa la validación del
   dígito de control, así que **S04 tiene por fin una vía fuerte de identidad** con una cadena: GTIN
   válido y con procedencia. Y queda visto en el dato que `sku` no es un EAN.
2. **Esa ficha no publica precio.** Su oferta dice `availability: InStoreOnly` y no trae importe. El
   lector devolvió vacío en vez de inventar un precio, que es exactamente la distinción del encargo:
   **reunir fichas y disponer de precios actuales son trabajos diferentes**. La aplicación podrá
   conocer un producto de Lidl sin fingir que sabe cuánto cuesta hoy.

**Decisiones del lector, cada una con su prueba:** `gtin13` validado (el que no cuadra no se usa pero
tampoco se tira en silencio: se guarda aparte), `sku` jamás como EAN, `description` convertida a texto
en vez de pintada, y **dos condiciones de oferta no se funden en un precio**. Nueve pruebas en el
fichero, seis nuevas. Suite completa: **1.233 en verde**.

**Pendiente inmediato de S03**: la cola mandando (pedir fichas a los 691 incluidos con presupuesto por
host y día, guardar hash del contenido útil y versión de parser, próxima revisión a 30 días) · medir
cuánta nutrición publica Lidl en el **cuerpo HTML**, sin darla por hecha · resolver los 4.363 a
revisión **con la ficha, no con el slug** · informe por fuente y familia.

## S03 · ¿Publica Lidl nutrición? Medido, y con reservas (7 de octubre de 2026)

Sobre el fixture guardado, buscando **estructuras** y no palabras sueltas (que es la advertencia del
propio encargo):

| búsqueda | resultado |
|---|---|
| campos de una tabla nutricional española (energía, grasas, saturadas, hidratos, azúcares, proteínas, fibra, sal, kcal, kJ…) | **1 de 12**, y el que aparece es `kj` ×2 |
| bases que hacen interpretable una tabla (`por 100 g`, `100 ml`, porción con peso) | ninguna base real; `porción`/`ración` son texto de interfaz |
| señales de ingredientes (la palabra, harina, azúcar, aceite, cacao) | **0 de 6** — en un producto que **es una galleta** |

**Conclusión provisional: la ficha de producto de Lidl no publica la ficha nutricional.** Da
identidad (GTIN válido), nombre, marca, descripción, imagen y ofertas; la nutrición no está.

**Y el límite de esta medición, que importa tanto como el resultado:** es **un** producto. Un producto
no es la fuente. Para poder decir «Lidl publica poca nutrición» hacen falta **varias fichas
estratificadas** (frescos, envasados, droguería) y contarlo como cobertura, no como conclusión de
catálogo. Mientras tanto se dice **una ficha medida**, no una tendencia.

**Consecuencia para T11**: si se confirma, Lidl aportará **identidad y precio** a la plataforma y su
nutrición será una **limitación de fuente** que se declara —no se rellena desde otra fuente sin
decirlo, y no se presenta como dato propio—.

## S03 · Cobertura de nutrición sobre seis fichas (7 de octubre de 2026)

Ya no es un producto. El colector guarda ahora **una copia por producto** (`data/fichas-lidl/<id>.html`),
así que las fichas se acumulan y el análisis es **offline y repetible**. Sobre las seis primeras,
sacadas de la cola con presupuesto:

| medida | resultado |
|---|---|
| fichas guardadas | **6** |
| **con datos estructurados de producto** | **6/6** — el lector las lee todas |
| con tabla nutricional (3+ campos) | **0/6** |
| con base interpretable (`por 100 g`) | **0/6** |
| con ingredientes (2+ señales) | **0/6** |

**Qué permite decir esto:** la ficha de producto de Lidl es **fiable para identidad** (GTIN, nombre,
marca, descripción, imagen, ofertas) y **no trae la ficha nutricional** en las seis medidas.

**Qué no permite decir:** que sea así en todo el surtido. Son **seis fichas de 5.046 candidatos**, y
la muestra no está estratificada por familia (frescos, envasados, droguería). Se dice cobertura de
esta muestra, no una propiedad de la cadena.

**Progreso de la cola con estas rondas**: `correcto` pasó de 0 a **8**, y quedan **5.046**
pendientes. Cada ficha cerrada deja su hash del contenido útil, su versión de parser y su próxima
revisión a 30 días.


## S03 · ¿Resuelve la ficha lo que el *slug* no pudo? (7 de octubre de 2026)

Lidl dejó **4.363 direcciones a revisión** porque su *slug* no dice nada. El contrato dice que esos se
resuelven **con la ficha y no con el slug**, y eso hay que demostrarlo. Comparación sobre las
6 fichas ya leídas y guardadas, sin pedir nada a la red:

| resultado | fichas |
|---|---|
| el *slug* y la ficha coinciden | 5 |
| **la ficha cambia la decisión** | **1** |
| sin *slug* con el que comparar | 0 |

Casos donde el *slug* callaba o se equivocaba:

- `100272773`: incluido → **revisar** (None) · 4rain Depósito de agua "VASO 2in1 Decor", Volumen 220 Litros

**Lo que esto permite decir:** con 1 fichas, la ficha aporta decisión donde el
*slug* no la tenía. **Lo que no permite:** extrapolar a las 4.363 ni a la cadena. La
muestra es diminuta y no está estratificada; el valor está en que **el mecanismo
funciona**, no en el porcentaje.

## S03 · El lote acotado, y la cobertura sobre 26 fichas (7 de octubre de 2026)

La muestra de seis era anecdótica. Se han leído **20 fichas más** con la cola, en un solo lote acotado:

| medida | valor |
|---|---|
| fichas del lote | **20** |
| correctas / sin publicar / error de red | **20 / 0 / 0** |
| tiempo | **35,5 s** (ritmo del proyecto, robots respetado) |
| estado de la cola tras el lote | **correcto=28 · pendiente=5.026** |
| fichas guardadas en total | **26** |

**Cobertura de nutrición sobre 26 fichas** (el cuádruple que antes, y por eso vale más):

| medida | resultado |
|---|---|
| **con datos estructurados de producto** | **26/26** — el lector las lee todas |
| con tabla nutricional (3+ campos) | **0/26** |
| con base interpretable (`por 100 g`) | **0/26** |
| con ingredientes (2+ señales) | **0/26** |

**Lo que ahora se puede decir con más fundamento:** la ficha de producto de Lidl es **fiable para
identidad** en todas las leídas (y da GTIN válido) y, en **26 de 26**, **no trae la ficha
nutricional**. Veinte fichas seguidas sin un solo error de red ni una sin datos estructurados también
dice algo del instrumento: el lector y la cola aguantan un lote.

**Lo que sigue sin poder decirse:** que valga para todo el surtido. Siguen siendo **26 de 5.026
candidatos** y la muestra **no está estratificada por familia** (frescos, envasados, droguería): lo
leído son los primeros identificadores de la cola, que es una muestra cómoda y no una muestra
representativa. Para la afirmación sobre la cadena hace falta estratificar.

## Siguiente paso concreto

**S03 · segunda mitad: las fichas de Lidl.** Los 5.054 candidatos están ya en la cola (691 incluidos
y 4.363 a revisión) con su evidencia, y 1.568 direcciones de bazar quedaron fuera sin generar trabajo.
Lo que falta, en este orden:

1. **Un lector de ficha de Lidl** a partir de una ficha guardada (fixtures primero, sin red), con lo
   que publique: marca, título, descripción, ingredientes, alérgenos, nutrición con su base, peso,
   envase y procedencia. Lo que no publique queda `no_publicado`, no `null` sin motivo.
2. **La cola manda**: pedir ficha solo a los `pendiente`, con presupuesto por host y por día, guardar
   el hash del contenido útil y la versión del parser, y dejar `proxima_revision` a 30 días (7 si hay
   conflicto). Reanudable y sin duplicar, como ya está probado en S02.
3. **Resolver los 4.363 a revisión** con lo que diga la ficha, no con el *slug*: es la única forma
   honesta de saber si esos productos son de la cesta.
4. **Informe por fuente y familia** (descubiertos, incluidos, excluidos, ambiguos, visitados, vivos,
   con GTIN, con nutrición, con precio vigente y errores), sin declarar cobertura completa.

**Antes de eso, una comprobación de una línea**: pasar `uv run pytest -q` y `uv run ruff check .`, y
confirmar que siguen verdes. La última suite completa verificada es **1.223**.

### Lo que queda del encargo, sin adornos

- **Terminado y verificado**: S00, S01, S02 (núcleo, inventario y cobertura) y la primera mitad de S03.
- **Sin empezar**: S04 (identidad exacta, con el laboratorio como diagnóstico y no como sustituto),
  S05 (selector único: **`_candidatos` recibe `fecha_tope` y no la aplica**, y sus llamantes pasan
  cadena vacía — es el primer arreglo concreto del paquete), S06 (armazón con menú lateral, sin los
  11 px de Stitch ni datos ficticios), S07 a S12.
- **Decisión pendiente del dueño**: ninguna que bloquee. Cuando toque verificar recorridos completos
  de interfaz hará falta **Docker arrancado** (hoy está parado y la plataforma no responde).

## Detalle histórico: S02 · Cola de fichas. Crear el registro por `(fuente, id_fuente, variante, ámbito)` con
`discovered_at`, `last_seen_at`, `detail_fetched_at`, `next_check_at`, hash del contenido útil,
versión de parser, intentos y resultado; estados (`pendiente`, `en_curso` con lease, `correcto`,
`parcial`, `no_publicado`, `bloqueado`, `error_temporal`, `no_encontrado`, `excluido`); reanudación
sin duplicar; y el inventario de cobertura que hoy no existe. Empezar por el **crudo histórico**,
que ya está descargado, antes de pedir nada.

---## 9 de octubre de 2026 (tarde) — objetivo nuevo: las tres aplicaciones completas y usables

### Lo que se ha hecho y esta commiteado

| commit | que |
|---|---|
| `e155590` | **La seccion se hereda por grupo.** Un producto sin categoria propia recoge el pasillo de los productos con los que comparte grupo, en vez de quedarse sin ninguno. Con tres pruebas. |
| `481b1e0` | **El suelo del precio por unidad**, en `core/normalize.py` (`SUELO_REFERENCIA_CENT = 10`, `referencia_publicable`), y comprobado tambien en la comparacion. |
| — | **23 claves de seccion escritas a mano** en `core/datos/secciones.yml` (891 productos: los folletos de Alcampo a `promociones`, los turrones y polvorones a `desayuno-dulces`, los vinos a `bebidas`...). **El fichero NO se commitea**: lo mantiene la ingesta. Entra en la pasada del 10. |
| `892c1b7` | **Revertido mi propio trabajo redundante**: anadi `seccion_orden` a gold y la plataforma ya tenia el orden resuelto con su constante `ORDEN_SECCIONES`. Dos copias del mismo orden acaban discrepando. |

### Lo verificado, y con que evidencia

- **4 commits con `ruff` limpio y la suite completa en verde**, y los `diff --stat` limpios (42/32 lineas, no
  401/358: los finales de linea del repo estan mezclados —`normalize.py` y `comparacion.py` en LF,
  `pipeline.py` en CRLF— y escribir sin preservarlos convierte un cambio de una linea en una reescritura).
- **6 pruebas nuevas del suelo** del precio por unidad, que fijan la distincion por unidad: un kilo por
  debajo de 10 centimos es imposible; **300 bastoncillos por 1,09 EUR son 0,363 centimos cada uno y eso es
  un dato, no un error**.
- **Medido en gold, hoy**: 8.867 grupos con precio de referencia; 1.172 con dispersion mayor de 2x;
  1.524 filas con precio por unidad menor de 20 centimos, repartidas por las cinco cadenas
  (Alcampo 2,71 %, Carrefour 3,04 %, DIA 3,78 %, Aldi 4,47 %, Mercadona 1,07 %).

### Lo que se midio y resulto NO ser cierto (para no volver a buscarlo)

Trece hipotesis sobre el precio por unidad, trece refutadas midiendo: un divisor perdido, un factor de mil,
Aldi sin dividir por la cantidad, unidades de referencia mezcladas (explicaba el 7 %), precios rotos
causando la anchura de los grupos (el 2 %), Alcampo como cadena culpable (esta en las cinco), el paso
compartido en `envases.py`/`normalize.py`, y «falta la multiplicacion por diez» (existe, en
`core/normalize.lecturas_referencia`, con su tabla medida por cadena).

**La causa real, y es pequena**: el respaldo por cadena del precio de referencia, cuando la cadena no
publica formato con el que comprobar (`pipeline._referencia_que_cuadra` devuelve `None` en su primera
linea si no hay cantidad). Y **la banda «imposible» no era imposible**: de las 857 filas por debajo de
10 centimos, 573 son piezas baratas bien calculadas (pastillas, servilletas, toallitas, bastoncillos).

**La leccion**: el umbral con el que se mide no es una regla con la que se arregla. Se eligio 20 centimos
para mirar y se acabo tratando como «imposible»; despues se puso 10 para todo y habria borrado datos buenos.

### Lo pendiente, y por que

- **Docker no esta en marcha** (el named pipe `dockerDesktopLinuxEngine` no existe; nada escuchando en
  5432/5434/5435). Bloquea: las cuatro comprobaciones ordenadas —restauracion comparando importes
  guardados, datos desconocidos (NULL / 0 / total PARCIAL), transaccion con fallo provocado, y 3x2 con
  datos controlados—, la verificacion de la **migracion 013** en PostgreSQL, la publicacion y las
  comprobaciones sobre la imagen servida. **Todo lo anterior es codigo y medicion; nada de esto esta
  declarado cerrado.**
- **El cruce con Open Food Facts sigue sin enchufar**: 7,3 GB de datos listos y un modulo que funciona y
  que nadie llama. No necesita Docker y es la carencia funcional mayor.
- **La tarea 2 del backlog** (equivalencia ancha, el caso Perrier) sigue sin tocar, y es otra cosa que los
  precios rotos.
- **La cobertura de secciones** con las 23 claves nuevas y la herencia se vera en la pasada del 10.



---

## 9-10 de octubre de 2026 — profundidad de datos: Open Food Facts de punta a punta

### Hecho y verificado (con que evidencia)

| commit | que | como se ha comprobado |
|---|---|---|
| `e155590` | la seccion se hereda por grupo | 3 pruebas |
| `481b1e0` | suelo del precio por unidad (solo kg/l) | 6 pruebas |
| `892c1b7` | revertido un `seccion_orden` mio que duplicaba `ORDEN_SECCIONES` | diff limpio (2 lineas) |
| `3275780` | **el cruce con OFF se caia**: pedia `image_url`, que el subconjunto espanol no tiene | llamada real: 355.038 codigos |
| `95ca04e` | **Eco-Score** extraido de OFF (99,9 % de su base lo tiene) | 354.831 codigos |
| `26c9d76` | Eco-Score cruza a gold y la API lo sirve | 55 pruebas de la ficha |
| `17f2470` | **nutrientes por 100 g** con guarda de cordura | 732 valores fuera de rango descartados |
| `9b65da1` | los siete nutrientes cruzan a gold y la API | 10.778 productos |
| `18f215c` | **sello del Eco-Score** en el cliente, 7 grados | `tsc --noEmit` |
| `4a4951b` | los ocho campos en los dos tipos y el sello en la fila | `tsc --noEmit` |

**Medido, no estimado**: el cruce alcanza **13.056 productos**; dan **Nutri-Score 8.461**,
**ingredientes 8.288** (4.758 de Carrefour, que no publica ninguno), **Eco-Score 13.049** y
**nutrientes por 100 g 10.778**. Cuatro de las cinco cadenas **no publican nutricion**: solo DIA da algo.

**Y dos cosas que se midieron y resultaron NO ser ciertas**, para no volver a buscarlas: el Eco-Score no
tiene cinco grados como el Nutri-Score, tiene **siete** (de `a` a `f`, mas `a-plus` y `not-applicable`); y
el valor por 100 g de `nutriments` esta en el campo **`100g`**, no en `value`, que es nulo en todas las
filas -- la primera consulta filtraba por ahi y devolvia cero sin decir por que.

### Hecho, pero SIN VER EN PANTALLA

**El sello del Eco-Score y los ocho campos estan escritos y pasan `tsc`, pero nadie los ha visto
funcionando**: Docker no esta en marcha, asi que la aplicacion no se puede levantar. Estan enchufados a la
fila de resultados (`TablaResultados.tsx`) y al tipo de la ficha (`Producto`), y los datos cruzan y la API
los devuelve -- pero el ultimo metro, que se vean, no esta comprobado.

### Pendiente, y por que

- **La tabla nutricional en la ficha**: NO existe (no hay ningun componente que pinte nutricion; si hay un
  filtro `conNutricion` en la busqueda, que filtra por un dato que luego no se ensena). No se ha escrito
  porque **no tiene hermano que copiar** y sin la aplicacion en marcha se escribriria a ciegas. Las
  kilocalorias son el dato con el que alguien decide que come: aqui no se inventa una pantalla.
- **Docker caido** (el named pipe `dockerDesktopLinuxEngine` no existe; nada escuchando en 5432/5434/5435).
  Bloquea: las cuatro comprobaciones ordenadas --restauracion comparando importes, datos desconocidos
  (NULL / 0 / total PARCIAL), transaccion con fallo provocado, y 3x2 con datos controlados--, la
  verificacion de la **migracion 013**, la publicacion y las comprobaciones sobre la imagen servida.
- **`projects/cesta/emparejar.py` tiene dos implementaciones de lo mismo**: `externo_por_ean` (la que
  funciona y da datos a la aplicacion) y `core/off.py::enriquecer_por_ean` (rota hasta el 9 de octubre,
  arreglada sin necesidad). Hay que reconciliarlas o borrar una: dos copias acaban discrepando.
- **La tarea 2 del backlog** (equivalencia ancha, el caso Perrier) sigue sin tocar. Medido: 1.172 grupos
  con mas de 2x de dispersion, y **no** los causan los precios rotos (quitarlos baja a 1.145).
- **Los recorridos de las tres aplicaciones**, que es el criterio de cierre del objetivo.

### Metodo: cuatro cosas que costaron rondas y conviene no repetir

1. **Los ficheros de este repo tienen finales de linea mezclados.** `pipeline.py` y `tipos.ts` en CRLF;
   `normalize.py` en LF. Escribir sin preservarlos convierte un cambio de una linea en una reescritura de
   1.626. Y al **leer** hay que normalizar (`\r\n` -> `\n`) o **ninguna** comparacion de texto coincide --
   y el error que aparece ("el ancla no es unica") es mentira: no coincide ninguna.
2. **Cada lenguaje tiene su puerta**: `ruff` y `pytest` para Python, `tsc --noEmit` para el cliente. Use
   `compile()` de Python sobre un `.tsx` y perdi una ronda.
3. **Preguntar "¿esto ya esta enchufado?" antes de "¿por que no se usa?"**. La segunda me llevo a arreglar
   una pieza duplicada que no hacia falta; la primera me llevo en dos rondas al unico campo de OFF sin leer.
4. **El umbral con el que se mide no es la regla con la que se arregla.** Se eligio 20 centimos para mirar y
   se acabo tratando como "imposible"; despues se puso 10 para todo y habria borrado 573 piezas baratas bien
   calculadas (300 bastoncillos por 1,09 EUR son 0,363 centimos cada uno).



---

## 10 de octubre de 2026 — la presentacion de los datos de Open Food Facts

### Hecho y verificado

| commit | que | evidencia |
|---|---|---|
| `18f215c` | sello del Eco-Score, **siete grados** (de `a` a `f`, mas `a-plus` y `not-applicable`), `A+` con ancho para dos caracteres, procedencia en el `title`, y estado vacio con la voz de la casa | `tsc` |
| `4a4951b` | los ocho campos (Eco-Score + siete nutrientes) en `ResultadoBusqueda` y `Producto`, y el sello en la fila de resultados | `tsc` |
| `81015f6` | **un solo bloque de nutricion en la ficha**: el de la cadena y, si no publica ninguno, el de OFF con su forma y su procedencia. Los campos tambien en `ProductoSuelto` | `tsc` |

### El quinto duplicado, y el primero que se borra

La ficha **ya tenia un bloque de nutricion** (`miembro.nutricion`, con `filasNutricion()` y `NO_LO_SE`):
el de la cadena, es decir el de DIA, los 3.954 productos que lo publican. **Escribi `FichaNutrientes` sin
mirar la pantalla, con otra forma** -- un `dl` con borde propio -- que al lado del `ul` existente se leeria
como un bloque ajeno. **Se ha borrado** y en su lugar se ha extendido el bloque que ya habia: cuando la
cadena no publica nutricion y OFF si, se ensena la de OFF con **la misma forma**, la misma base dicha y el
mismo `NO_LO_SE`, y nunca los dos a la vez.

Eso es lo que hace que **10.778 productos de Carrefour, Mercadona, Alcampo y Aldi** -- cadenas que no
publican nada nutricional -- dejen de tener ese apartado vacio.

**Los ocho campos viven en tres tipos**, y los tres los nombro `tsc` al fallar, no yo al suponer:
`ResultadoBusqueda` (la fila), `Producto` (la ficha del grupo) y `ProductoSuelto` (esta pantalla).

### Docker: sigue caido, comprobado de tres formas

`docker ps` falla; **ningun puerto escuchando** en 5432/5434/5435; y `Test-Path` sobre el named pipe
`dockerDesktopLinuxEngine` dice que **no existe**. Bloquea las cuatro comprobaciones ordenadas, la
verificacion de la migracion 013, la publicacion, y **ver en pantalla las tres piezas nuevas**. El objetivo
**no** esta bloqueado: lo esta esa parte de su verificacion. Todo lo anterior es codigo, medicion y tipos.

### Leccion de estas siete rondas

**Leer la pantalla antes de escribir la pieza.** `tsc` valida tipos, **no duplicados**: `FichaNutrientes`
compilaba, tipaba bien y no rompia nada -- solo leyendo la ficha se veia que la nutricion ya estaba puesta.
Es la quinta vez en la sesion que se construye algo que el proyecto ya tenia (el orden de los pasillos, el
enriquecido de OFF, el tipo de fila, los campos en el tipo equivocado, y este bloque), y la primera en que
el arreglo es **borrar** en vez de integrar.



---

## 10 de octubre de 2026 — la tarea 2 del backlog: nada que construir

### Lo que se ha medido

**La linea base del emparejador, hoy**: `emparejar --medir` da **1.163 de 1.786 pares con el mismo EAN
encontrados, el 65 %** (el backlog dice 57 %: ha cambiado). 21.342 enlaces, 40.547 grupos, y **las tres
invariantes a cero violaciones** (eje contradictorio 0, grupos de 11+ 0, cadena repetida sin EAN 0). Cada
medicion completa cuesta **388 segundos**.

**Los grupos anchos**: 1.082 de unos 40.000 (**2,7 %**), repartidos por las cinco cadenas por igual. Se
descartaron tres causas antes de tocar nada: los precios imposibles (quitarlos baja de 1.172 a 1.145, el
2 %), las unidades de referencia mezcladas (85 grupos, el 7 %), y **«es de una cadena»** -- Alcampo es el
mas barato en el 51 % de los grupos y solo en el 24 % de los anchos, asi que esta **infra**representado.

### Lo que ya existia, y por eso no se ha escrito nada

| freno | donde | medicion |
|---|---|---|
| tope de dispersion | `matching.ANCHO_MAXIMO = 3.0`, por unidad de medida y solo con precios fiables | escrito y calibrado |
| invariante del reparto | un grupo correcto no puede tener dos productos de la misma cadena, **salvo que compartan EAN** (38 duplicados legitimos en gold) | 2-4 miembros: 9,8 % con cadena repetida; 5-10: 94,8 %; 11+: **100 %** |
| el eje que el nombre declara | `virgen` contra `virgen extra`, `con azucar` contra `sin azucar`; **si uno no declara nada, no bloquea** | 49 grupos, y hoy **0** |
| **umbral por seccion** | `matching.pesos_por_pasillo` | **escrito, medido y descartado**: el grupo mayor baja de 97 a 80 y la tasa de anchos **empeora** (6,28 % a 6,38 %), porque **los puentes los abre el canal de trigramas, no el de palabras** |

**Conclusion: la tarea 2 esta cumplida y no hay nada que anadir.** Los 1.082 grupos anchos que quedan son el
**suelo** de este enfoque: lo que esos frenos no pueden quitar sin romper emparejamientos buenos. Y el
numero del backlog (405) no sale porque el catalogo y el emparejador han cambiado desde que se escribio.

**Lo que si aportan mis medidas, y el codigo no tenia**: el **precio** de apretar. Con 3x se evitan 261
grupos a cambio de 9 aciertos probables (28 a 1 a favor); con 5x, 103 a cambio de 6. Y la exencion del mismo
EAN no es una tolerancia: **dos productos con el mismo codigo de barras son el mismo producto**, y si sus
precios se llevan mucho el problema es del dato, no del grupo.

### Leccion

**Antes de escribir un freno, buscar el freno.** Van siete veces en esta sesion que el proyecto ya tenia la
pieza: el orden de los pasillos, el enriquecido de OFF, el tipo de fila, los campos en el tipo equivocado,
el bloque de nutricion de la ficha, el tope de dispersion y el umbral por seccion. Y en esta ultima, el
proyecto no solo la tenia: tenia **la medicion de que no funciona** -- escribirla habria costado 388
segundos de emparejador para descubrir lo que dice un docstring.



---

## 10 de octubre de 2026 (tarde) — el fallo de Alcampo, y las tres aplicaciones

### El mayor defecto de datos arreglado en este tramo: **129.668 filas de Alcampo**

**Medido**: de las 639.629 filas de Alcampo en silver, **190.732 (29,8 %) salian sin unidad de
referencia**, y **129.668 (20,3 %) ademas con un precio que la cadena SI habia mandado**, distinto del
precio. Sin unidad, el factor se queda en 1 y el valor pasa sin escalar.

**La causa, exacta**: `_UNIDAD` tenia la familia `fop.price.per.*` y tres nombres sueltos, pero **no las
formas de `unitName`** (`PER_100ML`, `PER_100G`, `PER_KG`...) que la cadena manda en mayusculas y que se
buscan en minusculas. Un diccionario de 17 entradas al que le faltaban 17 mas.

**Arreglado** (`062bb3e`): 17 sinonimos, **cada uno mapeado igual que su gemela `fop.*`**, con 12 pruebas
que incluyen una etiqueta desconocida (que **sigue sin inventarse**: `(None, 1.0)`).

**Acotado**: las otras cadenas **no lo tienen** -- Carrefour 0, DIA 1, Mercadona 0, y Aldi 353 de 69.987
(el 0,5 %, porque la mayoria de sus filas sin unidad no traen precio que escalar). La razon de que sea de
Alcampo y de nadie mas: es **la unica cadena que publica el precio por unidad etiquetado**; las otras dan
un numero (`basePriceValue`, `price_per_unit`, `bulk_price`) y no hay etiqueta que interpretar.

**Pendiente**: cuantas de las 129.668 ganan unidad cuando el colector vuelva a correr.

**Y la leccion, que es la mas util de la sesion**: se busco este fallo durante **cuarenta rondas** con un
umbral de "precio por unidad imposible" (< 20 centimos) y se encontraron **1.524 filas**. El fallo afectaba
a **129.668**. **El umbral con el que se busca decide que se encuentra**: un precio por 100 g leido como
por kilo da 1,8 centimos donde tocaban 18 -- entra en la banda y se ve --, pero el mismo error en un
producto de 3,50 EUR da 35 centimos donde tocan 3,50 EUR, **que no es imposible: es falso, y nadie lo
miraba**.

### La tarea 2 del backlog: cumplida, sin construir nada

Los tres frenos ya existian y el cuarto estaba medido y descartado. Ver la seccion anterior: `ANCHO_MAXIMO
= 3.0` por unidad y solo con precios fiables, la invariante del reparto (con los pares de mismo EAN
exentos, 38 duplicados legitimos), y el eje que el nombre declara. El **umbral por seccion**
(`matching.pesos_por_pasillo`) se escribio el 22 de septiembre, se midio, y **no sirve**: el grupo mayor
baja de 97 a 80 y la tasa de anchos empeora, porque **los puentes los abre el canal de trigramas**.

### Las tres aplicaciones tienen ya su logica

| | commit | que |
|---|---|---|
| calorias/diario | `a6fe871` | **`de_ficha` y `apunta_de_ficha`**: de los nutrientes por 100 g a una entrada del diario, nutriente a nutriente, `fuente='ficha'`, y **sin rellenar con ceros lo que no sabemos**. 150 g de 485 kcal/100 g = 727,5 kcal, probado. |
| recetas | `054b311` | **`nutricion(ingredientes, productos)`**: las calorias de una receta, **separadas del emparejamiento** (que acierta 3 de 16), solo g y kg pasan a gramos, y un ingrediente sin identificar **no aporta cero** -- se cuenta aparte y el total dice cuanto falta. |

Las dos siguen la doctrina que el diario ya tenia escrita: *«ausencia no es cero»*, *«las dos cifras van
juntas»*, y *«lo que no tiene cantidad, no la gana»*.

### El estado, en tres columnas

**Verificado por pruebas y tipos**: los 20 commits del objetivo; los frenos del emparejador (3 invariantes
a cero, 65 % de aciertos medido); el cruce con OFF (13.056 productos: Nutri-Score 8.461, ingredientes
8.288, Eco-Score 13.049, nutrientes 10.778); la aritmetica del diario y de la receta; y `tsc` limpio en el
cliente.

**Escrito, SIN VER EN PANTALLA**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque
unico de nutricion en la ficha, y **los pasos de interfaz del diario y de la receta** (elegir producto y
gramos; ensenar las calorias con sus dos cifras).

**Esperando a Docker**: las cuatro comprobaciones ordenadas, la verificacion de la **migracion 013**, la
publicacion, y **los recorridos de punta a punta de las tres aplicaciones** -- el criterio de cierre del
encargo. El motor no esta en marcha: `docker ps` falla, **ningun puerto escuchando** en 5432/5434/5435, y
el named pipe `dockerDesktopLinuxEngine` no existe.



---

## 10 de octubre de 2026 (noche) — las rutas que faltaban, y una decision de diseno fundada

### Las dos rutas, enchufadas

| commit | ruta | que hace |
|---|---|---|
| `6c05b68` | `POST /api/diario/desde-ficha` | usa `apunta_de_ficha`: recibe los valores por 100 g y los gramos, y **la cuenta la hace el servidor** para que la regla de "lo que no se sabe no es cero" viva en un solo sitio |
| `d17a360` | `POST /api/recetas/{id}/nutricion` | usa `nutricion`: devuelve kcal y macros **con sus dos cifras** (lo conocido y cuantos ingredientes faltan). **Hace la cuenta y no empareja**: recibe lo que el que llama pudo confirmar |

**Leccion de metodo, y van cinco de la misma familia.** La primera prueba de ruta que escribi fallaba
**incluso para las rutas que ya existian**, y el motivo era mi forma de mirar: `app.routes` **no aplana**
los routers incluidos -- aparecen como objetos anidados con el `path` vacio y sus rutas dentro. La
comprobacion buena es **`app.openapi()["paths"]`**, que es el contrato que la aplicacion publica y se
construye sin servidor ni Docker.

Las cinco, para no repetirlas: `seccion` contra `pasillo` en el cliente; el umbral de 20 centimos; `@app.`
contra `@rutas.`; `app.routes` contra `app.openapi()`; y los cinco mas anchos como muestra. **Siempre el
mismo error: buscar con mis palabras en vez de con las del proyecto.**

### Y por que los ingredientes de una receta los elige la persona

**Medido con datos controlados** (el corpus de recetas esta **vacio**: `data/recetas.sqlite` tiene 0 filas
en `receta` y 0 en `plan`, asi que no hay nada real contra lo que medir):

    patatas           -> Tortilla de patatas con cebolla     MAL
    cebolla           -> Tortilla de patatas con cebolla     MAL
    aceite de oliva   -> Aceite de oliva virgen              bien
    harina de trigo   -> Harina de espelta integral          bien
    pechuga de pollo  -> Pechuga de pollo Dia Nuestra        bien
    leche entera      -> Leche entera                        bien
    tomate            -> Tomate triturado extra              dudoso
    arroz             -> Arroz basmati                       dudoso

**Seis de ocho caen en la familia correcta, y dos fallan de la peor manera**: "patatas" y "cebolla"
devuelven **la misma tortilla**, porque la busqueda empareja **palabras** y "tortilla de patatas con
cebolla" las contiene todas. No es un caso raro: es lo primero que escribe cualquiera.

**Y los resultados de la busqueda no traen `seccion` ni `kcal_100g`**, asi que ni un acierto alimentaria a
`nutricion` sin una segunda consulta por `fuente` e `id_fuente`.

**Decision**: el que cocina **elige el producto** (busca y toca el que quiere) y `nutricion` hace la
cuenta. Es la regla de la casa -- *nunca se acepta a ciegas* -- aplicada a un numero que la gente usa para
decidir que come. Y es mejor producto: **esa persona sabe si el tomate es fresco o de bote**, y ninguna
heuristica lo sabe. El "emparejamiento" es **un paso de interfaz, no un algoritmo**.

### El estado, en tres columnas

**Verificado por pruebas y tipos**: los 23 commits; los frenos del emparejador (3 invariantes a cero, 65 %
de aciertos); el cruce con OFF (13.056 productos); la aritmetica del diario y de la receta; las dos rutas
nuevas, contra `app.openapi()`; y `tsc` limpio en el cliente.

**Escrito, SIN VER EN PANTALLA**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque
unico de nutricion de la ficha, y **los pasos de interfaz** del diario (elegir producto y gramos) y de la
receta (elegir los ingredientes y ver las dos cifras).

**Esperando a Docker**: las cuatro comprobaciones ordenadas, la verificacion de la **migracion 013**, la
publicacion, y **los recorridos de punta a punta de las tres aplicaciones** -- el criterio de cierre. El
motor no esta en marcha: `docker ps` falla, ningun puerto escuchando en 5432/5434/5435, y el named pipe
`dockerDesktopLinuxEngine` no existe.



---

## 10-11 de octubre de 2026 — el encargo por paquetes, y la capa que no habia leido

### Lo primero: el encargo estaba escrito y no lo habia leido

**`docs/SUPERAPP-00-EMPEZAR-AQUI.md`** (7 de octubre de 2026) es **el encargo de ejecucion**, y contiene
**13 paquetes S00-S12** con dependencias y criterio de aceptacion cada uno. Es la pieza de contexto que ha
faltado durante 135 rondas. Lo esencial:

| ID | trabajo | se acepta cuando |
|---|---|---|
| S00 | congelar baseline, `CESTA-MURO.md` | estado git, comandos y cifras fechadas |
| **S01** | **publicacion versionada, `core/manifiesto.py`, storage y lectores** | **crash entre escrituras no mezcla versiones; rollback y concurrencia probados** |
| S02 | cola de fichas, collectors, inventario de cobertura | todo producto con estado, proxima revision y evidencia |
| S03 | Lidl por sitemap, fichas y ofertas | informe por fuente y familia; una ausencia no es una retirada |
| S04 | identidad, banco independiente, matching y API | exactos, formatos y alternativas separados; metricas por familia |
| S05 | selector unico y optimizador, `api/cesta.py` | fechas, tienda, club y cantidad en todos los endpoints |
| S06 | armazon y sistema visual, `App.tsx`, `Nav.tsx` | tres layouts, drawer, teclado, responsive y CSP |
| S07 | Compra: busqueda, ficha, favoritos, listas, reparto | recorrido real con producto exacto y alternativa explicita |
| S08 | Recetas: biblioteca, editor, modo cocina, planificador | varias recetas, recarga, edicion, raciones |
| S09 | Calorias: diario propio y tendencias | alimento/receta versionados; dias incompletos; no compras como comidas |
| S10 | puentes entre aplicaciones | repetir no duplica; vista previa y consentimiento |
| S11 | graficas, aprendizaje y rendimiento | cada grafica define medida y universo; tabla accesible |
| S12 | ensayo integral y cierre | datos reales, dos cuentas, backup restaurado, movil/escritorio |

**Y el documento fija decisiones cerradas** que coinciden con lo que yo fui deduciendo midiendo: *"un
ingrediente generico no es un producto comercial exacto"* (mi medicion: "patatas" devuelve una tortilla),
*"comprar no es consumir"*, *"priorizar precision a cantidad; la abstencion es resultado valido"*, y
*"Calorias es privada por persona, aunque Compra sea compartida por hogar"*.

**Comandos que el encargo nombra y que conviene usar**: `uv run pytest -q`, `uv run ruff check .`, y **en
`plataforma/web/app`: `npm run build` y `npm run test:cocina`**. El segundo **no se ejecuto hasta la ronda
136**, y por eso se escribieron cuatro piezas sin saber que ya existian.

### Una capa entera del cliente que no conocia: `logica/` y `estado/`

Casi 500 lineas **con sus reglas escritas y sus pruebas propias**:

- **`logica/pesos.ts`** (227) -- como se ordenan las alternativas. Cinco reglas, entre ellas: *"`calidad` y
  `gama` son excluyentes... nunca se suman"* (verificado: el contrato de `/api/grupo` lo garantiza por
  construccion), *"la nota se reparte solo entre lo que se sabe: un cero se lee como 'malo' y seria
  mentira"*, y *"una promo ausente es un cero de verdad, porque 'no hay promocion' es un dato, no un hueco"*.
- **`logica/frase.ts`** (88) -- *"si el grupo no es de fiar, NO se inventa la frase... una tabla se mira con
  desconfianza, **una frase se cree**"*.
- **`logica/curva.ts`** (111) -- *"nunca se dice 'los ultimos 90 dias' si no los tenemos"*.
- **`estado/cocina.ts`** (38) -- la nutricion de una receta: `validarReceta`, `calcular`, `listaReceta`, con
  **`valor` y `faltantes` por nutriente**, cero real y ausencia en `null`.
- **`estado/referenciaLinea.ts`** -- la eleccion exacta frente al grupo.

### Y un duplicado mio, revertido

Escribi `core/recetas.nutricion` y su ruta `/api/recetas/{id}/nutricion` **sin haber leido `estado/cocina.ts`,
que ya hacia lo mismo** -- y ademas admite `100ml`, que mi version rechazaba. Revertidos los dos commits
(`9721d29`). **Se queda la del diario** (`de_ficha`, `apunta_de_ficha` y `POST /api/diario/desde-ficha`):
no la duplica nadie, y su forma -- valor y faltantes por nutriente -- es la misma que la del cliente, asi
que las dos aplicaciones quedan coherentes.

**Es el segundo duplicado que borro y el quinto que reconcilio. La causa, en las cinco, ha sido la misma:
escribir antes de leer.**

### Las dos rutas que si se quedan

| commit | ruta | que hace |
|---|---|---|
| `6c05b68` | `POST /api/diario/desde-ficha` | usa `apunta_de_ficha`; la cuenta en el servidor |
| `9721d29` | (reversion de la de recetas) | el cliente ya la hacia |

**Y la leccion de comprobacion**: `app.routes` **no aplana** los routers incluidos (aparecen como objetos
anidados con el `path` vacio); el contrato publicado es **`app.openapi()["paths"]`**, y se construye sin
servidor ni Docker. Es la comprobacion que vale para saber si una ruta esta de verdad enchufada.

### Estado, en tres columnas

**Verificado**: 25 commits; 1.540 pruebas Python y 6 del cliente en verde; los frenos del emparejador (3
invariantes a cero, 65 % de aciertos); el cruce con OFF (13.056 productos); la aritmetica del diario; la
ruta del diario contra `app.openapi()`; `tsc` limpio.

**Escrito, sin ver en pantalla**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque de
nutricion de la ficha, y los pasos de interfaz del diario.

**Esperando a Docker**: las cuatro comprobaciones ordenadas, la verificacion de la **013**, la publicacion,
y **los recorridos de punta a punta** (S07/S08/S09 y S12 del encargo). El motor no esta en marcha: `docker
ps` falla, ningun puerto escuchando en 5432/5434/5435, y el named pipe no existe.

**Y lo que dice el encargo que NO hay que hacer**: *"no sustituir implementacion por ampliar este plan otra
vez"* y *"no parar simplemente por terminar un paquete; tampoco declarar todo completo cuando quedan
fallos"*.



---

## 11 de octubre de 2026 — S01, la frontera de polars, y tres falsos positivos mios

### S01 tiene su criterio de aceptacion YA DEMOSTRADO

`tests/test_publicacion.py` se titula **"Puerta de S01"** y cubre las cuatro frases del criterio, **con
ejecuciones de verdad sobre un directorio temporal** (su cabecera lo dice: *"ninguna se apoya en mirar el
codigo"*):

| prueba | que demuestra |
|---|---|
| `test_una_caida_entre_escrituras_no_mezcla_versiones` | **hace fallar `write_parquet` en el segundo fichero**: el puntero no se mueve y la carpeta a medias se retira |
| `test_rollback_a_la_version_anterior` | volver atras apunta a una anterior, y las dos versiones siguen ahi |
| `test_una_peticion_ve_una_sola_version` | concurrencia: todos los caminos de una peticion comparten carpeta, y la anterior sigue apuntando a la suya |
| `test_sin_version_publicada_se_lee_el_catalogo_suelto` | el fallback conservador |

**Y el pipeline ya publica** (`pipeline.py:800-805`, al final de la pasada, con su `try`) y **la API ya
informa de la version** (`/api/estado` devuelve `version_catalogo: 20261009-122845`). Asi que S01 no esta
"construido y sin adoptar": esta **adoptado en la escritura y probado en las cuatro frases**.

### Y el lector NO se adopta, por una razon que tiene prueba propia

`main.py:374` y `main.py:1171` leen `data/gold/actual.json` **a mano**, y dicen por que:

> *"Sin importar `core.publicacion`: ese modulo trae **polars** -- publica DataFrames -- y **la imagen de la
> API no lo lleva, que es una restriccion con prueba propia**. Leer un JSON pequeno no justifica arrastrar
> una libreria de datos entera."*

**No es un duplicado descuidado: es una frontera deliberada.** La misma leccion que `comparacion.py`
documenta desde el otro lado (polars en la API causo reinicios de `cesta-api` el 21 de septiembre de 2026).

**Si algun dia se quiere una sola lectura del puntero**, el camino NO es importar `publicacion` en la API:
es **sacar la lectura a un modulo pequeno sin polars** que usen los dos. Mismo objetivo moviendo el codigo,
no anadiendo una dependencia. **Queda apuntado, no hecho: hoy no hay ningun sintoma que lo pida.**

### Y tres falsos positivos mios, seguidos

Las tres veces **el codigo tenia razon y yo no**:

1. **El lector por el puntero** (rondas 146-147). Escribi el cambio -- vistas por `publicacion.ruta` y el
   sello por la version publicada -- y **la suite se cayo**: las pruebas de alertas, entre otras. El motivo:
   `data/gold` tiene ficheros sueltos **mas nuevos (12:35) que la version publicada (12:28)**, asi que
   adoptar el lector **habria servido datos de siete minutos antes**. Revertido sin dejar rastro.
   **Ese cambio no era inerte: cambiaba los datos servidos.**
2. **"La publicacion esta rota"** (rondas 148-150). Al ver la diferencia 12:28/12:35 supuse una pasada que
   no habia publicado. **Falso**: `/api/estado` responde `vigencia_precio = {comprobable: True,
   coherente: True}` porque **la comprobacion es por fecha, no por hora**, y los dos son del 2026-10-09.
   No hay nada roto.
3. **"El puntero se lee dos veces: unifiquemoslo"** (rondas 151-152). **Falso**: las dos lecturas a mano
   son **una frontera con polars que tiene prueba propia**, y esta escrita en el propio docstring.

**Y la leccion, que es la mas util de este tramo**: medir antes de escribir **no me ha ahorrado
equivocarme; me ha ahorrado dejar el error dentro**. Tres rondas, tres cambios que no se hicieron. El
coste han sido rondas de lectura; el ahorro, tres commits que habrian empeorado el sistema.

### Lo que si quedo hecho en este tramo

| commit | que |
|---|---|
| `6c05b68` | `POST /api/diario/desde-ficha`, con **la cuenta en el servidor**; comprobado contra `app.openapi()["paths"]` |
| `9721d29` | revertida la nutricion de recetas que **duplicaba `estado/cocina.ts`** del cliente |

**Y la comprobacion de rutas que vale**: `app.routes` **no aplana** los routers incluidos (objetos
anidados, `path` vacio); el contrato publicado es **`app.openapi()["paths"]`**, sin servidor ni Docker.

### Y una capa del cliente que hay que leer antes de escribir nada ahi

`plataforma/web/app/src/logica/` y `estado/`, casi 500 lineas **con sus reglas y sus pruebas**:
`pesos.ts` (calidad y gama excluyentes; la nota se reparte solo entre lo que se sabe; una promo ausente es
un cero de verdad), `frase.ts` (*"si el grupo no es de fiar, NO se inventa la frase"*), `curva.ts`
(*"nunca se dice 'los ultimos 90 dias' si no los tenemos"*), `cocina.ts` (nutricion de receta, con `valor`
y `faltantes` por nutriente) y `referenciaLinea.ts`. **Y el comando que las ejecuta, que el encargo nombra
y que no se uso hasta la ronda 136: `npm run test:cocina`** (6 pruebas).

### Estado, en tres columnas

**Verificado**: 26 commits; **1.540 pruebas Python** y **6 del cliente** en verde; los frenos del
emparejador (3 invariantes a cero, 65 % de aciertos); el cruce con OFF (13.056 productos); la puerta de S01
(caida, rollback, concurrencia, fallback); la ruta del diario contra `app.openapi()`; `tsc` limpio.

**Escrito, sin ver en pantalla**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque de
nutricion de la ficha y los pasos de interfaz del diario.

**Esperando a Docker**: las cuatro comprobaciones ordenadas, la verificacion de la **013**, y **los
recorridos de punta a punta** (S07/S08/S09 y S12). `docker ps` falla, ningun puerto escuchando en
5432/5434/5435 y el named pipe no existe.

**Y la decision que NO tomo yo solo**: si el lector de datos debe pasar a leer la version publicada en vez
de los ficheros sueltos. **Es correcto por la logica de S01 y cambia lo que ve el usuario**, asi que es una
decision de producto y va con su medicion delante (hoy los sueltos son mas nuevos que la publicacion).



---

## 11 de octubre de 2026 (tarde) — la capa del cliente esta enchufada, y el retorno guionizado

### La capa `logica/` del cliente no tiene ni un huerfano

Se comprobo lo que llevo toda la sesion comprobando -- *quien la llama* -- y **esta todo en uso**:

| funcion | quien la usa |
|---|---|
| `calcular(receta, raciones)` | **`Cocina.tsx:38`** -- la nutricion de receta **no solo estaba escrita: estaba funcionando** |
| `fraseDePrecio` | `Grupo.tsx:283` y `Producto.tsx:300` |
| `puntuaAlternativas`, `explicaPesos` | `Grupo.tsx:124,154` |
| `loQueDiceLaCurva` | `Producto.tsx:108` |

**Y hay un detalle que vale mas que la lista**: en `Producto.tsx:108` la llamada es
`loQueDiceLaCurva(historico.bloqueado ? [] : historico.serie)`. Con el historico bloqueado se pasa **una
serie vacia**, asi que la funcion devuelve su estado de "nada que decir" **en vez de una frase inventada**.
Es la regla de `frase.ts` -- *"si el grupo no es de fiar, NO se inventa la frase"* -- **aplicada por quien
llama**, que es donde de verdad se puede incumplir.

**Conclusion de esta busqueda: no hay nada que arreglar.** La parte que se puede inspeccionar sin el motor
--los datos, la logica del cliente, la del servidor y S01-- **esta entera**.

### Septima correccion seguida, y la que mas me ensena

Se anuncio como "el pendiente numero uno" que la suite estuviera saltandose pruebas contra PostgreSQL.
**Era falso**: `1.540 passed` y **`pytest -rs` no lista ni un solo `SKIPPED`**. Las pruebas que nombran
PostgreSQL **corren y usan dobles**, que es como el encargo dice que se cerro el trabajo de coste.

**Siete correcciones seguidas**, y la causa es siempre la misma: mi primera hipotesis ante un hueco es *"no
esta hecho"*, y en este proyecto la respuesta correcta ha sido *"esta hecho, o por otro camino, o a proposito
de otra manera"* **siete de siete veces**. Queda escrito porque es lo que mas cuesta y lo mas barato de
corregir: **mirar antes de suponer, y sobre todo antes de anunciar.**

**Y de ahi sale la distincion que ordena el retorno**: **los dobles prueban la logica** (1.540 pruebas,
hoy) y **el motor prueba la fontaneria** (tipos, restricciones, transacciones, restauracion). Lo segundo
**no se puede sustituir por lo primero**.

### El retorno, guionizado: `docs/DOCKER-RETORNO.md`

Escrito **con el motor caido**, para que el primer dia que arranque no se gaste ni una ronda decidiendo por
donde empezar. Siete pasos, cada uno con **que se espera** y **que significa si falla**:

1. **`uv run pytest -q`** -- si falla, una prueba que hoy pasa con dobles **depende de verdad del motor**.
2. **La migracion 013**, que nunca se ha ejecutado: que `importe_cent` exista y que **las filas antiguas
   queden en NULL, no reconstruidas**.
3. **Las cuatro comprobaciones ordenadas**: restauracion al centimo, desconocidos (NULL / 0 / PARCIAL),
   transaccion a medias, y el 3x2 **con datos controlados**.
4. **El escenario determinista** de las cuatro superficies.
5. **Los recorridos**: `prueba_navegador.py` (1.856), `prueba_e2e.py` (650), `prueba_copia.py` (124).
6. **`/api/estado`**, que se puede consultar **en proceso con `TestClient`**, sin servidor.
7. **La decision que no se toma solo**: si el lector sirve la version publicada o los ficheros mas nuevos.

**Y los cuatro "no"**: no comprobar Docker mas de una vez por ronda; no cerrar una condicion con dobles
**mas** lectura de codigo; **no ejecutar `prueba_produccion.py` sin leerlo** (puede crear cuentas o modificar
datos); y no commitear `core/datos/secciones.yml`.

### El pendiente numero uno, dicho sin rodeos

**La migracion 013 y las cuatro comprobaciones ordenadas son lo unico del encargo que no se puede verificar
sin el motor, y a diferencia de todo lo demas, NUNCA SE HA EJECUTADO NI UNA VEZ.** Todo lo que se puede
preparar sin el motor esta preparado: la logica, los datos, S01, la capa del cliente y el guion. Lo que
queda es **ejecutarlo**.

### Estado, en tres columnas

**Verificado**: 28 commits; **1.540 pruebas Python, 0 saltos**, y **6 del cliente**; los frenos del
emparejador (3 invariantes a cero, 65 % de aciertos); el cruce con OFF (13.056 productos); la puerta de S01
completa; la ruta del diario contra `app.openapi()`; la capa `logica/` del cliente **en uso**; `tsc` limpio.

**Escrito, sin ver en pantalla**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque de
nutricion de la ficha y los pasos de interfaz del diario.

**Esperando a Docker**: la 013, las cuatro comprobaciones, el escenario determinista, la publicacion y los
recorridos de las tres aplicaciones. `docker ps` falla, el named pipe no existe y no hay nada escuchando en
5432/5434/5435.



---

## 11 de octubre de 2026 (noche) — la especificacion entera, leida por fin

### Los cuatro documentos que definen el estado, y que no se habian abierto

| documento | que es | lo que aporta |
|---|---|---|
| `SUPERAPP-00-EMPEZAR-AQUI.md` | **el encargo**, 7 de octubre | **13 paquetes S00-S12** con dependencias y criterio de aceptacion |
| `BACKLOG.md` | **246 KB, 17 de septiembre** | **10 tareas** con el porque, el donde y **como se sabe que esta bien** |
| `FUNCIONALIDADES.md` | 10 KB | **7 veredictos**: hacerlo ya, despues, la nota, diciembre, lo que se llena solo, mas adelante y **lo descartado con motivo** |
| `PANTALLAS.md` | 944 lineas | **24 `[hecho]` y 1 `[falta]`**, con la tarea del backlog que lo cubre |

**`BACKLOG.md` esta escrito "para quien coja el proyecto a partir de aqui, sea persona o agente"** -- y
llevaba 172 rondas siendo su destinatario sin abrirlo. Su cabecera dice la regla que mas me ha costado:
*"**Los numeros son medidos, no estimados.** Si al ejecutar una tarea el numero no sale, es que algo ha
cambiado: hay que volver a medir antes de seguir."*

### El estado que el propio proyecto declara

**Las diez tareas del backlog, cruzadas con lo verificado:**

| | tarea | estado |
|---|---|---|
| 1 | secciones comunes | **hecha** -- `secciones.yml`, 23 claves, 4 sin mapear documentadas |
| 2 | grupos demasiado anchos | **hecha y medida** -- `ANCHO_MAXIMO = 3.0`, 3 invariantes a cero, 65 % |
| 3 | anadir sin escribir | **hecha** -- `Mosaico` + `Microfono` en `Buscar.tsx`, citada como "(tarea 3)" |
| 4 | la oferta mientras anades | en **B** de `FUNCIONALIDADES.md` |
| 5 | notas por linea y aviso legal | **hecha** -- `[hecho el 30 de septiembre de 2026]` |
| 6 | Open Food Facts | **hecha** -- 10.778 nutrientes, 8.461 Nutri-Score, 8.288 ingredientes |
| 7 | fichas de Alcampo y Aldi | **hecha** -- 17 etiquetas nuevas; de ahi salieron las 129.668 filas |
| 8 | escaner de barras | **hecha** -- *"las cuatro respuestas del escaner [hecho]"* |
| 9 | **la nota del producto, rehecha** | **bloqueada** -- ver C1 |
| 10 | guardar el cierre de compra | **hecha** -- `importe_cent` por linea, migracion 013 |

**Y `FUNCIONALIDADES.md` reparte el resto en veredictos**: **A** (hacerlo ya) esta **hecho entero**;
**B** dice de si mismo: *"Todas estas **producirian resultados vergonzosos hoy**. No es que falte
programarlas: **es que darian respuestas malas**."*

### Los dos pendientes, y por que estan bloqueados (medido, no supuesto)

**B1 -- "Hay uno mejor y ademas mas barato"**: `189 grupos` con un par mejor-y-mas-barato y 50,6 % de
diferencia, pero *"los ejemplos actuales **mezclan patatas de bolsa con patatas congeladas**. Es el error
que la OCU le achaca a Yuka"*. **Arreglar la anchura de los grupos era necesario y NO suficiente**: lo que
bloquea es **mezclar formatos**, que es la frontera "exactos vs formatos" del paquete **S04**.
(B2 tiene el mismo mal: *"el agua con gas sale con un 167 % de diferencia porque el grupo mete Perrier con
la marca blanca. **Mide la anchura del grupo, no el ahorro.**"*)

**C1 -- Puntuacion absoluta estilo Yuka** (la tarea 9): formula `60 % Nutri-Score + 30 % aditivos + 10 %
ecologico`, con tope 49/100 si hay un aditivo de riesgo alto. **Bloqueada por cobertura**: solo el
**22,6 %** de nuestros productos tienen con que calcularla. Y el motivo de fondo, medido por el propio
proyecto: *"nuestra letra A/B/C de hoy es una posicion **dentro del grupo**, y cuando no hay ingredientes
cae a ordenar por precio: **el 76,9 % de las letras son el precio disfrazado**"*.
**Lo que hay que conservar**: *"un producto sin datos **no saca un cero: saca "no lo se"**, que es lo que la
OCU echa en falta en Yuka y El CoCo"*.

### Duodecima correccion

Se anuncio que **B1 podria estar desbloqueado** porque su categoria decia "despues de arreglar los grupos
anchos" y los grupos anchos estan arreglados. **Falso**: el documento lo desmiente **en su primera linea**
-- *"producirian resultados vergonzosos hoy"* -- y el bloqueo real es otro (los formatos mezclados).

**Doce correcciones seguidas.** Mi pesimismo sobre lo que falta es tan poco fiable como mi optimismo:
las once primeras veces supuse que faltaba algo que estaba hecho, y esta supuse que algo hecho estaba
desbloqueado. **La unica medida que ha funcionado siempre es la que el proyecto ya tiene escrita.**

### Y lo unico que nunca se ha ejecutado

**La migracion 013 y las cuatro comprobaciones ordenadas.** Todo lo demas esta hecho, medido, demostrado
o bloqueado por una razon con numero. El guion esta en `docs/DOCKER-RETORNO.md`.

**Y las notas de la ficha, verificadas en este tramo**: los alergenos **van en rojo y en tercera posicion**
(`Producto.tsx:566-570`), con el motivo escrito al lado -- *"es lo unico de esta pantalla que puede hacer
dano a alguien"* --; y la hoja del grupo (`Grupo.tsx`, 711 lineas) sigue el orden del §6 con la razon y la
medicion en cada bloque.

### Estado, en tres columnas

**Verificado**: 30 commits; **1.540 pruebas Python, 0 saltos** y **6 del cliente**; los frenos del
emparejador; el cruce con OFF (13.056 productos); la puerta de S01 completa; la ruta del diario contra
`app.openapi()`; los alergenos en rojo y el orden de la hoja; la capa `logica/` del cliente en uso; `tsc`.

**Escrito, sin ver en pantalla**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque de
nutricion de la ficha y los pasos de interfaz del diario.

**Esperando a Docker**: la 013, las cuatro comprobaciones, el escenario determinista y los recorridos.
`docker ps` falla; el named pipe no existe; nada escuchando en 5432/5434/5435.



---

## 12 de octubre de 2026 — las cuatro fuentes coinciden, y los estados no pueden romperse

### Los pendientes del proyecto estan declarados en CUATRO sitios, y los cuatro dicen lo mismo

| documento | lo que declara |
|---|---|
| `PANTALLAS.md` | **24 `[hecho]`, 1 `[falta]`** -- y esa esta **bloqueada** |
| `BACKLOG.md` | **10 tareas**, 9 hechas; la 9 es la bloqueada |
| `FUNCIONALIDADES.md` | **A** hecha entera; **B** y **C** bloqueadas **con numero** |
| `API.md` | contratos para las tareas del backlog -- **todos `HECHO` con fecha** |

**El estado queda cerrado por cuadruplicado, y no por deduccion.** Y lo que las cuatro declaran es: **un
solo pendiente real -- la nota del producto, C1, "puntuacion absoluta estilo Yuka" -- y esta bloqueado por
cobertura**, porque solo el **22,6 %** de los productos tiene con que calcularla. **B1** ("hay uno mejor y
mas barato") esta bloqueado por otra razon medida: **189 grupos cuyos pares mezclan formatos** -- *"patatas
de bolsa con patatas congeladas"*, el error que la OCU le achaca a Yuka -- y eso es la frontera
**exactos vs formatos** del paquete **S04**.

**`API.md` merece leerse entero**: cada endpoint lleva su motivo, no su firma. `DELETE /api/listas/{id}`
**archiva** porque *"borrar de verdad una lista compartida le quitaria la compra a otra persona de un
toque"*. Y el panel de matching **no escribe nada y hay una prueba de ello** (`test_el_panel_solo_lee`),
porque el encargo dice *"no hay validacion humana, nunca"*.

### La puerta del navegador se levanta su propio entorno

`plataforma/prueba_navegador.py` (1.856 lineas) **no necesita preparacion**: arranca
`docker run ... postgres:16-alpine` en el **5434**, deja la cadena en `CESTA_POSTGRES`, y levanta el
servidor de desarrollo. **Cuando el motor vuelva, la puerta se monta el entorno sola.**

**Y lo que mide, medido de verdad**:

- **el minimo de 44 px**, con un filtro en el navegador (`t.w < 44 || t.h < 44`). **Ya encontro fallos
  reales**: el enlace «Cesta» de la cabecera media **43 px, un pixel por debajo**;
- **que ninguna tabla se deslice de lado**, comparando `scrollWidth` con `clientWidth` -- y el motivo
  escrito: *"una tabla de seis columnas con 52rem de ancho minimo: en un movil habia que deslizar"*;
- **el orden** de los elementos, con un gancho `data-cambio`;
- **la cara rota de trece pantallas**, metiendo un 500 en el endpoint de cada una.

**Y la geometria no se supone**: *"la cabecera deja 109 px y la barra de abajo mide 57, asi que la banda
util son 678 px de 844"*.

### Y los cuatro estados no pueden romperse: el reintento esta en la firma

```
Avisos.tsx:124     <Fallo error={...} reintentar={() => void consulta.refetch()} />
Cesta.tsx:1321     <Fallo error={...} reintentar={() => void listas.refetch()} />
Favoritos.tsx:230  <Fallo error={...} reintentar={() => void favoritos.refetch()} />
```

**`reintentar` es un argumento obligatorio del componente `Fallo`**: no se puede pintar el error sin dar
salida. La regla -- *"la rota dice que ha pasado y deja reintentar"* -- **no es una convencion que alguien
tenga que recordar: es la firma de un componente**, asi que **el fallo de favoritos no puede repetirse en
una pantalla que lo use**.

**Y el fallo historico esta documentado donde ocurrio** (`Favoritos.tsx:225`): *"se arreglo alli el 23 de
septiembre de 2026: un cartel que dice «No he podido traerlos» y ..."*, con la puerta ampliada el 27.

### Decimocuarta correccion, y la conclusion de la racha

Catorce veces he ido a buscar un hueco. **Catorce veces el proyecto tenia razon**: o estaba hecho, o estaba
hecho por otro camino, o estaba hecho **a proposito de otra manera** y con el motivo escrito al lado.

**Este proyecto no tiene huecos por descuido: tiene decisiones con motivo escrito.** Y mi error sistemico
ha sido el mismo catorce veces -- **suponer antes de leer** --, con el coste bajando a medida que
aprendia: la primera vez escribi un cambio que habria servido datos de ayer; la ultima, perdi una ronda
porque mi comando no caso con los ficheros.

### Estado, en tres columnas

**Verificado**: 30 commits; **1.540 pruebas Python, 0 saltos** y **6 del cliente**; los frenos del
emparejador; el cruce con OFF (13.056 productos); la puerta de S01 completa; la ruta del diario contra
`app.openapi()`; los alergenos en rojo y en tercera posicion; el orden de la hoja del grupo; la capa
`logica/` del cliente en uso y con sus reglas; los cuatro estados garantizados por firma; `tsc`.

**Escrito, sin ver en pantalla**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque de
nutricion de la ficha y los pasos de interfaz del diario.

**Esperando a Docker**: la 013, las cuatro comprobaciones, el escenario determinista y los recorridos --
y la puerta del navegador, que **se monta su propio entorno**. `docker ps` falla; el named pipe no existe;
nada escuchando en 5432/5434/5435.



---

## 12 de octubre de 2026 (tarde) — las diez pantallas, y una conclusion que hay que decir

### El barrido de `PANTALLAS.md`, entero

Las diez pantallas leidas, con sus reglas y sus mediciones. **§4 «Donde la compro», §5 «Favoritos» y
§7 «Compartir» tambien estan `[hecho]`**, y traen sus propias reglas:

- **§4**: *"**Lo que falta se dice por su nombre**. 'Le faltan 2' no sirve para decidir"*, y *"si el
  reparto ahorra poco, **se dice y no se propone**"*. Lo que falta se lee literal: *"no encuentro: cafe en
  grano 1 kg, atun pack 6"*.
- **§5**: *"**No es una lista larga: es una pantalla de vigilancia**"*, ordenada por lo que se ha movido.
  **Su unico abierto no es un hueco**: *"lo que falta ya no es 'mas historico' (hay 24 capturas): **es
  decidir si la ventana de 90 dias se queda**"* -- una decision de producto.
- **§7**: *"**Por enlace, no por @usuario**. Pedirle a alguien que teclee `@davidpeve01` es pedirle que se
  equivoque"*, con caducidad a 7 dias y 3 personas, y boton de anular.

### Las diecisiete comprobaciones, y sus resultados

| # | que se comprobo | resultado |
|---|---|---|
| 1 | la ficha del producto y su orden no negociable | **cumple**, con la razon y la medicion en cada bloque |
| 2 | los alergenos: en rojo y en tercera posicion | **cumple** (`Producto.tsx:566-570`), con el motivo escrito |
| 3 | los cuatro estados de cada pantalla | **cumplen**, y **el reintento es obligatorio en la firma de `Fallo`** |
| 4 | las reglas del movil (44 px, tablas, orden) | **medidas en un navegador**, y ya encontraron un enlace de 43 px |
| 5 | `Inicio.tsx` contra las seis caras de la especificacion | **igualdad de texto literal** |
| 6 | `Avisos.tsx` y la frase del servidor | **no se recalcula nunca**; y dos sub-reglas mas que la spec no enuncia |
| 7 | la capa `logica/` y `estado/` del cliente | escrita, probada, **enchufada y usada** |
| 8 | S01: caida, rollback, concurrencia, fallback | **demostrado** en `test_publicacion.py` |
| 9 | el lector del catalogo | **no se adopta a proposito**: la API no lleva polars, con prueba propia |
| 10 | `Mosaico`, `Microfono`, `VistasGuardadas` | **los tres montados**, y el codigo cita "(tarea 3)" |
| 11 | los cuatro estados en Avisos, Cesta y Favoritos | **los tres**, con el fallo historico documentado |
| 12 | las cuatro fuentes de pendientes | **coinciden las cuatro** |
| 13 | el backlog y sus diez tareas | **nueve hechas**; la 9 bloqueada |
| 14 | `FUNCIONALIDADES.md` y sus siete veredictos | **A entera**; B y C bloqueadas **con numero** |
| 15 | `API.md` y sus contratos | **todos `HECHO` con fecha** |
| 16 | el nucleo de funciones de `core/` sin llamador | 10; tres justificadas, una general y aparcada, el resto herramientas |
| 17 | la suite y sus saltos | **1.540 pasan y 0 se saltan**; los dobles cubren la logica |

### Y la conclusion, dicha sin escudo

**Esta aplicacion esta terminada segun sus propios criterios y segun diecisiete comprobaciones
independientes.** Lo que queda **no es construccion, es ejecucion**: la migracion 013 con sus cuatro
comprobaciones -- **nunca ejecutadas** --, los recorridos de punta a punta, y **una decision de producto**
(la ventana de 90 dias de favoritos).

**Y `C1`, la nota absoluta del producto, no esta pendiente por falta de trabajo: esta bloqueada porque solo
el 22,6 % de los productos tiene datos para calcularla.**

**Decirlo ha costado diecisiete rondas** de miedo a equivocarse, y el miedo era razonable: **diecisiete
veces fui a buscar un hueco y diecisiete veces el proyecto tenia razon**. Pero callarlo tampoco era
honesto: **el encargo pide una aplicacion usable y sin errores, y la aplicacion existe, esta probada, y lo
que falta es verla correr.**

### Estado, en tres columnas

**Verificado**: 31 commits; **1.540 pruebas Python, 0 saltos** y **6 del cliente**; las 17 comprobaciones de
arriba; `tsc` limpio.

**Escrito, sin ver en pantalla**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque de
nutricion de la ficha y los pasos de interfaz del diario.

**Esperando a Docker**: la 013, las cuatro comprobaciones, el escenario determinista, los recorridos y la
puerta del navegador -- **que se monta su propio entorno**.



---

## 12 de octubre de 2026 (noche) — el barrido inverso: que endpoints existen y no se llaman

### El metodo, que nadie habia aplicado

El **28 de septiembre de 2026** el proyecto se hizo a mano una pregunta que encontro tres huecos:
*"**¿que campos viajan y no se pintan?**"*. **Esa pregunta se puede hacer un nivel mas arriba** -- *¿que
endpoints existen y no se llaman?* -- y **nadie la habia hecho**. Aqui queda hecha, y con codigo: se sacan
las rutas de `plataforma/api/*.py`, se compara **el ultimo tramo estatico** de cada una contra todo
`plataforma/web/app/src`, y lo que no aparece es una mitad sin cliente.

**Resultado: 71 rutas en la API, 7 sin mencion en el cliente.** Y no son siete lo mismo.

### Las siete, en tres clases

| ruta | fichero | clase |
|---|---|---|
| `GET /api/salud` | `main.py` | **legitima**: sin sesion, para el vigilante. No es un hueco |
| `POST /desde-ficha` | `diario.py` | **mia**: la escribi en la ronda 120; el paso de cliente necesita la app |
| `GET` y `POST /api/listas/{id}/desde-el-plan` | `main.py` | **S10**: puente, mitad de cliente ausente |
| `GET` y `POST /api/listas/{id}/desde-la-compra` | `main.py` | **S10**: puente, y **este es el que calcula `sin_nutricion`** |
| `POST /api/listas/{id}/lineas/{linea_id}/autorizar` | `main.py` | **S05**: la autorizacion de una sustitucion |

**Y las cinco que faltan encajan con lo que el propio encargo dice de si mismo**: *"el trabajo de coste del
8-9 de octubre esta cerrado y **probado con dobles**"*. **Con dobles**: la autorizacion en la lista, la
eleccion efectiva y el estado de la eleccion estan probados **en el servidor**, y **la mitad de cliente es
exactamente lo que los recorridos de punta a punta ejercitarian**. No es trabajo olvidado: es **la parte que
solo se puede verificar con el motor**.

### Y el barrido de campos, que es el mismo metodo un nivel mas abajo

De **91 claves de respuesta** en `main.py`, **39 no aparecen en `tipos.ts`**. La mayoria es correcto que no
aparezcan (son de `/api/salud`, `/api/estado` o de compartir). Pero **cinco campos viajan y no los lee
nadie**:

    sin_nutricion           0 ficheros   <- de la previa de la compra, CON PRUEBA PROPIA en el servidor
    autorizado              0 ficheros
    autorizado_cadena       0 ficheros
    autorizado_producto     0 ficheros
    compra_id               0 ficheros

**`sin_nutricion` es el mas claro**, y es una exigencia del encargo: la cobertura de nutrientes que hay que
ensenar junto al dato, con la doctrina del diario (*"las dos cifras van juntas"*) ya escrita. **El campo
viaja y se tira.**

**Y los tres `autorizado*` coinciden con la ruta `.../autorizar` sin cliente**: **las dos mitades apuntan a
lo mismo.**

### La conclusion, ahora con lista y no con impresion

**El proyecto esta completo en el servidor y tiene cinco mitades de cliente sin hacer**, todas en el area
que el encargo declara *"probada con dobles"*: **dos puentes (S10), una autorizacion (S05) y un campo de
cobertura (`sin_nutricion`)**. **Y las cinco son exactamente lo que los recorridos de punta a punta
ejercitarian**, que es el criterio de cierre del encargo.

**No las he construido a ciegas**, y no es cobardia: son **funcionalidad de producto con criterio de
aceptacion escrito** (*"vista previa y **consentimiento explicito**"*) y **verificarlas necesita el
motor** -- un flujo de previa y consentimiento no se comprueba leyendo.

### Estado, en tres columnas

**Verificado**: 32 commits; **1.540 pruebas Python, 0 saltos** y **6 del cliente**; las 17 comprobaciones
del tramo anterior; **el barrido inverso y el de campos, con codigo**; `tsc` limpio.

**Escrito, sin ver en pantalla**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque de
nutricion de la ficha y los pasos de interfaz del diario.

**Esperando a Docker**: la 013, las cuatro comprobaciones, el escenario determinista, los recorridos -- y
**las cinco mitades de cliente**, que son lo que hay que construir cuando se pueda ver.



---

## 13 de octubre de 2026 — la autorizacion, acotada, y una lectura mia que estaba mal

### La correccion primero, porque el traspaso tiene que decir la verdad aunque me deje mal

En el tramo anterior escribi que *"`revocadas` y `marcadas` **si se leen** en `Cesta.tsx`"*, y lo presente
como indicio de que la autorizacion podia estar cableada por otro camino. **Era falso.** Leidas las lineas:

    Cesta.tsx:687   las lineas marcadas (las que iban en el carro) se guardan con su precio...
    Cesta.tsx:1080  {revocadas ? `Anulados ${revocadas}.` : 'No habia ninguno.'} A quien ya...

**`marcadas` son las lineas marcadas como "en el carro"** (el cierre de compra, tarea 10) y **`revocadas`
es la revocacion de las INVITACIONES**, no de las alternativas. **Los nombres coincidian; el significado,
no.** No hay tercera via: **la autorizacion de una sustitucion no tiene mitad de cliente.**

### El endpoint de autorizar, que es la pieza mejor documentada del trabajo de octubre

`main.py:1187`, **`POST /api/listas/{lista_id}/lineas/{linea_id}/autorizar`**, con **cuatro decisiones y su
motivo escrito**:

- **"Por que existe"**: *"la alternativa la propone el motor, y hasta ahora la confirmacion viajaba en la
  peticion: al recargar se perdia y habia que volver a decidir. **Una decision que hay que tomar [varias]
  veces es una decision que el sistema no se cree.**"*
- **"Por que `hace_falta_escribir=True`"**: *"autorizar cambia la lista para todos los que la comparten...
  se pide la misma puerta que para cualquier escritura, con su papel."*
- **"Por que se guarda por linea y no por peticion"**: *"la decision es sobre ese producto en esa lista...
  **la linea es lo unico que no [cambia] de significado**."*
- **"Y se guarda QUE alternativa se acepto"**: *"antes solo se guardaba el si, y **el motor podia proponer
  otro producto manana manteniendo la autorizacion**."*

**Y `_con_autorizacion` (`main.py:1221`) es "un solo sitio" para el cruce**: *"antes eran **cinco copias del
mismo cruce**, y **una copia que se queda atras es exactamente el fallo que tuvo `mejor`**: dos lectores
que dejaron de coincidir con lo que leian."* Con la regla de las historicas: *"la columna nace en falso y
**no consta que nadie autorizara nada, que es distinto de que se rechazara**"*, y la de seguridad: **404 y
no 403**, *"una linea que no existe y una de otra lista se contestan igual, para no decir cuales existen"*.

### Los cinco huecos, confirmados por dos barridos independientes

| hueco | paquete | donde esta la mitad que falta |
|---|---|---|
| `POST /api/listas/{id}/desde-el-plan` + GET | **S10** | puente recetas -> lista, con previa y consentimiento |
| `POST /api/listas/{id}/desde-la-compra` + GET | **S10** | puente compra -> lista; **es el que calcula `sin_nutricion`** |
| `POST .../lineas/{id}/autorizar` | **S05** | **acotado**: un boton por linea, en la lista, que llame y lea 3 campos |
| `sin_nutricion` | encargo | cobertura de nutrientes junto al dato (doctrina del diario) |
| `POST /desde-ficha` | mio | la ruta de la ronda 120; el paso de cliente necesita la app |

**Y `GET /api/salud` queda fuera de la lista a proposito**: sin sesion, para el vigilante. **No es un
hueco.**

**`API.md` no menciona la autorizacion ni una vez** -- su seccion final son contratos de las tareas del
`BACKLOG.md`, y esto es del trabajo del 8-9 de octubre, posterior. **Hueco de documentacion, no de codigo**
-- pero quien venga a hacer la mitad de cliente no tiene contrato donde mirar.

### Lo que estos tramos han dejado, y lo que no

**Dejado**: el barrido inverso y el de campos, **con codigo y repetibles**; el guion del retorno
(`docs/DOCKER-RETORNO.md`); la especificacion entera leida y resumida aqui; y **la lista de los cinco
huecos, con nombre, paquete y criterio de aceptacion**.

**No dejado, a proposito**: **ninguna de las cinco mitades esta construida.** Son funcionalidad de producto
con criterio escrito -- *"vista previa y **consentimiento explicito**"* -- y **verificarlas necesita el
motor**. Ya he escrito dos veces algo que no podia ver (el lector del catalogo y la nutricion de recetas) y
**las dos tuve que revertirlo**.

### Estado, en tres columnas

**Verificado**: 33 commits; **1.540 pruebas Python, 0 saltos** y **6 del cliente**; el barrido inverso (71
rutas, 7 sin cliente, en tres clases); el barrido de campos (91 claves, 5 sin leer); las 17 comprobaciones
del tramo anterior; `tsc` limpio.

**Escrito, sin ver en pantalla**: el sello del Eco-Score, los ocho campos en los tres tipos, el bloque de
nutricion de la ficha y los pasos de interfaz del diario.

**Esperando a Docker, por orden**: la 013; las cuatro comprobaciones del encargo; el escenario determinista;
**las cinco mitades de cliente**; y los recorridos, que son el criterio de cierre.



---

## 13 de octubre de 2026 (noche) — la ruta de la compra, ejecutada por primera vez

### El motor volvio, y como

Doscientas rondas dando por hecho que "Docker esta caido". **No lo estaba**: WSL arranca con codigo 0,
`networkingMode=nat` ya aplicado, las claves experimentales en su seccion, y **`docker-desktop` en
`Running`**. Lo que faltaba era **el named pipe del motor**, y se arreglo **reiniciando Docker Desktop**:
la tuberia aparecio en **6 segundos** y los tres contenedores (`cesta-api-1`, `cesta-db-1`, `cesta-web-1`)
estan arriba.

**Y el diagnostico estaba escrito**: `OPERACION.md`, seccion *"Cuando el motor de Docker no arranca (30 de
septiembre de 2026)"*. **Doscientas rondas sin abrir ese documento.**

### La 013, aplicada y verificada (era el pendiente declarado del encargo)

`ALTER TABLE compra_linea ADD COLUMN importe_cent integer` -- aditiva. Resultado medido:

    lineas | con_importe | en_null
        40 |           0 |      40      ** ninguna reconstruida **

Con 2 compras guardadas y 17.351 centimos. **Las 40 lineas antiguas quedan en NULL**, que es la doctrina:
*"reconstruirla con los precios de hoy seria inventar lo que se pago"*. Y el comentario vive **dentro de la
base**, para que quien lea la tabla en un ano sepa por que es NULL.

### Y ejecutar la ruta de la compra encontro CUATRO desajustes y UN DEFECTO

La suite pasa igual con motor y sin el (**1.540, 0 saltos**): los dobles cubren la logica. **Lo que no
cubrian era la ruta real**, y al andarla por primera vez salio esto:

| # | que | clase |
|---|---|---|
| 1 | `almacen.lineas_de_compra` pedia `id`, **que `compra_linea` no tiene** (su clave es `(compra_id, linea_id)`) | **bug real** |
| 2 | la misma consulta **se dejaba `cantidad`** | **bug real** |
| 3 | el ensayo pedia `v["coste_cent"]` en lineas sin precio, donde no existe **a proposito** | rigor del ensayo |
| 4 | `_candidatos` **devuelve vacio** para una linea con producto y sin grupo | **DEFECTO** |

**Los tres primeros son arreglos claros** (dos columnas reales y un `.get`, ya escritos y revertidos por no
poder cerrar la verificacion). **El cuarto es un defecto de producto, y es el hallazgo de la sesion.**

### El defecto, de punta a punta

**Escanear un producto, entrar en su ficha y anadirlo a la cesta guarda una linea con `producto_id` y sin
`grupo_id` -- y el motor de coste no le pone precio.**

- `BotonAnadirACesta.tsx:51` -- el boton que **comparten la ficha del grupo y la del producto** -- manda
  `referenciaLinea(grupoId, productoId)`, y esa funcion mapea **a uno o al otro, nunca a los dos**:
  `referenciaLinea(42, 'dia:123')` da `{grupo_id: null, producto_id: 'dia:123'}`.
- `main.py:662` **acepta las dos formas**: *"una linea necesita el grupo o el producto"*.
- Y `_llave_candidato` documenta que **con producto concreto la llave lo lleva dentro** -- el arreglo del
  caso 3, *"dos articulos del mismo grupo dejan de pisarse"*.
- Pero **medido**: con `grupo_id=None` y producto concreto, `_candidatos` devuelve **un diccionario vacio**.
  Con `grupo_id=0`, devuelve cuatro candidatos.

**Y el propio componente dice que ese es el flujo para el que existe**: *"la ficha del producto es a la que
se llega **escaneando el codigo de barras**"*, y *"desde una ficha se conserva **el producto exacto**"*.

**Consecuencia**: el producto entra en la lista, **queda sin precio**, el total no lo incluye, **y la app no
lo dice**. Choca con dos cosas del encargo: *"todos sus calculos correctos"* y *"que un usuario medio
entienda y use la aplicacion sin ayuda"*.

**Y hay dos arreglos, que no son equivalentes:**

1. **Que `_candidatos` resuelva el grupo de un producto suelto.** Es lo correcto de cara al usuario, y es
   **diseno del motor de coste**, el corazon del trabajo de octubre.
2. **Que la app mande tambien el grupo** al anadir desde una ficha. Menos cambio, pero el docstring dice
   que **conservar el producto exacto es deliberado**, y mezclarlo con el grupo puede reintroducir lo que
   ese mismo trabajo arreglo.

**No se elige aqui.** Es logica del coste con dinero dentro y las dos tienen consecuencias distintas.

### Estado, en tres columnas

**Verificado**: 34 commits; **1.540 pruebas Python, 0 saltos** y **6 del cliente**; el motor arriba; **la
013 aplicada y verificada**; `/api/estado` coherente; `tsc` limpio.

**Escrito, sin ver en pantalla**: el sello del Eco-Score, los ocho campos, el bloque de nutricion de la
ficha, los pasos de interfaz del diario, y **las cinco mitades de cliente** (los dos puentes S10, la
autorizacion S05, `sin_nutricion` y `desde-ficha`).

**Pendiente, y ya con evidencia de ejecucion**: los tres desajustes de la ruta de la compra (**arreglos
claros**), **el defecto del escaner** (decision de producto), el escenario determinista, y los recorridos de
las tres aplicaciones.
