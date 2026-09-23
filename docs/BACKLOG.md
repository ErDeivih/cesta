# Cesta — trabajo pendiente, listo para ejecutar

Escrito el 17 de septiembre de 2026 para quien coja el proyecto a partir de
aqui, sea persona o agente. Cada tarea trae **por que**, **que hay que hacer**,
**donde**, y **como se sabe que esta bien**.

Los numeros son medidos, no estimados. Si al ejecutar una tarea el numero no
sale, es que algo ha cambiado: hay que volver a medir antes de seguir.

---

## El orden, de un vistazo

    1   Secciones comunes                  M    desbloquea 4 cosas. EMPEZAR AQUI.
    2   Grupos demasiado anchos            M    desbloquea otras 3. Medir siempre.
    3   Anadir sin escribir                S    mosaico + voz
    4   La oferta mientras anades          S    la pieza dificil ya esta hecha
    5   Notas por linea y aviso legal      XS   dos ratos
    6   Traer de Open Food Facts           S    nutrientes, categorias, sellos
    7   Sondear fichas de Alcampo y Aldi   XS   una ejecucion y una decision
    8   Escaner de codigo de barras        M    la funcion diferencial
    9   La nota del producto, rehecha      M    arregla un problema de raiz
    10  Guardar el cierre de compra        S    barato ahora, imposible despues

Las tareas 1 y 2 van primero porque **bloquean a las demas**, no porque sean las
mas vistosas. La 10 va pronto aunque no se note: sin ella, en diciembre no habra
historial que mirar.

`docs/FUNCIONALIDADES.md` tiene el catalogo entero con veredicto, incluido lo
descartado y por que, para no volver a discutirlo.

---

## 0. Rehacer el matching y la interfaz (encargo del 22 de septiembre)

**Por que.** Hay un encargo nuevo del dueno: migrar la interfaz a un stack
especializado y arreglar el matching, **sin ninguna validacion humana**. El plan
maestro es `docs/PLAN-UI-MATCHING.md` y su informe es
`docs/DIAGNOSTICO-MATCHING.md`.

### La interfaz nueva: donde esta, y que le queda (mirar esto primero)

0. **LA INTERFAZ NUEVA YA SE PUEDE SERVIR, y aun le falta cola.** El `app.js`
   viejo tiene cinco vistas: `buscar`, `lista` (la lista de la compra),
   `favoritos`, `panel` y `ajustes`, con login. La nueva tiene buscador, grupo,
   ficha, escaner, cesta, favoritos, ajustes, panel y panel de matching. Las
   pantallas ya estan todas, y esa fue justo la trampa: **una pantalla no es una
   funcion.** Auditado el 23 de septiembre leyendo `app.js` entero (1.758 lineas)
   contra todo `app/src`, y **vuelto a contar al cerrar el dia**: la interfaz
   nueva tiene **13 operaciones de escritura** contra **14** de la vieja. Los tres
   bloqueantes que salieron de aquella auditoria -- escribir en la lista, el
   registro y compartirla -- estan resueltos. Lo que queda escrito abajo, al
   final de esta seccion, se puede escalonar.

   Servir `web/dist` hoy **todavia quita funciones** (los avisos de precio, la
   escritura sin cobertura, tres pantallas del panel y darme de baja). Por eso
   `plataforma/docker-compose.yml` trae la linea puesta (`./web/dist:/srv:ro`) con
   un aviso encima: es el destino, pero cambiarla en produccion es una decision
   del dueno y no un paso automatico. Volver atras mientras tanto es poner
   `./web:/srv:ro`.

   Lo que falta, por orden de valor:

   1. ~~**La lista de la compra**~~ — **a medias, y hay que decirlo asi** (23 sep):
      estan el login, la lista y donde comprarla (`src/paginas/Cesta.tsx`), y las
      rutas de la API ya existian. Pero **no se puede anadir nada**: el front
      nuevo solo llama a `GET /listas`, `GET /listas/{id}` y
      `GET /listas/{id}/donde`. Medido con `Select-String` sobre
      `src/api/*.ts`: **0 llamadas de escritura**. La API tiene
      `POST /listas/{id}/lineas` y `PATCH /listas/{id}/lineas/{id}` desde el
      principio (`plataforma/api/main.py:390` y `:398`) y el `app.js` viejo las
      usa (`app.js:628` y `:655`). O sea: la pantalla sirve para mirar una lista
      que hayas hecho en la interfaz vieja, no para hacerla. Esto no se ve mirando
      la pantalla, porque una lista vacia y una lista que no se puede llenar se
      parecen mucho. **Es el hueco que mas se nota**: la lista es el caso de uso
      numero uno.
   2. ~~**El login**~~ — **hecho** (22 sep), va con la cesta: la API usa sesion
      por cookie y un solo origen, asi que funciona sin tocar CORS.
   3. ~~**Favoritos**~~ — **hecho** (22 sep): la pantalla
      (`src/paginas/Favoritos.tsx`) y el boton de guardar en la ficha del grupo
      (`src/componentes/BotonFavorito.tsx`). El boton **no se pinta si no hay
      sesion**: uno que al pulsarlo pida entrar es una promesa que no se puede
      cumplir en el pasillo, con una mano.
   4. ~~**Ajustes**~~ — **hecho** (23 sep): `src/paginas/Ajustes.tsx` y
      `src/api/ajustes.ts`, sobre `PUT /api/preferencias`, que ya existia.

   ### Lo que sigue faltando, auditado linea a linea (23 sep)

   Cada linea es una funcion que el `app.js` viejo tiene y la interfaz nueva no,
   con el sitio exacto. Ordenado por lo que se nota al usarla en la tienda.

   **Bloquean servir `dist`:**

   1. **Escribir en la lista** (en curso, 23 sep): anadir, tachar, cantidad,
      borrar. La API lo tiene desde el principio (`main.py:390` y `:398`) y el
      viejo lo usa (`app.js:628`, `:655`).
   2. **Pintar las lineas de la lista.** No es que no se puedan tocar: es que
      **no se pintan**. `Cesta.tsx:213-217` solo usa `detalle.data.lineas.length`
      y `tachado_en`; el campo `nombre_visto` (`tipos.ts:414`) no se renderiza en
      ningun fichero de `app/src`. Se entra, se ve un total, y no hay lista.
   3. **Crear la lista "Casa" si no existe.** `Cesta.tsx:155-164` dice "se crean
      desde el movil o con la interfaz antigua": manda a la interfaz vieja. El
      viejo la crea sola (`app.js:448-455`) con `POST /listas`.
   4. ~~**El registro**~~ — **hecho** (23 sep): `registrarse()` en
      `src/api/cesta.ts` y el formulario de alta en `src/paginas/Cesta.tsx`, que
      alterna con el de entrar (`POST /api/registrarse`, `main.py:83`, que ya
      existia y **entra sola** en la misma respuesta). Comprobado contra la API
      viva por Caddy: 201 con `Set-Cookie`, `GET /api/yo` con esa cookie devuelve
      la persona, repetir el alta da 409 y un usuario de dos letras da 422. La
      cuenta de prueba se borro despues (0 usuarios de prueba). Las reglas no se
      duplican en el front: se ensena el texto de la API.
   5. ~~**Compartir la lista**~~ — **hecho** (23 sep): el enlace de invitacion,
      quien esta dentro, compartir por nombre de usuario y anular, en la seccion
      **Compartir** de `src/paginas/Cesta.tsx` (solo la ve quien creo la lista), y
      la ruta `/unirme/:codigo` en `src/paginas/Unirse.tsx`, que es la que devuelve
      la propia API. El codigo **no se guarda**: vive en la barra de direcciones,
      porque un enlace caducado guardado se aplicaria solo la proxima vez que
      alguien abra la aplicacion. Con esto **los tres bloqueantes estan
      resueltos** y lo que queda se puede escalonar.
   6. **Escribir sin cobertura**: cola local + `POST /listas/{id}/sincronizar`, y
      leer la lista sin red. El viejo funcionaba con el PC de casa apagado
      (`app.js:39-47, 63-80, 476-484`); el nuevo depende de `GET /listas/{id}` y
      sin red no ensena nada. En `docs/APP.md` esto es el paso 7 del orden de
      construccion, asi que **se puede escalonar**, pero hay que decidirlo.

   **Se pueden escalonar, pero que sea decidido y no por omision:**

   7. **Avisos de precio**: crear ("cuando este mas barato que nunca en 90 dias",
      "cada vez que baje", umbral), ver los que han saltado y quitarlos
      (`GET/POST/DELETE /api/alertas`, `main.py:528, 542, 552`). Cero
      coincidencias de `alertas` en `app/src`. Era lo unico de Favoritos que
      avisaba de algo.
   8. **Tres pantallas del panel**: `GET /indice` (`app.js:796-920`),
      `GET /posicion` (`app.js:925-996`) y `GET /ofertas-dudosas`
      (`app.js:1110-1156`), mas el **filtro del panel por cadenas cercanas**:
      `Panel.tsx:488` llama `useBajadas(dias, subidas, [])` con la lista vacia y
      ninguna pestana lee `cadenas_cerca`.
   9. **"Darme de baja"**: falta el boton en Ajustes (`DELETE /api/yo`,
      `main.py:617`; el viejo lo tiene con confirmacion por usuario,
      `app.js:1571-1603`). **La API ya funciona**: hasta el 23 de septiembre
      respondia **500** para quien hubiera anadido una linea a una lista suya,
      porque `lista_linea.anadido_por` era la unica clave ajena del esquema con
      `ON DELETE RESTRICT` y PostgreSQL la comprueba antes de que actue el
      CASCADE. Arreglado en `plataforma/sql/005_borrarse_del_todo.sql` (la clave
      pasa a `SET NULL`, como ya estaba `tachado_por`) y comprobado contra la API
      viva: 500 -> 200. Sin eso, poner el boton habria sido poner un boton que
      revienta.
   10. **Interruptor "repartir entre dos tiendas"** en Ajustes (`max_tiendas=1`;
      el viejo en `app.js:1413-1418`), y el desglose "N en CADENA" del reparto
      (`app.js:718-719`).
   11. **Campos de la ficha de producto** que ya vienen en los tipos y no se
      pintan: `certificados` (`tipos.ts:90`), `peso_variacion_pct`
      (`tipos.ts:105`, "al peso: ronda los N g y puede variar un X %") y
      `distintivo` (`tipos.ts:106`, "la cadena dice"). Y la tabla de nutricion
      (`Producto.tsx:352-366`) pinta la clave cruda de la API
      (`energia_kj`, `saturadas`...) sin nombre legible ni unidad; el viejo la
      traducia y la ordenaba (`app.js:1734-1748`).
   12. **Detalles menores**: sin ejemplos pulsables en el buscador
      (`app.js:284-295`), sin contador de lo que falta por coger en la barra de
      abajo (`app.js:507-509`), el estado vacio del buscador no distingue "nada
      con esa palabra" de "nada con los filtros" (`app.js:325-332`), y pulsar
      "Buscar" en la barra de abajo borra la busqueda porque el enlace es `to="/"`
      sin query (`componentes/Nav.tsx:21`).

   **Lo que la nueva tiene y la vieja no** (no es paridad, es ir por delante), por
   si alguien se plantea volver atras: buscador con orden por columna, numero de
   resultados y limite 40/80/120; vistas guardadas de filtros; ficha de grupo en
   pagina propia con columnas por cadena y pesos ajustables; chispa de historico
   por producto; escaner de codigo de barras; penalizacion y explicacion del
   emparejamiento; y el panel de matching.

   La barra de abajo del movil tiene cuatro sitios — buscar, cesta, escaner y
   panel — y el matching paso a estar dentro del panel: la lista de la compra es
   a lo que se va en la tienda, y el matching se mira en casa.

1. ~~**Reconstruir la imagen de la API**~~ — **hecho** (23 sep). Medido contra
   `http://127.0.0.1:8080`, la misma matriz de rutas antes y despues:

       /api/grupo/11580          500  ->  200  (53.248 B)   el fallo vivo
       /api/panel/matching       404  ->  200  (10.278 B)
       /api/ean/8412345678905    404  ->  200
       /api/buscar?q=leche       200  ->  200  (1.303 -> 1.353 B: +`marca`)
       las otras 15 rutas        200  ->  200  sin cambios

   Lo del 500 no era una tarea de limpieza: **la ficha de grupo estaba rota en
   produccion** por el `TIMESTAMP WITH TIME ZONE` de DuckDB (necesita `pytz`).
   Comprobado despues: `marca` en 3 de 3 resultados de busqueda y `producto_id`
   en 22 de 22 productos del grupo 11580.
2. ~~`/api/buscar` no devuelve `marca`~~ — **hecho** (22 sep).
3. ~~`serie` no dice de que producto es cada punto~~ — **hecho** (22 sep); el
   front ya pinta la chispa del historico siempre.
4. **El boton de camara del escaner no esta probado en un movil real.** Lo
   verificado es que se esconde solo cuando no hay `BarcodeDetector`.
5. **`metodo` no sabe decir `vector`, y el canal de vectores se pierde.** Medido
   el 23 sep sobre la ultima pasada: 22.705 filas = 21.625 pares distintos (1.080
   repetidos: el mismo par por EAN y por nombre), `metodo` vale `ean` 1.761 veces
   y `nombre` 20.944, **`vector` ninguna**. No es un fallo de los datos:
   `enlaces()` recorre los tres canales pero devuelve `(i, j, puntuacion, nivel)`
   sin el canal (`core/matching.py:632-678`), y `core/equivalencias.py:105`
   rellena `metodo` a partir de `nivel`. Asi que hoy **no se puede ver en gold
   que pares aporto el canal de vectores**, que es la pregunta de la Fase 3: se
   sabe por la medida de `--medir`, pero no par a par. Arreglarlo es devolver el
   canal desde `enlaces()` y arrastrarlo, o sea tocar la firma del nucleo del
   emparejador con 34 pruebas y la tarea diaria de las 06:00 detras: no se hace a
   la carrera al final de una sesion. El detalle, en
   `docs/DIAGNOSTICO-MATCHING.md` (§22).
6. **El canal de vectores: medido entero, y **apagado** porque rompe la asignacion.**
   (23 sep.) El coste, que era el primer obstaculo, esta resuelto: `candidatos()` lee
   los vectores en SQL en vez de traerlos a Python (antes no terminaba en 62
   minutos; ahora el catalogo entero son **239,9 s y 270 MB**). Y se encendio, se
   midio, y se volvio a apagar. Los dos lados, sobre el mismo catalogo (misma
   huella):

       metrica                    sin vectores   con vectores   diferencia
       enlaces                          22.705         26.703        +3.998 (+18 %)
       grupos comparables                7.992          8.394          +402 (+5 %)
       productos comparables            22.693         24.823        +2.130 (+9,4 %)
       calidad asignada                 12.338         14.153        +1.815 (+14,7 %)
       identicos                         6.605          8.328        +1.723
       recall de --medir                 65 %           73 %
       ---------------------------------------------------------------- lo que rompe
       conflictos de asignacion              0            861
       peor caso (parejas de un producto
         en la misma cadena)                 2              3

   **El encargo pide cero conflictos de asignacion y con el canal puesto hay 861**,
   con productos emparejados con tres productos de la misma cadena. Contado sobre el
   `equivalencia.parquet` de las dos pasadas.

   La causa: `enlaces()` da al canal de vectores **su propio reparto hungaro y su
   propio juego de `ocupados`** (`core/matching.py`, `for canal in ("marca",
   "equivalente", "vector")`), asi que el 1-a-1 se respeta dentro del canal y no
   entre canales. Los dos del nombre nunca produjeron un conflicto; el tercero si.

   **Que hay que hacer antes de encenderlo**: que sus candidatos pasen por el mismo
   reparto y el mismo `ocupados` que los otros dos. Y despues volver a medir **las
   dos columnas**, no solo la de arriba: un canal que sube el recall rompiendo la
   asignacion no es una mejora, es otro emparejador. Todo el material para
   comprobarlo esta ya: `data/debug/_conflictos.py` cuenta los conflictos de una
   pasada a partir de su `equivalencia.parquet`, y `--medir --comparar-vectores`
   (992 s) da el recall.

7. **Los ejes contradictorios: el instrumento ya existe, y el catalogo saca 54.**
   (Encargo del 22 sep, bloque 1.) Lo pidio la revision de Claude y es lo primero
   por valor: el reparto hungaro es 1-a-1 **por par de cadenas**, pero `agrupar()`
   une por **componentes conexas**, asi que basta que en un par se una *entera* con
   *sin lactosa* y en otro *sin lactosa* con *desnatada* para acabar con las dos
   juntas **sin que ningun enlace individual este mal**.

       grupos                                    37.681
       con algun eje contradictorio                  54    <- la barra pide CERO
       grupos de 11 o mas productos                  74    <- la barra pide < 30
       de esos, con eje contradictorio                5

   Los peores, hoy: el 2532 (43 productos, `virgen` con `virgen extra`), el 294 (34,
   `oliva suave` con `orujo`), el 8087 (13, con y sin azucar), el 3684 (13, blanco
   con integral) y el 1116 (11, tres valores de aceite).

   El instrumento es `core/atributos.py` (los ejes que **el nombre declara**) y se
   mide con `uv run python -m projects.cesta.ejes [--peores N]`. Dos reglas que no
   se pueden cambiar sin romperlo:

   - **El margen de precio NO es el cuchillo.** `core/comparacion.py` documenta
     ahorros reales de 28x entre marca blanca y marca (preservativos, cerveza,
     tampones): cortar por margen borraria justo los hallazgos que esto existe para
     encontrar. El margen detecta; **el atributo declarado en el nombre** corta.
   - **Si uno de los dos no declara nada, no bloquea.** No es tolerancia: es
     ausencia de prueba. Un nombre que calla no afirma que sea igual.

   Consecuencia de esa segunda regla, y hay que tenerlo dicho: **el grupo de las 84
   cervezas no lo caza esto**. Nadie escribe "con alcohol" en una cerveza, asi que
   el eje del alcohol solo ve a los que dicen "sin alcohol" y nunca hay dos valores.
   Para ese caso hace falta la **comprobacion de cohesion contra el medoide**, que
   es el mismo bloque del encargo.

   **Y la segunda dimension, que no estaba en ningun diagnostico: el pack no es la
   unidad.** El grupo mezcla una botella de 1,5 l con un pack de 6x1,5 l. Ahi **nadie
   se contradice** (todas son agua de 1,5 l) y el precio por litro se compara bien:
   el problema es que "donde compro agua" acaba recomendando nueve litros frente a
   uno y medio. Medido con `unidades_pack`:

       grupos que mezclan un pack con sueltas        615
       de esos, de 11 o mas productos                 21

   Y los ejemplos de la revision salen exactos: el grupo **444** con unidades [1, 6]
   y el **6182** con [1, 6, 12, 18]. Ademas, **el instrumento del pack caza lo que el
   de los ejes no ve**: el grupo de las 84 cervezas es [1, 12], porque nadie escribe
   "con alcohol" en una cerveza y el eje nunca llega a tener dos valores. Los dos
   medidores son complementarios, y hay una prueba que lo fija.

   Queda hecho aqui lo que se puede hacer sin tocar el emparejador: medir. **Partir
   los grupos** (por eje y por pack, descartando los que no declaran) y **la cohesion
   contra el medoide** son el paso siguiente. El trinquete esta en
   `tests/test_atributos.py`: techos 54, 74, 615 y 21, y si bajan se bajan en el
   mismo commit.

### Como se comprueba el encargo, y cuanto sale hoy

Las cinco condiciones van **juntas a proposito**: lo que paso el 22 de septiembre fue
subir un numero mientras bajaba el otro (el recall del emparejador subio y los grupos
se fundieron peor), y mirando una sola columna eso se ve como una mejora.

    condicion                                   comando                                        hoy
    pruebas verdes                              uv run pytest -q && uv run ruff check .        736 pasan, 2 fallan (ajenos)
    --medir >= 57 %                             uv run python -m projects.cesta.emparejar \
                                                  --medir                                      65 %   CUMPLE
    cero grupos con eje contradictorio          uv run python -m projects.cesta.ejes         0    CUMPLE
    menos de 30 grupos de 11+ productos         (el mismo comando)                            0    CUMPLE
    las cinco cadenas con bronze del mismo dia  ver `docs/ESTADO.md`                         CUMPLE (23 sep)
    cadena repetida de la misma sin EAN         `projects.cesta.ejes`                         0    CUMPLE

**El `--medir` esta medido CON las dos redes puestas**, que era la duda que quedo al
ponerlas: cortar por cadena repetida y por eje contradictorio podia llevarse pares
ciertos por delante. No se los llevo -- **1.174 de 1.813 pares ciertos, el 65 %**, en
420 s sobre el catalogo de hoy (52.417 productos). Y el numero que de verdad mide el
precio de la segunda red no es ese, porque el recall cuenta **enlaces** y la segunda red
solo toca **grupos**: medido sobre gold, los pares ciertos que acaban en el mismo grupo
pasaron de **1.806 de 1.809 a 1.807 de 1.809**. No costo: gano uno.


**La sexta la propuso Claude y es la mejor de todas**, asi que va en la barra: los
enlaces son 1-a-1 **por par de cadenas**, y por tanto **un grupo no puede tener dos
productos de la misma cadena** salvo que compartan EAN (el duplicado legitimo). Es
una **invariante**, no una tolerancia: no hay umbral que elegir, y no mira el precio,
asi que no puede borrar los ahorros reales de 28x. Cuando se midio por primera vez,
los **74 de 74** grupos de 11 o mas la incumplian.

Los dos instrumentos de esa condicion viven hoy en `data/debug/_cadena_repetida.py`,
que esta en `.gitignore`: **deberia subir a `projects/cesta/` junto a `ejes.py`**, y
su techo ponerse en `tests/test_atributos.py` como los otros cuatro.

Y la de mas valor, que no es ninguna de esas cinco porque es la que las explica
(medido el 23 de septiembre de 2026, despues de las dos redes):

    grupos que mezclan un pack con sueltas      642
    de esos, de 11 o mas                          0

Los tres instrumentos, y donde viven: `projects/cesta/ejes.py` (ejes y pack, sobre el
gold; sus techos estan en `tests/test_atributos.py`), `tests/test_contraste.py` (el
contraste del texto y de los limites, con la formula de WCAG escrita dentro) y
`data/debug/_conflictos.py` (los conflictos de asignacion de una pasada, a partir de
su `equivalencia.parquet`). Los dos primeros son pruebas; el tercero es un script de
trabajo y **deberia subir a `projects/cesta/`** el dia que se toque el canal de
vectores otra vez.

**Donde se aplicaria un modelo de salida forzada (Jev), para cuando haya acceso.**
El estudio esta en `docs/JEV-IMPLANTACION.md` y el catalogo en `docs/JEV.md`. Los
sitios, por orden de valor, y los dos primeros **se pueden probar hoy sin Jev**,
porque ya tenemos un modelo local y un arnes que fuerza el esquema JSON
(`projects/cesta/banco_de_pares.py`):

1. **El clasificador de ejes** (`core/atributos.py`): hoy son 12 ejes, 28 opciones y
   71 patrones de subcadena escritos a mano, y cada eje nuevo es otra ocasion del
   mismo fallo (`desnatad` casando dentro de `semidesnatad`). Es un `Choice` de
   manual: el nombre es el `state`, los valores del eje mas "no lo dice" la salida, y
   la regla de que **el que calla no bloquea** se implementa con la confianza.
2. **Las categorias sin pasillo**: es **el unico paso de la cadena diaria que
   todavia dice "A MANO"**. Son 19 opciones exactas (`core/secciones.ORDEN`) y hay
   881 claves ya mapeadas que sirven de banco de pruebas gratis.
3. **Nada mas por ahora**: como juez de pares no (el 64 % de lo que se nos escapa es
   dato numerico, que es justo lo que Jev documenta que no sabe hacer), y las
   ofertas tampoco (las 1.260 fichas de `SIN_REGLA` son **20 textos distintos**: eso
   es una lista de veinte cadenas, no un modelo).

La barra antes de tocar `core/atributos.py`: tiene que **reproducir las listas a
mano** en el pasillo coherente, tiene que salir mejor en los tres casos que hoy
sobre-disparan (`yogur natural` no es cafeina, `vino blanco` no es harina integral,
`orujo de hierbas` no es aceite), y los **ejes contradictorios** (hoy 52) no pueden
subir.

### El encargo de UX del 23 de septiembre, y como se juzga

Esta en `Claude outputs/ENCARGO-UX-23SEP.md` (328 lineas, 11 secciones). Lo que
cambia de marco, y es lo que manda sobre todo lo demas:

**Cesta hoy ensena datos; lo que hace falta es que conteste preguntas.** Nadie abre
esto pensando "quiero ver el indice encadenado". Se abre con una de estas cuatro:

    1. Que me falta, y donde lo compro.
    2. Esto que tengo en la mano, esta caro?
    3. Voy tachando bien?
    4. Ha bajado algo de lo mio?

**Y la prueba de aceptacion no es un porcentaje**: coger el movil y contestar las
cuatro **en menos de quince segundos sin saber donde esta el boton**. Se juzga
**contra la madre del dueno**, no contra quien escribio el codigo: no va a leer
ayuda, no va a explorar menus, y si algo no se entiende a la primera **no pregunta:
deja de usarlo**. Cualquier tarea de interfaz que no acerque a eso es decoracion.

Por orden de valor, y con lo que cada uno tiene de innegociable:

    1. La primera vez (nadie la ha mirado y decide si alguien vuelve): se arregla
       ENSENANDO LA APLICACION FUNCIONANDO con datos reales, no con una visita
       guiada.
    2. La lista, mas cuidado que el resto junto: dos secciones (por coger / en el
       carro), pasillo pegajoso, deshacer en vez de confirmar, y SIN aviso rojo
       cuando no hay cobertura.
    3. "Esto esta caro?": LA FRASE ANTES QUE LA TABLA, y sin frase si el grupo no
       es de fiar.
    4. /api/habituales, con el caso del primer dia (origen: tuyo | de todos |
       basico).
    5. La cohesion contra el medoide como SEGUNDA RED: la invariante caza lo que se
       funde ENTRE cadenas, el medoide lo que se funde DENTRO de un grupo
       legitimo. El umbral se calibra contra el banco de pares, no a ojo.
    6. Los avisos, que hoy no avisan (`alertas.evalua()` solo corre al abrir la API).

**Reparto del trabajo, para no repetir el error**: el barrido de las 28 mejoras del
estudio **no se hace en paralelo en el front**; **el codigo del front lo toca un solo
agente a la vez**. Quien mida en el navegador devuelve los defectos con su numero,
como se hizo con los grupos.

### Estado del encargo de UX, y el paso siguiente escrito

    punto 1  la primera vez con datos reales      HECHO (23 sep: la tarjeta, puesta)
    punto 2  la lista                             HECHO (dos secciones, pasillo pegajoso,
                                                  deshacer y sin rojo sin cobertura)
    punto 3  "esto esta caro?"                    HECHO (la frase antes que la tabla)
    punto 4  /api/habituales                      HECHO de punta a punta: el endpoint
                                                  (3 escalones, origen por tarjeta) y
                                                  **el mosaico en el buscador**
                                                  (componentes/Mosaico.tsx); 404 en
                                                  produccion hasta el rebuild
    punto 5  el medoide como segunda red          HECHO y MEDIDO: no se pone como
                                                  guarda (el suelo del banco y los
                                                  grupos malos caen en el mismo tramo).
                                                  La segunda red que SI corta son los
                                                  ejes declarados, y los 49 estan en 0.
                                                  Instrumento: projects/cesta/cohesion.py
    punto 6  los avisos que no avisan             HECHO: el vigilante mira cuando
                                                  cambia gold (`api/vigilante.py`);
                                                  falta la campana en la pantalla
                                                  (no hay pantalla de alertas)

**Lo que le falta a la barra, dicho con su numero**, porque el encargo se cierra cuando
se cumplen las seis condiciones y no cuando se acaban las tareas:

    (a) las cuatro preguntas en menos de 15 s con el movil    SIN MEDIR
        No lo puede medir quien escribe el codigo: hace falta un navegador y un movil.
        Es lo que mide Claude, y devuelve defectos con su numero, no parches.
        Las cuatro YA tienen por donde contestarse: falta y donde (Cesta), esta caro
        (ficha, con la frase), voy tachando (Cesta, dos secciones), y ha bajado algo de
        lo mio (**Panel -> Bajadas -> «Solo lo mio»**, que entro el 23 sep). El guion
        de la medicion esta en `docs/PRUEBA-15-SEGUNDOS.md`, con los pasos exactos.
    (b) la primera vez con datos reales                       CUMPLE
    (c) la lista: dos secciones, pasillo pegajoso,
        sin rojo sin cobertura                                CUMPLE (23 sep)
    (d) la frase antes que la tabla, y sin frase si el
        grupo no es de fiar                                   CUMPLE
    (e) pruebas verdes y `verificar_docs` verde                CUMPLE
        (736 pasan; las 2 que fallan son de `core/datos/secciones.yml`, de otro
        agente, y no se tocan desde aqui)
    (f) CERO grupos con eje contradictorio                    0    CUMPLE (23 sep)
        menos de 30 grupos de 11+                             0    CUMPLE
        `--medir >= 57 %`                                     65 % CUMPLE

**De la barra solo queda (a), y no la puede cerrar quien escribe el codigo.** Las cinco
condiciones de dato estan en verde, y la ultima -- los 49 grupos con eje contradictorio
-- cayo el 23 de septiembre de 2026 con **la segunda red**; el como y el precio que
tuvo, unas lineas mas abajo.

Y (a) no se puede dar por hecha sin medirla: es la unica condicion que se juzga **contra
la madre del dueno**, y quien la mide tiene que ser alguien que no haya escrito la
pantalla. Lo que si se puede hacer desde aqui es no dejar nada que estorbe, y eso es lo
que se ha hecho.

**El «Deshacer» de la lista, listo para ejecutar.** Es el resto del punto 2 que mas
vale (quitar una linea es la accion destructiva, y hoy no se puede volver atras).
Esta comprobado que **la API ya lo permite**, que era la duda:

    almacen.py:288   en el ON CONFLICT (id) DO UPDATE de anadir linea:
                     borrado_en = NULL, tocado_en = now()

O sea que volver a anadir con **el mismo id** resucita la linea. Y
`api/cesta.ts::anadirLinea` ya acepta ese `id` como parametro (commit `481abff`), con
el porque escrito al lado. **Lo que falta son tres cambios en
`plataforma/web/app/src/paginas/Cesta.tsx`, y hay que hacerlos los tres juntos**
(una parada a medias deja el arbol en rojo, porque TypeScript avisa de importaciones
y variables sin usar):

    1.  anadir `anadirLinea` a la importacion de `../api/cesta` (linea ~34).
    2.  en el `map` de las secciones, pasar la linea entera cuando el cambio es un
        borrado:  `cambiar={(lineaId, cambio) => cambia.mutate({lineaId, cambio,
        linea: cambio.borrado ? l : null})}`. Asi **no hace falta estado nuevo**: la
        linea quitada viaja en las `variables` de la propia mutacion de TanStack.
    3.  pintar la barra de deshacer leyendo `cambia.variables?.linea`, con un
        `<Boton>` que llame a `anadirLinea(listaId, {nombre: l.nombre_visto,
        grupo_id: l.grupo_id, producto_id: l.producto_id, cantidad: l.cantidad},
        l.id)` y refresque la lista.

Y lo que **no** hay que hacer, que es la tentacion: reanadir sin el id. Eso no
deshace: **crea una linea nueva** y deja la compra duplicada, que es peor que no
poder deshacer.

### El punto 1 esta hecho, y se hizo mal una vez: escrita y sin poner

La tarjeta de la primera vez es `plataforma/web/app/src/componentes/LoQueSeCompra.tsx`,
y esta puesta en el estado vacio del buscador (`paginas/Buscar.tsx`, `{!busca &&
<LoQueSeCompra />}`). Cuatro productos que compra todo el mundo, con la diferencia de
hoy. **Sin visita guiada**: una guia se lee una vez; cuatro precios reales se entienden
solos.

**El fallo que hay que contar, porque es el que se repite.** El componente se escribio
en la ronda anterior, compilaba, y **no lo llamaba ninguna pantalla**: en el buscador
seguia viendose exactamente lo de antes, y ni `tsc` ni `vite build` dicen nada de un
componente que nadie pinta. Estuvo asi hasta que se fue a mirar quien lo llamaba. Por
eso `tests/test_primera_vez.py` comprueba **quien lo pinta**, no que exista: un
componente suelto es como no tenerlo.

**De donde salen los cuatro, medido y no elegido a ojo.** Cada busqueda ensena solo su
primer resultado, asi que ese primero tiene que ser un producto llano cuyo nombre repita
lo que se ha buscado. Contra la API viva el 23 de septiembre de 2026
(`/api/buscar?q=<basico>&limite=1`, los cuatro `comparable: true`):

    leche entera    -> «Leche entera»                        96 -> 167 cent
    pan de molde    -> «Pan de molde integral sin corteza»  233 -> 644 cent
    aceite de oliva -> «Aceite de oliva suave»              370 -> 519 cent
    agua mineral    -> «Agua mineral Dia 1,5 L»              18 ->  26 cent

**`huevos` estuvo en la lista y se quito**: su primer resultado es «Media tortilla de
patata con cebolla». Una tarjeta que promete huevos y ensena una tortilla se lee como un
fallo justo el dia que mas caro sale. La regla queda escrita al lado de `BASICOS`, y la
prueba se pone roja si alguien lo devuelve a la lista.

**Y eso destapa un defecto aparte, que no se tapa eligiendo otra palabra**: buscar
`huevos` pone **una tortilla** la primera, y buscar `aceite de oliva` mete «Picos sin
gluten» entre los cinco primeros. Es relevancia de busqueda, afecta a todo el mundo y no
solo a esta tarjeta. Queda **pendiente** con la consulta que lo reproduce, para que se
pueda comprobar sin creerselo:

    curl -s "http://127.0.0.1:8080/api/buscar?q=huevos&limite=5" | jq '.resultados[].nombre'
    curl -s "http://127.0.0.1:8080/api/buscar?q=aceite%20de%20oliva&limite=5" | jq '.resultados[].nombre'

Elegir `agua mineral` para el ejemplo **no arregla** que a quien escriba `huevos` le
salga una tortilla: son dos cosas distintas, y la segunda sigue abierta.

Lo que la tarjeta **no** hace, y es lo que la mantiene honesta: si una busqueda no
devuelve nada o devuelve algo que no se puede comparar, **ese hueco no se rellena**; y
si no queda ninguno de los cuatro, no se pinta nada y el buscador se queda como estaba.
La diferencia sale de restar los dos precios por unidad del grupo, no de un `ahorro` que
llegue sumado por otro camino.

### La segunda red: el eje que el nombre declara (los 49 se fueron a cero)

Es la ultima condicion de dato que quedaba, y la que el encargo pide **a cero**: cero
grupos con eje contradictorio. Estaba en 49.

**Lo que se hizo, en una frase**: `agrupar_enlaces` acepta ahora un parametro `nombres`
(`core/matching.py`), y con el **rechaza la union que dejaria un eje contradictorio
dentro del grupo**. Dos nombres que dicen `virgen` y `virgen extra` -- o `entera` y
`desnatada` -- **no son el mismo producto**, y no hace falta mirar el precio para
saberlo: lo dice el nombre.

**Por que el eje y no el margen.** Ya estaba comprobado y conviene repetirlo, porque es
la tentacion: `core/comparacion.py` documenta ahorros reales de 28x entre marca blanca y
marca. Un cuchillo de precio borraria justo los hallazgos que esta aplicacion existe para
encontrar. **El margen detecta; el eje declarado en el nombre corta.** Y con la regla que
lo hace honesto, la misma de `core/atributos`: **el que calla no bloquea** -- un producto
que no dice si es entera o desnatada no afirma que sea igual, es que no lo sabemos.

**Lo que costo, medido sobre el mismo bronze y antes/despues** (23 de septiembre de 2026):

    metrica                                     antes    despues
    grupos con eje contradictorio                  49          0     <- la barra
    grupos de 11 o mas productos                    0          0
    cadena repetida sin EAN                         0          0
    grupos comparables entre cadenas            8.803      8.781
    pares ciertos EN EL MISMO GRUPO      1.806 de 1.809  1.807 de 1.809
    recall de --medir                           65 %        65 %    <- la barra
    grupos que mezclan pack con sueltas           644        642

El recall de `--medir` cuenta **enlaces**, y la segunda red solo toca **grupos**: por eso
el numero que mide su precio no es ese, sino **cuantos pares ciertos acaban en el mismo
grupo**, y eso hay que medirlo sobre gold (1.809 pares con el mismo codigo en dos
cadenas distintas). Salio **a favor**: uno mas que antes. No hay coste que justificar.

**Y por el camino se encontro un eje que estaba mal.** El eje `formato` tenia
`concentrado` como opcion, y no es una opcion del mismo eje que las otras dos: el estado
(polvo o liquido) y la concentracion son dos cosas distintas y un producto puede ser las
dos. Se llevaba por delante pares **ciertos por codigo de barras**:

    «Cafe liquido espresso concentrado black Nescafe 500 ml»   carrefour
    «Cafe espresso concentrado black Nescafe 500 ml»           dia        EAN 9556001329141
    «Ambientador liquido concentrado Foresan deluxe»           mercadona
    «Ambientador concentrado Deluxe Foresan 125 ml»            carrefour  EAN 8414716502321

Son el mismo producto con el nombre escrito de dos maneras. `concentrado` se quito de
`formato`, y con eso los pares ciertos juntos subieron de 1.801 a 1.807: **un eje
inventado es peor que no tenerlo**, que es la regla que ya estaba escrita en
`core/atributos.py`.

Los cuatro techos de `tests/test_atributos.py` bajaron en el mismo commit (`49 -> 0`,
`648 -> 642`), y `tests/test_invariante_reparto.py` gana cinco pruebas de la segunda red,
incluidas las dos que importan: **`virgen` y `virgen extra` no van al mismo grupo** y
**el que calla no bloquea**.

**Lo que queda de este punto, y es el punto 5 del encargo**: el medoide. La segunda red
de hoy corta donde **el nombre declara** algo distinto; queda lo que se funde sin que
ningun nombre diga nada. Se ha medido, y la respuesta esta unas lineas mas abajo: **la
cohesion contra el medoide mira, pero no puede cortar** -- el suelo del banco de pares
cae en el mismo tramo que los grupos peores del catalogo.

### El mosaico de lo de siempre, en el buscador: un toque en vez de tres

La mejora que `docs/DISENO.md` llamaba «la de mas valor del buscador», y la pantalla que le
faltaba al punto 4. `componentes/Mosaico.tsx`, en el estado vacio del buscador: cuadricula
de **tres columnas** (`docs/PANTALLAS.md:57-62`), foto, nombre, precio por unidad y la
cadena mas barata, y **un boton que apunta a la lista de casa con un toque** -- sin
dialoga, sin elegir lista y sin preguntar la cantidad (se anade con 1 y se cambia en la
cesta, que es donde se ve lo que va a costar).

**Las tres decisiones que lleva dentro, y ninguna es adorno:**

  1. **Sin historial no se pinta: sale la tarjeta de la primera vez.** Una cuadricula de
     24 productos basicos son 24 recuadros sin una razon para mirarlos;
     `LoQueSeCompra` ensena cuatro que compra todo el mundo **con su diferencia de hoy**,
     que es lo que hace entender para que sirve la aplicacion. Primero se entiende,
     despues se usa. **Y decide `Mosaico`, en un solo sitio**: con la condicion tambien
     en `Buscar.tsx`, el dia que una cambie se pintan las dos cosas a la vez.
  2. **Un 404 no es una pantalla roja.** Mientras la imagen de la API que corre no tenga
     la ruta, esto contesta 404 -- y quien acaba de abrir la aplicacion no tiene la culpa
     de eso. Se cae al mismo sitio que sin historial.
  3. **El `origen` se dice solo cuando la cuadricula mezcla escalones.** Una tarjeta
     basica y una tuya no valen lo mismo, asi que hay que poder decirlo; pero doce
     etiquetas iguales en una cuadricula que no mezcla son ruido.

Y el boton dice **«En la cesta»** cuando ya esta: pulsar tres veces el mismo boton es el
error facil de verdad, y aqui se ve sin salir de la pantalla.

Probado en `tests/test_mosaico.py` (7 pruebas, leyendo el codigo como las de contraste) y
en `tests/test_primera_vez.py`, que ahora comprueba la cadena entera -- `Buscar` pinta el
mosaico, y el mosaico cae en la tarjeta cuando no hay historial -- porque **el fallo de
"escrito y sin pintar" ya paso una vez** con esa misma tarjeta.

Verificado en el bundle servido: pide `/habituales`, lleva «Lo de siempre» y la
cuadricula de tres columnas. `pytest` 759 pasan / 2 fallan (las dos de
`core/datos/secciones.yml`, que no son mias) y `ruff` limpio.

### Los avisos ya avisan: el vigilante mira cuando cambian los datos

Punto 6 del encargo, y el fallo era de una linea: *"`alertas.evalua()` solo corre cuando
alguien abre `GET /api/alertas`, o sea que la alerta salta si entras a mirar."* Un aviso
que solo salta cuando vas a verlo no es un aviso.

**Lo que se hizo.** `plataforma/api/vigilante.py`, un hilo dentro de la API que mira
**cuando cambia gold** (`catalogo.sello_de_gold()`, la fecha de escritura de
`grupos.parquet`) y, en cada pasada:

  1. lee de PostgreSQL las alertas **pendientes**: `vista_en IS NULL AND salto_en IS NULL`
  2. las mira contra gold con `alertas.evalua` -- la misma funcion que usa la pantalla,
     para que no haya dos reglas que puedan separarse
  3. apunta `salto_en = now()` y **la frase que la explica** en cada una que salta

**Dos columnas nuevas, y son dos cosas distintas** (`sql/006_alertas_que_saltan.sql`,
que se aplica sola: `almacen.migra()` corre todos los `.sql` al arrancar):

    salto_en      cuando se cumplio la condicion. Lo pone el vigilante.
    salto_texto   la frase, guardada en ese momento.

La frase **se guarda y no se recalcula**, y ese detalle importa: se mide contra el gold de
ese dia, y gold se reescribe cada manana. Sin guardarla, el aviso que alguien vio ayer
contaria hoy otra cosa, o ninguna. Es lo que pedia el encargo con *"dejar el resultado
guardado, para que abrir la aplicacion sea instantaneo"*.

**`vista_en` no se toca, y es la mitad de la gracia.** `vista_en` es "esta persona lo ha
visto" y lo pone ella; apuntarlo desde el vigilante seria decir que alguien ha visto un
aviso que no ha visto, y abrir la pantalla no podia volver a contarlo. Y una alerta
**salta una vez**: el `UPDATE` lleva `AND salto_en IS NULL`, asi que dos pasadas seguidas
no cuentan lo mismo. Un aviso que se repite todos los dias deja de leerse.

**Donde se aparta de lo que decia el encargo, y por que.** El encargo pedia evaluarlas
*"en la cadena diaria, despues del pipeline"*. **No se hizo ahi**: la cadena diaria corre
en la maquina y no toca PostgreSQL, que es donde viven las alertas -- la API es la unica
que habla con las dos mitades. Meter un paso nuevo en `ejecutar.bat` seria cruzar esa
frontera y arriesgar la tarea de las 06:00, que **no se puede romper**. El vigilante
consigue lo mismo (la alerta salta sin que nadie mire) y ademas cubre los relanzados: si
el pipeline se rehace a las once, vuelve a mirar.

**Un fallo no puede tumbar la API**: la pasada va envuelta, se imprime el fallo y el bucle
sigue; si PostgreSQL o gold no estan, se reintenta en la vuelta siguiente. Probado.

`tests/test_vigilante.py` (8 pruebas, gold de mentira y PostgreSQL sustituido): que se
apunta `salto_en` y la frase, que **no** se toca `vista_en`, que una alerta que no se
cumple no se apunta, que dos pasadas no cuentan lo mismo, que un fallo no para el bucle y
que **solo se mira cuando gold cambia**.

**Lo que queda del punto 6, y es pantalla**: el *"punto en el icono"* y la frase entera
al abrirlo. **Hoy no hay pantalla de alertas en la interfaz nueva** -- `alertas` no
aparece ni una vez en `plataforma/web/app/src` --, asi que eso es una pantalla entera, y
va en la lista de lo que falta de la interfaz, no en el vigilante. La API ya lo tiene todo
para pintarla: `GET /api/alertas` devuelve cada alerta con su `salto_en` y su
`salto_texto`.

### El medoide: medido, calibrado contra el banco, y **no se pone como guarda**

El punto 5 del encargo pedia la cohesion contra el medoide como segunda red, con el
umbral **calibrado contra el banco de pares y no elegido a ojo**. Esta hecho, medido y
decidido, y la decision es **no cortar con ella**. El instrumento se queda en
`projects/cesta/cohesion.py`, que es lo que faltaba: hasta hoy solo habia una hipotesis.

**Que mide.** Para cada grupo, el **medoide** (el miembro con la media de parecido mas
alta al resto, o sea el centro medido y no elegido) y la **cohesion** (el parecido del
medoide con el miembro que peor encaja). Los vectores son `bge-m3` del cache de
`data/gold/embedding.parquet`, leidos en SQL.

**Lo que salio el 23 de septiembre de 2026** (52.417 productos, 8.756 grupos con dos o
mas miembros con vector; 1.791 pares ciertos con vector):

    grupos cuya cohesion es menor que:   0,50 -> 0    0,60 -> 84    0,70 -> 1.244
                                         0,75 -> 2.865   0,85 -> 5.925   0,95 -> 8.456
    pares CIERTOS:   minimo 0,511   p1 0,617   p5 0,725   mediana 0,874

**El suelo del banco (0,511) esta en el mismo tramo que los grupos peores del catalogo**,
asi que el umbral no separa nada: o no corta (por debajo de 0,51, y ahi no hay ningun
grupo), o se lleva por delante pares ciertos y grupos legitimos a la vez.

Y leyendo los nombres se ve por que. Los cuatro grupos de cohesion mas baja:

    grupo 24370   0,500   'Boniato'                             (aldi)
                          'Boniato Carrefour 1 kg aprox'        (carrefour)
    grupo 7096    0,513   'CILLIT BANG Multiusos 750ml + 33% gr.'  (alcampo)
                          'Multiusos cocina Bosque Verde'          (mercadona)
    grupo 2750    0,537   'TENDILLA Torrezno frito lima-chili'  (alcampo)
                          'Rolls picantes sabor chili-lima'     (aldi)
    grupo 2393    0,719   'VICTORIA Cerveza pack 6 uds. x 20 cl.'  (alcampo)
                          'Cerveza Estrella Galicia especial pack 24 latas 33 cl.' (carrefour)
                          'Cerveza Estrella Galicia pack 6 x 20 cl'  (dia)

Los dos primeros son **comparaciones legitimas y valiosas** -- el mismo producto con marca
blanca y con marca nacional, escrito de dos maneras, que es exactamente lo que esta
aplicacion existe para comparar --; el tercero mezcla dos aperitivos distintos y el
cuarto dos cervezas distintas, **y los cuatro tienen el mismo parecido**. El texto es
justo lo que cambia cuando la comparacion vale mas. Para cazar el grupo 2393 (que esta en
0,719) habria que cortar en 0,72, y ahi se van un 5 % de los pares ciertos y 2.865 grupos.

**Conclusion, escrita como es**: la cohesion sirve para **mirar**, no para cortar. No se
pone como guarda en `agrupar_enlaces`, y el motivo esta medido, no supuesto. Lo que
separa de verdad en ese grupo de cervezas no es la cohesion: son **formatos distintos**
(6 x 20 cl frente a 24 x 33 cl), o sea la dimension del pack, que se mide en
`projects/cesta/ejes.py` (hoy 642 grupos mezclan un pack con sueltas, y **0 de ellos son
de 11 o mas**).

Esto es la misma leccion que dio el canal de vectores (+3.998 enlaces y 861 conflictos de
asignacion): **el parecido de texto propone, no decide**. Se puede volver a intentar
cuando haya una senal que separe "otro nombre" de "otro producto" -- y entonces el numero
a batir es este: **0,511 de suelo y 0,719 el grupo malo que se quiere cazar**.

### El pasillo de la lista, pegado arriba: la ultima pieza del punto 2

Es la condicion (c) de la barra, y la que cerraba el punto 2: *"la lista en dos
secciones, **con pasillo pegajoso** y sin aviso rojo cuando no hay cobertura"*.

**El motivo no es de diseno, es de tienda.** Esta es la unica pantalla que se usa de
pie, en movimiento y con una mano: lo que hay que saber mientras se empuja el carro es
**en que pasillo se esta**. Con nueve lineas de seis pasillos, leer los nueve nombres
para saber que queda aqui es trabajo que se hace andando.

**De donde sale el pasillo, y la regla que hubo que escribir.** El pasillo es un
atributo del **producto** (`seccion` viaja por producto, `catalogo.buscar:225`), y un
grupo tiene miembros de varias cadenas. Medido sobre el gold del 23 de septiembre:

    pasillos distintos en gold                          20
    productos sin pasillo                                86   (0,16 % de 52.417)
    grupos con miembros en mas de un pasillo          2.437 de 39.702   (6,1 %)

(El total de 39.702 son los grupos con `grupo_id` de `data/gold/grupos.parquet`; los
39.563 de `ejes.py` son los comparables, que es otra cuenta y por eso no cuadra.)

O sea que el caso "no coinciden" **no es un rincon**: en 2.437 grupos hay que decidir.
Se decide asi, y esta escrito en `catalogo.pasillo_de_grupos`: gana **el pasillo que
mas miembros comparten**, y los empates se rompen **por el orden del recorrido de la
tienda**. Sin una regla escrita, el mismo grupo cambia de pasillo entre dos ejecuciones
sin que haya cambiado nada, y la lista se reordena sola delante de quien la mira.

**Las tres decisiones de pantalla**, en `Cesta.tsx::porPasillo`:

1. **Las lineas sin pasillo van las ultimas y sin encabezado.** No se les pone "otros"
   ni el nombre del grupo: un dato que no tenemos no se rellena. Y si gold no trae la
   columna -- la plataforma se despliega por separado del scraper, puede llegar antes
   --, la lista se pinta de un tiron, exactamente como ayer.
2. **El orden de dentro de un pasillo no se toca.** Lo manda la API
   (`ORDER BY en_carrito, anadido_en`), y `sort` es estable, asi que las lineas del
   mismo pasillo mantienen el orden en que llegaron. Lo unico que se ordena aqui es
   **en que orden salen las tandas**: el del recorrido de la tienda.
3. **La altura de la cabecera se mide, no se escribe.** La cabecera de la aplicacion
   tambien es `sticky top-0`, asi que un pasillo pegado en `top: 0` se metería detras.
   `Cabecera.tsx` publica su altura como `--alto-cabecera` con un `ResizeObserver`, y
   el pasillo se pega en `top: var(--alto-cabecera)`. Se mide porque **no es una altura
   fija**: envuelve en movil y el desplegable de "Estado de las cadenas" la hace mas
   alta. Un `top-14` escrito a mano acierta hoy y falla el dia que cambie una linea de
   texto, sin dar ningun error.

**Lo que la API manda y lo que no**: `GET /api/listas/{id}` devuelve cada linea con
`seccion` (el slug), `pasillo` (el nombre que se lee) y `pasillo_orden` (su punto en el
recorrido). **No reordena nada**: quien reparte en tandas es la pantalla, que es la que
sabe cuantas secciones tiene la lista. Lo mismo en `/sincronizar`, para que la lista no
cambie de forma segun por donde haya entrado el dato.

Probado en `tests/test_pasillos.py` (8 pruebas, con gold de mentira y sin PostgreSQL) y
`tests/test_pasillo_pegajoso.py` (5, leyendo el codigo, como las de contraste).

### Sin cobertura en el pasillo no es un fallo, y ya no se anuncia como uno

Condicion (c) de la barra, y la mitad que faltaba del punto 2. Lo que habia en
`paginas/Cesta.tsx` era esto:

    {cambia.isError && (
      <Aviso tono="mal" titulo="No he podido guardar el cambio">
        ... Sin la cola de cambios de la interfaz antigua, aqui no se pinta un cambio
        que el servidor no ha aceptado.

Tres cosas mal en cuatro lineas, y las tres se arreglan distinguiendo **que clase de
fallo es**:

  - **Un fallo de red pintado en rojo.** `Aviso` pone `role="alert"` cuando el tono es
    `mal`, asi que quedarse sin cobertura en el pasillo -- que es lo normal, no un fallo
    de nadie -- se anunciaba como una alarma. Se lee como "la aplicacion se ha roto" y
    la lista se deja de usar justo donde mas sirve. Ahora va en tono neutro, y dice lo
    unico que hay que saber: que el cambio **no se ha guardado** y que hay que volver a
    pulsar.
  - **Una explicacion para quien programa dentro del aviso que lee quien esta en la
    caja**: la cola de cambios de la interfaz vieja no le importa a nadie que este
    haciendo la compra.
  - **Y el agujero que salio al mirarlo**: si lo que no llega es **la propia lista**
    --abrir la aplicacion en el pasillo sin cobertura--, `detalle.isError` **no se
    miraba en ninguna parte**. Desaparecia el estado de carga, quedaba el encabezado y
    la pantalla en blanco, sin decir nada. Eso si parece una aplicacion rota.

La regla vive en un solo sitio, `api/cliente.ts::esSinRed` (`fetch` lanza `TypeError`
cuando no puede ni salir del aparato), al lado de `textoDeError`, que ya trataba ese
mismo caso: si cada pantalla lo comprobara por su cuenta, el texto y el color acabarian
discrepando. Un 403 de una lista de solo mirar o un 500 **siguen siendo rojos**: eso si
hay que mirarlo.

Probado en `tests/test_sin_cobertura.py` (4 pruebas), que leen el codigo como las de
contraste y las de movil: esto es una decision de pantalla y un cambio que devuelva el
rojo no da ningun error de compilacion. Verificado ademas en el bundle servido: lleva
«Sin cobertura», sigue llevando el rojo del guardado, y ya no dice «interfaz antigua»
en ninguna parte.

**Lo que queda del punto 2**: nada de la lista en si -- el **pasillo pegajoso** entro el
mismo dia, unas lineas mas arriba --, y **la regla de "sin cobertura" ya vale en todas
las pantallas**: se puso en `componentes/ui.tsx::Fallo`, que es el unico sitio por el que
pasan buscar, la ficha, el grupo, el escaner, el panel y el panel de matching. Arreglarlo
pantalla por pantalla habria dejado la septima naciendo en rojo, que es justo lo que
habia pasado con la lista. El rojo sigue para lo que **la API contesta que no** (un 403 de
una lista de solo mirar, un 500): eso si hay que mirarlo.

### `/api/habituales` rellena por escalones, y el origen va en cada tarjeta

Verificado el 23 de septiembre contra la base viva. La ruta existe
(`plataforma/api/habituales.py`), pide sesion, `limite` acotado, los tres origenes
documentados, sin `polars`, y eligio **pesar por recencia con vida media de 30 dias**
con el porque escrito. Todo eso esta bien.

**El problema era de contrato, y se vio con los datos de la casa, no con un caso
inventado.** El historial real:

    lineas del dueno            1   (grupo 9919, del 2026-09-21)
    lineas de toda la casa      1   (y esa esta borrada)

Y `lista()` devolvia **el primer escalon que tuviera algo**, sin rellenar, asi que con
**una** linea propia la respuesta era un mosaico de **una tarjeta**. El encargo pedia que
*"con historial vacio la pantalla no se vea vacia"*; con historial *casi* vacio, que es el
caso real de una casa que empieza, se veia casi vacia. Era el problema numero uno del
encargo -- la primera vez -- reapareciendo dentro del endpoint construido para resolverlo.

**La decision, tomada antes de que haya consumidor** (y entonces costaba una linea, como
estaba escrito aqui): **se rellena hasta `limite` bajando escalones** -- tuyo, de todos,
basico -- y **`origen` pasa a ir en cada tarjeta**, que es la opcion honesta de las dos
que estaban sobre la mesa: una tarjeta basica y una tuya no valen lo mismo, y una
cuadricula puede tener las dos a la vez. Lo que se dice una vez es `origenes`, la lista de
escalones que han entrado, para que la pantalla sepa si tiene que explicar algo.

Y **un grupo no se repite**: si lo que compras es "leche entera" y ademas esta en la
compra basica, sale una vez, en el escalon de mas arriba. Repetirlo para llenar la
cuadricula seria inflar el mosaico con lo mismo.

Lo que **no** cambia: en `"de todos"` y `"basico"` **no viajan `veces` ni `ultima_vez`**
-- son recuentos de todo el mundo o de nadie, y mandarlos con el mismo nombre que los
tuyos seria repetir el error de "imposible" (dos numeros, un nombre).

Probado en `tests/test_habituales.py` (26 pruebas, dos nuevas): un mosaico con **una**
linea propia deja de ser de una tarjeta, y un grupo que sale en dos escalones sale una
vez.

**La ventana sigue abierta y sigue siendo el momento**: la palabra `habituales` aparece
**0 veces** en `plataforma/web/app/src`, asi que no hay ningun consumidor al que
romperle el contrato. El dia que el mosaico se programe, esto ya esta decidido.

Y el numero que hay que mirar antes que ninguno: **`--medir` mide la configuracion
que corre**, que hoy son 65 % sin el canal de vectores. El canal esta apagado a
proposito (sube a 73 % de recall y rompe los conflictos de asignacion de 0 a 861).

Con los puntos 1 a 3 hechos, la interfaz nueva **ya se puede servir**: la API que
hay en produccion tiene todo lo que pide. Lo que decide cuando se cambia el
montaje de `docker-compose.yml:77` es la paridad de la interfaz, que es el punto
0 de arriba, no la API.

**Lo que ya esta hecho (22 sep 2026).** Todo esto esta en git, con sus pruebas.

    docs/DIAGNOSTICO-MATCHING.md            el informe, con TODOS los numeros y
                                            las mediciones que descartaron ideas
    projects/cesta/diagnostico_matching.py  lo reproduce en un comando
    core/normalize.py                       la etiqueta de 100 g/ml, por cadena
    projects/cesta/pipeline.py              cantidad_fiable, la unidad que se
                                            contradice, y el formato que el
                                            propio precio de la cadena desmiente
    core/matching.py                        asignacion hungara 1-a-1, etiqueta
                                            identico veraz, veto de precio,
                                            freno de union y freno de ancho
    core/equivalencias.py                   Fase 1: producto_id estable y cada
                                            pasada versionada, con su motivo
    core/embeddings.py                      Fase 3: bge-m3 por Ollama, cache
                                            incremental, y el coseno EN SQL
    projects/cesta/banco_de_pares.py        el banco de pares con verdad del EAN
                                            (1.809 positivos, 63.049 negativos)
    projects/cesta/embeddings.py            la medida de si los vectores ayudan
    plataforma/api/                         /api/ean y /api/panel/matching, mas
                                            marca en la busqueda y producto_id en
                                            la serie
    plataforma/web/app/                     LA INTERFAZ NUEVA: Vite + React +
                                            TypeScript + Tailwind + TanStack +
                                            uPlot. Compila a web/dist y Caddy
                                            sirve eso (docker-compose.yml:61).
                                            Los ficheros viejos siguen ahi como
                                            plan B.
    tests/                                  640 pruebas. Las que guardan cosas
                                            que se rompen solas: test_interfaz
                                            (el sitio donde compila y el que se
                                            sirve), test_imagen_api (la API no
                                            arrastra polars), conftest (las
                                            pruebas no leen el disco)
    projects/cesta/collectors/carrefour.py  cat11729677 en ROTAS_EN_ORIGEN
    git                                     el proyecto YA tiene control de
                                            versiones; no tenia .git

**Tres fases de "algoritmos complejos" se midieron, y dos se descartaron.** Esta
es la parte del BACKLOG que mas tiempo ahorra a quien venga detras:

    3 · embeddings (bge-m3)      PASA. Precision 0,90 con recall 0,89 en el
                                 umbral 0,76, medido contra los negativos
                                 dificiles. Integrado como generador de
                                 candidatos, apagado por defecto si no hay cache.
    8 · clasificador aprendido   NO. Ninguna caracteristica separa un acierto de
                                 un error: el parecido del nombre es incluso
                                 MAYOR en los pares equivocados (0,848 contra
                                 0,814). No hay nada que aprender.
    9 · LLM local (JSON forzado) NO. Con el enunciado estricto acierta 20 de 20
                                 negativos y 1 de 20 positivos: es un esceptico.

**Y la conclusion que apunta a traer datos en vez de a programar**: los errores que
quedan no se arreglan con un modelo. Dos productos de la misma marca con codigos
distintos son, por construccion, casi identicos en todo el texto. **Lo que los
separaria es mas codigo de barras**, y hoy solo lo trae el 48,5 % del catalogo:
son exactamente Alcampo (0 de 23.776) y Aldi (0 de 2.123), que no publican
ninguno. Comprobado ademas que no se pierde ni uno entre capas: 25.517 en bronze,
25.517 en silver y 25.517 en gold.

**Los numeros, antes y despues, medidos sobre el mismo bronze.**

    aciertos de emparejar --medir       57 %   ->  65 %    (el liston es 57 %)
    productos comparables               19.834 ->  22.696  (+14 %)
    grupos comparables                  6.431  ->  7.997   (+24 %)
    grupo mayor                         329    ->  97
    etiqueta identico que dice verdad   70 %   ->  100 %
    conflictos de asignacion            ?      ->  0        (medido)
    fallos por "otra unidad"            172    ->  39
    filas en disputa (no se comparan)   85     ->  45
    grupos anchos (>200 %)              369    ->  261
      de esos, los que cuelgan de un enlace flojo  222 -> 66

Las cifras mas recientes de cada cosa estan en `docs/CIFRAS.md` y en el informe;
aqui van las que resumen el encargo. **Todo lo de esta tabla se midio corriendo el
codigo de antes y el de despues sobre el mismo bronze**, guardando la salida de
cada version: comparar dos dias distintos no mide el codigo, mide el calendario.

**Lo que queda mal, con las causas ya identificadas y medidas.**

Los grupos anchos NO vienen de un par malo: de los enlaces aceptados, **0** violan
el veto de precio de 30x. Y el criterio viejo del BACKLOG ("bajar de 405 grupos
anchos a menos de 150") **se retiro con la medicion hecha**: la mayoria de esos
grupos son equivalencias correctas de marca blanca contra marca cara, con un
ahorro real. Lo que distingue un grupo ancho bueno de uno malo no es el ancho,
es **la fuerza del enlace mas flojo que lo sostiene**. Ver el informe §17.

Y el freno que si funciona es ese: **un enlace flojo puede unir, mientras no haga
que el grupo se vuelva ancho**. Los intentos que NO funcionaron, con su medicion,
para que nadie los repita:

1. **Un grupo es lo que queda conectado, y eso se propaga.** Y no por muchos
   enlaces flojos, sino por **uno solo**: dentro del grupo 92 (97 productos, 181
   enlaces internos) el parecido mediano es **1,00** y lo que lo sostenia eran dos
   puentes de 0,55 (`Mahou tostada 0,0` <-> `Saer Brau tostada 0,0` <-> `Mahou
   tostada`). Ya hay un freno (`core.matching.agrupar_enlaces`, union 0,80: un
   enlace flojo puede meter a un producto suelto pero no pegar dos grupos) que
   baja el mayor de 329 a 97 y sube los comparables de 6.589 a 7.925. Se probo
   una version mas dura (un flojo solo entre dos sueltos): frena el error a la
   mitad, pero **hunde la letra de calidad de 12.996 a 5.546 productos** y se
   descarto midiendo.
2. **El IDF por pasillo se probo y NO arregla nada.** La hipotesis era buena:
   "cerveza" parece una palabra rarisima entre 52.567 productos y no distingue
   nada entre cervezas. Se implemento, se midio y se descarto: al mismo umbral
   cuesta 3 puntos de acierto, y puesto al umbral que los recupera el grupo mayor
   solo baja de 97 a 80 y la tasa de grupos anchos hasta empeora. **El motivo esta
   medido**: de los 137 enlaces internos del grupo mayor, en 50 manda el TRIGRAMA,
   y son justo los puentes. `parejo()` es `max(palabras, 0,85 x trigramas)`, asi
   que quitarle peso a las palabras no cierra un puente que abre el trigrama.
   **El numero a tocar era el 0,85** (`PESO_TRIGRAMAS`), y **tambien se probo y
   tampoco**: 0,80 da 64 % en vez de 65 %, quita 23 enlaces y deja la tasa de
   grupos anchos igual. El motivo es aritmetico: con el liston en 0,55, un puente
   sostenido por trigramas necesita un Dice de 0,55/0,85 = 0,647, y con 0,80 el
   corte sube a 0,6875, asi que solo caen los puentes de esa banda estrecha.
   Bajar el peso no apaga el canal, lo desplaza.
   **Las dos hipotesis sobre la puntuacion estan medidas y descartadas.** Lo que
   cierra los puentes es la asignacion y la union (hecho) y, mas alla, un freno a
   nivel de grupo. El codigo de `pesos_por_pasillo` se queda en `core/matching.py`
   con sus pruebas, y `PESO_TRIGRAMAS` ya no es un numero suelto dentro de una
   funcion: es una constante con su tabla de medicion al lado.
3. Y el grupo 30054 no es de emparejamiento: DIA publica **1 g** para unos filetes
   de dorada de "300 g aprox". Es el mismo roto que los 33 detergentes "de 61
   litros": el dato de cantidad de lo que se vende al peso.

El criterio del BACKLOG (**menos de 150 grupos con mas del 200 %**, hoy 448) no se
cumple **y se retira, con la medicion hecha**: se siguio esa pista durante tres
intentos y la premisa es falsa. La mayoria de los grupos anchos son equivalencias
correctas de marca blanca contra marca cara, con un ahorro real
(`Agua Dia 5 L` a 13,6 c/l contra `Solan de Cabras` a 53,8, sostenidas por un
enlace de 0,74; `Chocolate blanco Hacendado` contra `Toblerone`, enlace de 1,00).
Lo que distingue un grupo ancho bueno de uno malo **no es el ancho, es la fuerza
del enlace mas flojo que lo sostiene**:

    cuello < 0,60        222 grupos anchos (50 %)   <- la sospecha
    cuello 0,60 - 0,70   145                (32 %)
    cuello 0,70 - 1,00    69                (15 %)   <- el ahorro de verdad
    cuello = 1,00         12                 (3 %)

Y no se puede cumplir aunque se quisiera: exigiendo mas parecido para agrupar,
0,75 deja 196 grupos anchos (todavia mas de 150) y se lleva el 43 % de los
productos comparables y el 53 % de la letra de calidad.

**La metrica que se mide desde ahora** (ya la publica el diagnostico en cada
pasada): **grupos anchos que cuelgan de un enlace flojo (< 0,60): hoy 222.**
Bajarla no cuesta comparador, cuesta quitar puentes, que es lo que hay que hacer.

Lo que queda por hacer con esos 222 no es otro ajuste de la formula —las dos
hipotesis sobre la puntuacion (IDF por pasillo y peso de trigramas) estan medidas
y descartadas— sino un **freno a nivel de grupo**: no admitir un miembro si baja
el cuello de botella del grupo por debajo del liston. Esta en
`docs/DIAGNOSTICO-MATCHING.md` §17.

Y una cosa que ya no cuesta nada: `uv sync --extra plataforma` esta hecho, asi
que `pytest` completo pasa de 545 a **585 en verde** (los 30 de mas son las
pruebas de la API, que no corrian por falta de fastapi).

Los **2 fallos** que quedaban en `test_verificar_precios` **estan arreglados**
(23 sep), y eran un defecto de verdad, no ruido: `informe()` contaba como fallo
todo lo que no coincidia, asi que un dia de red mala daba el mismo aviso que un
dia de precios malos. Ahora solo `no aparece` y `404` cuentan. La suite entera:
**642 pasan, 0 fallan, 1 saltada.**

**Las decisiones que se tomaron, y por que.**

1. **git**: hecho. Habia dos agentes escribiendo en los mismos ficheros sin red.
2. **El front se rehace con Vite + React + TS, y Caddy lo sigue sirviendo.** Nada
   de FastAPI sirviendo HTML: `docs/API.md:336` sigue valiendo. Se actualizo
   `docs/APP.md:318`. Cambio pendiente para el dia del front: en
   `docker-compose.yml:61`, `./web:/srv:ro` pasa a `./web/dist:/srv:ro`.
3. **Ningun veto duro por unidad ni por categoria.** Medido: los 266 enlaces con
   unidad distinta eran, los 266, el mismo producto (mismo EAN). Y
   `docs/MODELO.md:42-45` ya decia que en un grupo manda una unidad pero a nadie
   se le expulsa.
4. **El umbral de precio es 30x, no el 60 % del plan.** Con el 60 % habria marcado
   3.191 de 17.789 enlaces; con 30x, 13.
5. **Hay dos topes de referencia, no uno**: la sonda del EAN (precision) y el
   bloque canonico (40.303 productos, 32.873 pares). "El tope del EAN" sale hoy
   100 % por construccion y no mide nada.

**Consecuencia para este BACKLOG.**

1. La tarea 2 ("Grupos demasiado anchos") **sigue siendo el bloqueo numero uno**,
   con el diagnostico afinado: freno de grupo, no de par. Sus criterios siguen
   valiendo (>= 57 % de aciertos, de 405 grupos >200 % a menos de 150).
2. **N8 ("el boton *esto no es lo mismo*") queda anulado**: es validacion humana,
   que el encargo nuevo prohibe. Las colas de revision a mano de la tarea 2 y de
   `docs/FASES.md` tambien. Se sustituyen por un panel de auditoria que explica
   cada par sin que nadie apruebe nada.

---

## Antes de tocar nada

Lee, por este orden:

    docs/DATOS.md         que es parquet, DuckDB y las cuatro capas
    docs/CADENAS.md       que publica de verdad cada supermercado
    docs/COMPETENCIA.md   que hacen las otras apps y que nos llevamos
    plataforma/LEEME.md   como se levanta y que hay dentro

Y respeta estas cuatro reglas, que estan metidas en el codigo y **deshacerlas
rompe cosas que ya hemos aprendido por las malas**:

1. **Una letra de calidad sacada del precio no se llama calidad.** El 77 % de
   ellas salen de ordenar por precio, no de leer una etiqueta. La API devuelve
   `calidad` solo si viene de ingredientes, y `gama` si viene del precio.
   Mezclarlas produce la conclusion falsa de que lo barato es peor.
2. **Una oferta es una regla, no un precio.** "2a unidad -50%" no abarata el
   producto, abarata el par. Y los descuentos de tarjeta **no bajan el total**:
   no se descuentan en caja.
3. **Ninguna correccion de dato se aplica sin que algo independiente la
   confirme.** El patron esta en `pipeline.py`: el nombre dice "pack 24 x 33 cl"
   pero solo se multiplica si el precio resultante cuadra al 5 % con el que
   publica la cadena. De 211 candidatos se corrigieron 110; los 101 que no
   cuadran se quedaron como estaban.
4. **Cada precio lleva su fecha**, y uno de mas de tres dias se ensena pero no
   decide en que tienda comprar.

Comprobacion antes de dar nada por hecho:

    uv run pytest                    180 pruebas, todas en verde
    uv run ruff check plataforma/    limpio

---

## 1. Secciones comunes entre cadenas  ← EMPEZAR POR AQUI

**Por que.** Es lo que mas desbloquea de todo el proyecto: la lista ordenada por
pasillos (la mejora que mas se nota en el supermercado, y que tienen las tres
apps de lista), el "Explorar" de la app, la pantalla de secciones del panel y el
analisis por linea de producto. Hoy cada cadena tiene su arbol y no hay uno
comun.

**Lo que se creia y era falso.** Que esto pedia un clasificador de texto. No:
son **849 claves** en total, y ya hay un fichero con **el 97 % propuesto**.

**Lo que YA esta hecho** (17 de septiembre):

    core/datos/secciones.yml    849 claves, **todas asignadas**. Cobertura
                                medida: 99,9 % de los productos.
                                Alcampo, Carrefour, DIA y Mercadona al 100 %;
                                Aldi al 96,7 %.
    core/secciones.py           `seccion_de(fuente, categoria)`, `orden_de()`
                                y `sin_asignar()`. Sin dependencias.
    tests/test_secciones.py     13 pruebas, incluida una que avisa si una cadena
                                cambia su arbol y aparecen claves sueltas.

**Lo que falta:**

1. En `projects/cesta/emparejar.py`, anadir la columna `seccion` a
   `grupos.parquet`. **Y heredarla por grupo**: si un miembro del grupo tiene
   seccion y otro no, se la pasa. Medido: el 64,8 % de los productos que estan
   en un grupo podrian heredar la seccion del miembro de Alcampo.
2. En `plataforma/api/catalogo.py`, devolver `seccion` en buscar y en la ficha.
3. En la lista del movil, agrupar por seccion **dentro de "Por coger"**, usando
   `core.secciones.ORDEN`, que ya esta en el orden en que se recorre una tienda.
   Lo que no tenga seccion va al final, bajo "otros": **no se inventa una
   seccion** para que no quede feo.

**Como se sabe que esta bien.**

    - `uv run pytest tests/test_secciones.py` en verde (13 pruebas)
    - la columna `seccion` llega a grupos.parquet con >= 99 % de cobertura
    - la lista del movil se agrupa y el orden es el de recorrer la tienda
    - un producto sin seccion aparece bajo "otros", al final, y no desaparece

**Lo que NO hay que hacer.** Un clasificador. Si al final quedan restos sin
seccion, se miran y se anaden al fichero. El aprendizaje automatico aqui es una
red de seguridad para mas adelante, no el plan.

---

## 2. Grupos demasiado anchos

**Por que.** Es el bloqueo numero uno del panel y ensucia el comparador. El grupo
de agua con gas mas disperso mete Perrier (2,40 EUR/l) con la marca blanca de
Carrefour (0,28), **con todos los formatos bien leidos**. No es un fallo de
formato: es que "equivalente" se esta estirando demasiado.

Mientras siga asi, cualquier cifra de "diferencia de precio por seccion" mide lo
ancho que es el grupo y no el ahorro.

**Que hay que hacer.**

1. Medir primero: cuantos grupos tienen mas de N miembros y mas de X % de
   dispersion. Hoy hay 405 con mas del 200 %.
2. Probar dos frenos, por separado y midiendo cada uno contra el 57 % de
   aciertos de `emparejar --medir`:
   - **Tope de dispersion dentro del grupo**: si anadir un producto hace que el
     grupo pase de cierta relacion entre el mas caro y el mas barato, no entra
     como equivalente.
   - **Umbral por seccion** (necesita la tarea 1): en refrescos hace falta mas
     parecido que en legumbres, porque los nombres se parecen mas entre si.
3. Dejar una cola de revision: `data/debug/grupos_anchos.parquet` con los que
   quedan, para mirarlos a mano.

**Como se sabe que esta bien.**

    - los aciertos de `emparejar --medir` NO bajan del 57 %
    - los grupos con mas del 200 % de dispersion bajan de 405 a menos de 150
    - el grupo del agua con gas ya no mete Perrier con la marca blanca

**Cuidado.** La ultima vez que se toco el emparejador sin medir, la cobertura
bajo del 53 % al 43 % y costo entenderlo. Mide antes y despues, siempre.

---

## 3. Anadir sin escribir

**Por que.** Es lo que separa una lista que se usa de una que se abandona. Las
tres apps de lista lo tienen resuelto y nosotros no: hoy hay que escribir en un
buscador. En el pasillo, con una mano, eso es demasiado.

**Tres cosas distintas, en este orden de valor.**

### 3.1 Mosaico de lo habitual

Una cuadricula con lo que esa persona ha puesto mas veces en sus listas, con su
foto, a un toque. Es lo primero que se ve al abrir la pestana de buscar cuando
el campo esta vacio.

    dato        ya lo tenemos: lista_linea tiene anadido_por y anadido_en
    consulta    los 24 grupos que mas veces ha anadido ese usuario en 90 dias
    donde       plataforma/api/main.py (ruta nueva /api/habituales)
                plataforma/web/app.js (se pinta al vaciarse el buscador)

### 3.2 Voz

`SpeechRecognition` del navegador. Gratis, sin servidor y sin dependencias.
**No es un asistente**: es un atajo para no escribir. "dos litros de leche
entera" rellena el campo de busqueda y, si detecta cantidad, la propone.

Ojo: en iOS solo funciona en Safari y pide permiso. Si no esta disponible, el
boton del microfono **no se dibuja**, en vez de dibujarse y fallar.

### 3.3 Sugerencias del historial

"Sueles comprar leche y hace nueve dias que no la pones." Necesita unos meses de
listas hechas para no decir tonterias. **Anotado para diciembre**, no ahora.

**Como se sabe que esta bien.**

    - con el buscador vacio se ve el mosaico, y anadir algo desde ahi son dos
      toques (el producto y ya)
    - el boton de voz no aparece en un navegador que no lo soporta
    - las sugerencias no salen hasta tener 30 dias de listas

---

## 4. La oferta mientras anades

**Por que.** Es la idea buena de Tiendeo: *"puedes hacer la lista y al mismo
tiempo ver las promociones de los productos que estas anadiendo"*. Nosotros
podemos hacerlo mejor que ellos porque sabemos el precio **y la mecanica**: no
"hay una promo", sino "llevando dos, 1,50 EUR menos por unidad".

La pieza dificil ya esta hecha (`core/promos.py`, 10 pruebas en verde). Falta
ensenarla.

**Que hay que hacer.**

1. En el resultado de busqueda, el que tiene oferta lleva su sello (ya se hace)
   **y el texto de la mecanica traducido**: "3x2", "2a unidad -50%".
2. En la lista, si una linea tiene oferta aprovechable y llevas menos unidades
   de las que compensan, una linea pequena debajo: *"llevando 3 en vez de 2, la
   tercera sale gratis"*. `unidades_optimas` ya lo calcula.
3. Una pestana o filtro "solo con oferta" en la busqueda.

**Como se sabe que esta bien.**

    - un producto con "3x2" ensena la sugerencia cuando llevas 2
    - un producto con "Club Alcampo ... acum en tu tarjeta" NO la ensena,
      porque ese dinero no se descuenta en caja
    - el total de la lista baja al subir de 2 a 3 unidades en un 3x2

---

## 5. Notas por linea, y el aviso legal

Dos cosas pequenas que no cuestan casi nada.

**Notas.** El campo `nota` existe en `lista_linea` y la interfaz no lo usa.
"la de cristal", "si hay del grande". Un toque largo sobre la linea, o un lapiz.

**El aviso.** Copiar el de QueFalta porque es correcto y hay que decirlo:
*"Los precios son orientativos y pueden variar"* y *"Cesta no esta afiliada,
asociada ni patrocinada por ninguno de estos supermercados"*. En ajustes, y una
linea pequena bajo el total de la lista.

---

## 6. Traer de Open Food Facts lo que no traemos

**Por que.** Medido contra el volcado entero (7,9 GB, ya esta en
`data/externo/food.parquet`). De nuestros 12.835 productos que cruzan por codigo
de barras:

    nutrientes completos (kcal, grasas, azucares, sal)   11.723   <- no lo traemos
    categorias                                           10.209   <- no lo traemos
    sellos                                                8.055   <- no lo traemos
      sin gluten 2.667 | ecologico 1.205 | vegano 763
      sin lactosa 717 | sin aceite de palma 267
    origen                                                1.248   (solo 635 "en:spain")

**Que hay que hacer.** Tres lineas en `CAMPOS` de `core/off.py`
(`nutriments`, `categories_tags`, `labels_tags`) y llevarlas a gold.

Los **sellos** son el hallazgo util: dan filtros que la gente busca de verdad
("sin gluten", "sin lactosa", "vegano") y tienen entre dos y cuatro veces mas
cobertura que el origen.

**Lo que NO hay que prometer.** El filtro de producto nacional. Techo realista:
unos 1.900 productos de 52.575, el 3,7 %. No hay fuente que lo arregle — BEDCA
describe alimentos genericos, no productos con codigo de barras. Se queda
escondido y se dice por que.

---

## 7. Sondear las fichas de Alcampo y Aldi

**Por que.** Son el 50 % del catalogo y ninguno publica codigo de barras en el
listado. Sin EAN no hay cruce con Open Food Facts, y por tanto no hay
Nutri-Score, ni NOVA, ni ingredientes, para 25.600 productos.

DIA y Mercadona tampoco lo dan en el listado: lo dan en la **ficha**, y por eso
los dos tienen un maestro incremental que solo pide fichas que no conoce.

**Que hay que hacer.** Ejecutar `uv run python -m projects.cesta.sondear_fichas`
(escrito, sin lanzar: desde la sesion no hay salida a esos dominios). Pregunta
**una vez por un producto** a un punado de direcciones candidatas y cuenta que
trae cada respuesta.

    si alguna trae ean/gtin   escribir el maestro incremental calcado al de DIA
                              (collectors/dia.py, funcion `_ficha`). Ritmo lento,
                              fichero permanente: el EAN no cambia, se pide una
                              vez en la vida y el catalogo se cubre en semanas
    si solo trae nutricion    sigue mereciendo la pena: el EAN solo era el camino
    si no trae nada           se deja escrito en CADENAS.md y se deja de buscar

**Lo que NO hay que hacer.** Tirar 25.000 peticiones a ciegas contra el WAF de
Alcampo. Es la forma mas rapida de cerrar la puerta que hoy tenemos abierta,
despues de tres semanas costando que se quede abierta.

**Mientras tanto, y esto se puede hacer hoy:** 3.375 productos de Alcampo estan
enlazados como *identicos* a un producto con EAN de otra cadena y podrian
heredarlo, marcado como **inferido**, nunca como leido. Aldi no puede: todos sus
enlaces son *equivalentes*, porque es marca propia entera.

---

## 8. Escaner de codigo de barras

**Por que.** Es nuestra funcion diferencial. Yuka te dice si un producto es sano.
El lector de precios de Mi Carrefour te dice cuanto cuesta en Carrefour. **Nadie
te dice si esta mas barato en la tienda de al lado.** Y escanear con el movil en
la tienda ya es una costumbre establecida en Espana, asi que no hay que ensenar
el gesto.

**Lo que aguantan los datos** (medido el 17 de septiembre):

    codigos de barras que reconocemos                23.312
    ... de los que podemos comparar precio            9.811   (42 %)
    ... de los que tenemos algo de nutricion         10.826   (46 %)
    ... cuyo grupo llega hasta Alcampo                7.809   (34 %)

    por cadena:  Mercadona 100 % · DIA 100 % · Carrefour 93 %
                 Alcampo 0 % · Aldi 0 %

**El detalle que salva la funcion.** El codigo de barras es **del fabricante**,
no de la cadena. Escaneando una Coca-Cola dentro de un Alcampo, el codigo casa
con la fila de Carrefour, y como el grupo incluye tambien la de Alcampo
(emparejada por nombre), se puede comparar igual. Lo que no funcionara nunca es
escanear la marca propia de Alcampo o de Aldi: esos productos no tienen codigo en
nuestro catalogo.

### Lo tecnico

    Chrome Android     `BarcodeDetector` nativo. Funciona.
    Safari iOS         **NO lo soporta**, desactivado por defecto
    Firefox            tampoco

Asi que:

1. `if ('BarcodeDetector' in window)` → usar el nativo, cero dependencias.
2. Si no → **cargar perezosamente** `zxing-wasm` (variante solo lectura,
   ~1,04 MiB, MIT/Apache 2.0, lee EAN-13 y EAN-8). Solo se descarga cuando hace
   falta, no en cada visita.
3. La camara pide `getUserMedia` con `facingMode: 'environment'` y **solo
   funciona en HTTPS o en localhost**. Detras de Tailscale con http:// no va:
   hay que resolverlo con el certificado de Tailscale (`tailscale cert`) o
   avisar de que el escaner solo va en el PC.

**Esto ultimo hay que comprobarlo antes de prometer nada.** Si no hay HTTPS, el
escaner no existe, por bien que este programado.

### Las cuatro respuestas que tiene que saber dar

El escaner falla mas veces de las que acierta, y eso **no es un fallo: es el
dato**. Las cuatro pantallas tienen que estar disenadas, no solo la buena:

    1. LO CONOZCO Y PUEDO COMPARAR      (42 % de los codigos)
       "Atun Calvo 3x80 g — 3,45 EUR aqui. En Alcampo 2,89 (-16 %)"
       + la ficha entera + boton de anadir a la lista

    2. LO CONOZCO PERO SOLO EN UNA CADENA
       "Lo tengo en DIA a 3,45 EUR. No lo encuentro en las demas."
       No inventar una comparacion que no existe.

    3. NO LO CONOZCO                     (lo mas frecuente en Alcampo y Aldi)
       "No tengo este codigo. Puede ser marca propia de Alcampo o Aldi, que no
        publican codigo de barras."
       + buscador por nombre como salida, no un callejon sin salida.

    4. NO TENGO NUTRICION                (54 % de los que conozco)
       El precio se ensena igual. Donde iria la nota, pone **"no lo se"**, no
       un cero ni una nota gris. La OCU critica exactamente esto en Yuka y
       El CoCo: base de datos incompleta que da notas inexactas.

### Como se sabe que esta bien

    - escanear un EAN conocido de Mercadona ensena la comparacion en menos de
      dos segundos desde que se enfoca
    - escanear un codigo inventado ensena la pantalla 3, con el buscador
    - en un navegador sin camara o sin permiso, el boton del escaner NO SE
      DIBUJA (no se dibuja y falla: no se dibuja)
    - el wasm NO se descarga en Chrome Android
    - una prueba de `GET /api/ean/{codigo}` con: codigo conocido multicadena,
      conocido de una sola, desconocido, y codigo mal formado

---

## 9. La nota del producto, rehecha

**Por que.** Nuestra letra A/B/C de hoy es una posicion **dentro del grupo**, y
cuando ningun producto del grupo publica ingredientes cae a ordenar por precio:
**el 76,9 % de las letras son el precio disfrazado**. Ya nos hizo publicar una
conclusion falsa una vez ("la marca blanca es peor") y la app tiene que llamarla
`gama` para no mentir.

**La solucion no es parchear: es cambiar de nota.** Yuka tiene su formula
publicada y es mejor porque es **absoluta**:

    60 %   calidad nutricional    la metodologia del Nutri-Score
    30 %   aditivos               con tope en 49/100 si hay uno de riesgo alto
    10 %   ecologico              bonus si lleva sello organico oficial

**Lo que tenemos para calcularla:**

    Nutri-Score          8.359 productos
    ingredientes          6.863
    al menos uno de los dos           11.724   (22,6 % del catalogo)
    sellos de OFF (tarea 6)            8.055   → el 10 % de ecologico

**Lo que hay que conservar del sistema actual**, y es lo que nos distingue de
Yuka: **la procedencia**. Un producto sin datos no saca un cero, saca **"no lo
se"**. Eso es justo lo que la OCU echa en falta en Yuka y El CoCo.

**Lo que ya esta bien y no hay que tocar.** Nuestro contador de aditivos exige
`E` seguido de tres o cuatro digitos, asi que **no cuenta los aromas como
aditivos**, que es el error que la OCU documenta en Yuka y MyRealFood.
Comprobado el 17 de septiembre: 2 falsos positivos en 400 productos revisados.
Si tocas `core/calidad.py`, vuelve a comprobarlo.

### Como se sabe que esta bien

    - un producto sin Nutri-Score ni ingredientes devuelve `nota: null` y la
      app pone "no lo se", nunca un numero
    - un producto con un aditivo de riesgo alto no pasa de 49
    - la nota NO cambia al cambiar de grupo (es absoluta: esa es toda la gracia)
    - se conserva `gama` para ordenar dentro de un grupo, y se sigue llamando
      gama

---

## 10. Guardar el cierre de compra

**Por que.** Es barato ahora e imposible de recuperar despues. Sin esto, en
diciembre no habra historial que mirar, y todo lo de la seccion D de
`FUNCIONALIDADES.md` (despensa deducida, sugerencias, "sueles comprar leche cada
nueve dias") no tendra con que funcionar.

**Que hay que hacer.** Una tabla `compra`:

    compra        id, lista_id, cerrada_por, cerrada_en, cadena_elegida,
                  total_estimado_cent
    compra_linea  compra_id, grupo_id, producto_id, cantidad, precio_cent

Y un boton "he terminado la compra" en la lista que: guarda las lineas que
estaban en el carro, las quita de la lista, y deja las que no se cogieron.

**Como se sabe que esta bien.**

    - cerrar una compra vacia la parte "en el carro" y deja "por coger"
    - el historial queda consultable en /api/compras
    - cerrar dos veces no duplica (idempotente por lista y minuto)

---

## 11. Lo que se llena solo

No hay nada que programar. Se apunta para que nadie lo de por roto:

    tendencia_30d       necesita 30 dias   →  5 de octubre
    oferta_sospechosa   necesita 45 dias   →  20 de octubre
    posicion_90d        necesita 90 dias   →  diciembre
    estacionalidad      necesita un ano    →  septiembre de 2027

`oferta_sospechosa` da hoy cero casos porque compara con el precio de hace 45
dias y llevamos doce. **No esta roto: esta esperando.** El panel ya lo dice en
pantalla, con los dias que faltan.

---

## 12. Mas adelante, y por que no ahora

**Recetas a lista.** Util de verdad, pero es un modulo entero: guardar recetas,
sacar ingredientes, casarlos con productos del catalogo (que es el mismo
problema del emparejador, otra vez). Despues de 1 a 4.

**Clasificador de texto para las secciones.** Solo si tras la tarea 1 quedan
restos sin colocar. Hay 10.209 ejemplos etiquetados gratis en Open Food Facts.
TF-IDF y regresion logistica; ni se te ocurra una red neuronal con ese volumen.

**Modelo para el emparejador.** Hay 1.748 pares verdaderos gratis (mismo EAN
entre cadenas). Riesgo conocido: que aprenda de los productos que tienen EAN
(marcas conocidas) y falle justo en marca blanca, que es lo que importa. Hay que
medirlo separando los dos casos antes de creerselo. **Y despues de la tarea 2**,
porque los grupos anchos no los arregla un modelo.

**App nativa y widget.** Hoy somos una web servida por Caddy. Un widget pide app
nativa y eso es otro proyecto.

**Mas cadenas.** QueFalta tiene 19 y nosotros 5, pero las nuestras **se comparan
entre si**. Anadir cadenas sin poder emparejarlas es cambiar lo que nos hace
utiles por una lista mas larga.

---

## 13. Lo que no se hace nunca

- **Resolver el CAPTCHA de Alcampo**, ni a mano ni automatizado.
- **Abrir un puerto en el router.** Hay un PostgreSQL detras. Tailscale, y ya.
- **Ensenar un numero sin decir de cuando es** ni sobre cuantas filas se ha
  calculado.
- **Llamar calidad a una letra que sale del precio.**
- **Restar del total un descuento que no se descuenta en caja.**
- **Escribir en `data/gold/` desde la plataforma.** Lo escribe el pipeline, se
  monta en solo lectura, y esa frontera es lo que permite arreglar una mitad sin
  tocar la otra.

---

# Lo que sigue, despues de la pasada del 17 de septiembre (tarde)

Ordenado por **valor / coste**. Los cinco primeros no necesitan red: el dato ya
esta en `data/raw`.

## A. Sin pedirle nada a ninguna web

### A1. Texto de oferta de DIA y Mercadona — 0 % hoy
Las dos saben que hay oferta (`is_promo_price`, `price_decreased`) pero no
publican **cual** en el listado. Sin el texto no se puede aplicar
`core/promos.py`, que es lo que convierte "2ª unidad -50 %" en un precio real.

**Pasos**: (1) leer 200 fichas de DIA y 200 de Mercadona con el localizador de
`rehacer_maestro.py`; (2) contar cuantas traen texto de promocion y con que
clave; (3) si aparece, anadirlo a `_maestro_de_ficha` y a `a_registro`; (4)
medir cuantas de esas frases entiende `promos.lee()`.
**Valor**: hoy el 13 % del catalogo tiene texto de oferta y son solo Alcampo y
Carrefour. Con DIA y Mercadona pasaria de 6.800 a ~12.000.

### A2. Conservacion de DIA — 0 % hoy
`item_treatment_type` esta en las 5.410 fichas guardadas y no se lee. El filtro
"congelado" hoy no cubre DIA.
**Pasos**: contar los valores distintos, traducirlos en `core/sellos.py`
(`_CONSERVACION`), cablear, medir.

### A3. Categoria estructurada de DIA
`family_code`, `subfamily_code`, `section_code` en el 100 % de las fichas. Hoy la
seccion de DIA se deduce de su URL (`core/secciones.py`). Un arbol de verdad es
mejor que dos trozos de URL, y ademas permite comprobar `secciones.yml` contra
algo que no sea nuestra propia adivinanza.

### A4. `isRecall` de Aldi
Booleano en los 2.065 productos, hoy `false` en todos. **Ninguna app de la
competencia avisa de retiradas de producto**, y nosotros sabemos que hay en cada
lista. Pasarlo a bronze cuesta una linea; cuando deje de ser cero, ya habra donde
engancharlo.
Fuente externa complementaria: las alertas de AESAN, que son publicas.

### A5. `main_feature` y `badges` de Mercadona
`main_feature` (58 %) dice "ultracongelado", "lonchas", "antitranspirante": es
`tipo_producto` gratis para 2.500 productos. `badges.requires_age_check` marca
los que llevan alcohol.

## B. Con red, en orden de valor

### B1. Fichas de Alcampo y Carrefour — el agujero grande
77 % del catalogo sin **nada** de composicion. Es la razon de que la letra de
calidad se calcule ordenando por precio en el 77 % de los casos.
`projects/cesta/sondear_fichas.py` existe y **no se ha ejecutado nunca**.
Ver `docs/PARIDAD-CAMPOS.md`, punto 3.1, y `docs/PATCHRIGHT.md` para el WAF de
Alcampo.

### B2. Origen en Carrefour y Alcampo
Aldi enseno que el origen puede estar donde no se busca: en un logotipo y dentro
de una descripcion. Merece una pasada especifica sobre el crudo de las otras dos
antes de volver a decir que el filtro "producto espanol" es imposible.

## C. Lo que ya estaba pendiente y sigue

1. **Los grupos son demasiado anchos** (F2). Sigue siendo el bloqueo numero uno:
   el grupo del agua junta Perrier (2,40 EUR/l) con marca propia (0,28) **con los
   formatos leidos bien**. Bloquea el panel y el "mejor y mas barato".
   Ahora hay dos senales nuevas que no habia: `tipo_producto` (DIA, 5.410) y
   `envase` (8.829). Dos productos con envase distinto casi nunca son el mismo.
2. **No esta en git.** Decision de David, pero cada pasada como la de hoy toca 20
   ficheros y no hay forma de ver el diff ni de volver atras.
3. **La plataforma nunca se ha levantado con Docker.** Solo piezas sueltas.
4. **HTTPS para el escaner** (`tailscale cert`) sin verificar. Bloquea F5.

## D. Reglas que han salido de esta pasada y conviene no perder

1. **Antes de pedirle un campo nuevo a una web, buscarlo en `data/raw`.** Ha
   aparecido ahi las siete veces que se ha mirado.
2. **Un dato que no cruza la frontera de gold no existe.** Al anadir una columna
   al contrato, anadirla en el mismo commit a `emparejar.COLUMNAS` y a
   `docs/PARIDAD-CAMPOS.md`.
3. **Un centinela no es una fecha ni un numero.** 2030-12-31 en Aldi, 999 dias en
   DIA. Al leer un campo nuevo, mirar primero los valores mas repetidos.
4. **Un campo que se llama X no siempre es X.** `drained_weight` de DIA es el peso
   neto. Comprobarlo contra otra columna antes de creerselo.
5. **El texto se filtra por grupo; un atributo, por producto.**
6. **Cada valor viaja con su procedencia.** `calidad_origen`,
   `proc_precio_unidad` y ahora `sellos_origen`.

---

# Lo siguiente, tras la tercera pasada del 17 de septiembre

La seccion anterior sigue valiendo. Esto es lo que ha cambiado de sitio y lo
nuevo, con las especificaciones desglosadas para que se pueda hacer de una
sentada cada cosa.

## Ya hecho de la lista anterior

- ~~A1. Texto de oferta de DIA~~ → 221 productos, y 200 marcados `promo_club`.
- ~~A4. `isRecall` de Aldi~~ → columna `es_recall`, aviso en rojo en la ficha.
- Y ademas, sin estar en la lista: la fecha de fin de las ofertas de Alcampo
  (1.904), el peso al peso de Alcampo (742), el peso escurrido de Mercadona
  (179), los pictogramas de peligro (450), el distintivo de DIA (550) y el
  filtro "sin alcohol" (3.316).

## N1. El numero real de unidades de un pack — Mercadona, 1.320 productos

**Alto nivel**: hoy, cuando una cadena dice "1 ud" y su precio por unidad
sugiere que el envase trae mas piezas, lo deducimos dividiendo
(`unidades_inferidas`). Mercadona publica el numero exacto en
`price_instructions.total_units`, y el tamano de cada pieza en `pack_size`.

**Desglose**:

1. Medir sobre el crudo cuantos de los 1.320 tienen ademas `pack_size`, y
   comparar `total_units` con el `unidades_inferidas` que calculamos hoy: cuantos
   coinciden, cuantos no, y en los que no, quien acierta. **Sin esta medicion no
   se toca nada**: es la unica forma de saber si el heuristico es bueno.
2. Anadir `unidades_envase` (Int32) al contrato solo si el paso 1 dice que el
   heuristico falla en mas del 5 %.
3. Cablearlo en `mercadona.a_registro`.
4. En `pipeline.a_silver`, dar prioridad a lo declarado sobre lo deducido, y
   dejar `unidades_inferidas` como respaldo. Ojo al orden: `unidades_inferidas`
   ya interactua con la regla de "precios en disputa" (ver
   `docs/PRECIO-POR-UNIDAD.md`, punto 3.1).
5. Prueba: un pack de 6 yogures de 125 g debe dar 6 unidades y 0,75 kg, y el
   precio por kilo tiene que cuadrar con el de la etiqueta de Mercadona.

**Criterio de aceptacion**: el numero de filas "en disputa" no sube, y al menos
1.000 productos pasan de unidades deducidas a unidades declaradas.

## N2. La conservacion de DIA — hoy 0 %

**Alto nivel**: `item_treatment_type` esta en las 5.410 fichas guardadas y no se
lee. El filtro "congelado" hoy no cubre DIA, que es el 10 % del catalogo.

**Desglose**:

1. `uv run python -m projects.cesta.auditar_crudo --fuente dia --minimo 0.5` y
   buscar el campo en la salida; si no aparece, es que esta en la ficha maestra y
   no en el listado: mirarlo con el localizador de `rehacer_maestro.py`.
2. Contar los valores distintos y cuantos productos tiene cada uno.
3. Traducirlos en `core/sellos._CONSERVACION`, que es donde vive el vocabulario.
4. Cablear en `_maestro_de_ficha` (guardando **la palabra de DIA**, no la
   nuestra: ver la regla de `data/master` en `docs/OPERACION.md`) y normalizar en
   `a_registro`.
5. `rehacer_maestro --fuente dia` + `reprocesar --fuente dia` y medir.

**Criterio de aceptacion**: `conservacion` de DIA pasa de 0 a mas de 1.500, y el
filtro "congelado" devuelve congelados de DIA.

## N3. El arbol de categorias de DIA — 5.410 productos

**Alto nivel**: hoy la seccion de DIA se deduce de dos trozos de su URL
(`core/secciones.py`). Su ficha trae `section_code`, `family_code` y
`subfamily_code` en el 100 %: un arbol de verdad.

**Desglose**:

1. Sacar el arbol completo (codigo → cuantos productos) de las fichas guardadas.
2. Cruzarlo con lo que hoy adivina `secciones.clave_de("dia", url)`: cuantos
   coinciden y cuantos no. **Esto es lo valioso**: es la primera vez que se puede
   comprobar `secciones.yml` contra algo que no sea nuestra propia adivinanza.
3. Si el arbol es mejor, anadir `seccion_cadena` al contrato y usarlo como clave
   preferente en `secciones.seccion_de`.
4. Volver a medir la cobertura de secciones (hoy 99,9 %) y los productos mal
   clasificados.

**Criterio de aceptacion**: se publica el numero de discrepancias entre el arbol
de DIA y `secciones.yml`, y se corrige el fichero donde el arbol tenga razon.

## N4. El "2ª unidad" estructurado de Alcampo — 509 productos

`promotions[].requiredProductQuantity` da el N sin leer el texto. Hoy
`core/promos.py` lo saca con una expresion regular y acierta el 69 % de los
textos de Alcampo. Usar el campo cuando exista es gratis y elimina una
adivinanza.

**Desglose**: (1) comparar el N del campo con el `a` que deduce `promos.lee()` en
esos 509; (2) si no coinciden, ver quien acierta mirando el precio; (3) si el
campo gana, pasarlo a `a_registro` y que `promos.lee()` lo acepte como pista.

## N5. Las fichas de Alcampo y Carrefour — sigue siendo el agujero grande

77 % del catalogo sin **nada** de composicion, y es la razon de que la letra de
calidad se calcule ordenando por precio en el 77 % de los casos.
`projects/cesta/sondear_fichas.py` existe y **no se ha ejecutado nunca**, porque
ninguna de las sesiones que han escrito este codigo tiene red hacia esos
dominios. Es la primera tarea de quien si la tenga.

## N6. Una sexta cadena

Estudiado y aparcado, con el motivo:

| cadena | tamano | por que no, hoy |
|---|---|---|
| **Lidl** | ~650 tiendas | investigado y descartado: no publica precios por internet en Espana. Ver `docs/LIDL.md` |
| **Eroski** | ~1.600 | **la mejor candidata**. Tiene tienda online con precios. No se ha podido sondear: ninguna sesion ha tenido red hacia `eroski.es` |
| **Consum** | ~800 | tienda online propia, fuerte en Levante. Mismo problema de red |
| **BonÀrea** | ~500 | catalogo propio, muy integrado. Sin sondear |

**Antes de escribir una linea de colector nuevo**: `sondear_fichas.py` contra la
cadena, medir que campos publica y rellenar su fila en
`docs/PARIDAD-CAMPOS.md`. Una cadena que no publique precio por unidad ni
formato no suma; suma ruido en los grupos.

## N7. Los grupos demasiado anchos (F2) — sigue siendo el bloqueo numero uno

Y ahora se sabe algo mas: **el envase no sirve para separarlos**. De los 980
enlaces donde las dos cadenas publican envase, 372 (38 %) no coinciden, y son el
mismo producto con distinta palabra. `tipo_producto` tampoco, todavia: solo lo
publica DIA, asi que hay cero enlaces con el dato en las dos puntas.

Lo que si hay nuevo para intentarlo: `peso_neto_g` (5.436 productos) permite
comparar un producto vendido por volumen con otro vendido por peso, que hoy
caen en grupos distintos.

## Reglas nuevas de esta pasada

7. **Ejecuta `auditar_crudo.py` antes de pedirle un campo nuevo a una web.** Ha
   acertado las ocho veces.
8. **`\b` no delimita numeros pegados a puntuacion.** Usa `(?<!\d)` y `(?!\d)`.
   Ha fallado dos veces el mismo dia: con `€` y con `_`.
9. **Un patron de texto se escribe con limites de palabra o no se escribe.**
   "eco" dentro de "seco", "champ" dentro de "champu". Dos veces el mismo dia.
10. **Un filtro de exclusion y uno de inclusion se afinan al contrario.** En "sin
    gluten" (incluir) pasarse es peligroso; en "sin alcohol" (excluir) quedarse
    corto es lo peligroso. Ver `core/alcohol.py`.
11. **Medir y descartar tambien es un resultado, y se escribe con su numero.**
    Las valoraciones de Alcampo (1.260 votos en total) y el texto largo de
    Carrefour (no rescata ninguna oferta) estan documentados para que nadie
    repita el trabajo.

---

# Lo siguiente, tras la revision de la ingesta del 18 de septiembre

## Hecho hoy

- ~~N1. Unidades reales de los packs de Mercadona~~ → 1.087 productos. Medido
  antes de tocar nada, como pedia la especificacion: de los 1.256 con
  `total_units`, nuestra deduccion **acertaba 169 y fallaba 1.087**. La ficha
  dice ya "6 × 125 g · 0,42 € cada una".
- `core/cobertura.py`, el control que faltaba: ¿falta media tienda?
- Reintentos y rescate en Carrefour; `precio_comparable` llega a gold; cupo de
  fichas de DIA adaptativo; `core/comparacion.py` con la frontera compartida.

## N8. El boton "esto no es lo mismo" — la idea que mas vale de la competencia

**Alto nivel.** Los grupos demasiado anchos son el bloqueo numero uno y llevamos
tres intentos de arreglarlo desde el algoritmo. Soysuper lo resuelve por otro
lado: deja que la persona rechace un equivalente. Cada rechazo es informacion que
no se puede sacar de ningun dato de la cadena.

**Desglose.**

1. Tabla en PostgreSQL: `par_rechazado(producto_a, producto_b, quien, cuando)`,
   con los dos ids en el orden canonico (el menor primero) para que no haya
   duplicados cruzados.
2. `DELETE`/`POST /api/grupo/{id}/no-es-lo-mismo` con los dos `producto_id`.
   Requiere sesion: un rechazo anonimo no se puede deshacer ni auditar.
3. En la ficha del grupo, junto a cada producto que **no** sea el que se esta
   mirando: un enlace pequeno "no es lo mismo". Nada de iconos: hay que leerlo.
4. El emparejador exporta los rechazos a `data/gold/rechazos.parquet` antes de
   correr y `core/matching.enlaces()` los descarta al emitir. **Ojo**: los
   rechazos son pares de `(fuente, id_fuente)`, no de posiciones, porque las
   posiciones cambian cada dia.
5. Prueba: rechazar un par y comprobar que al dia siguiente el grupo se parte.

**Criterio de aceptacion.** Un rechazo sobrevive a un ciclo completo de pipeline
y emparejador, y el producto rechazado deja de aparecer en el grupo.

**Cuidado.** Un rechazo parte el grupo, pero el union-find los puede volver a
unir por un tercer producto (A–B rechazado, pero A–C y C–B siguen). Hay que
decidir y escribir que se hace: lo honesto es que el rechazo pese sobre el grupo
entero, no solo sobre ese par.

## N9. "Lo de siempre"

Soysuper aprende los productos habituales. Nosotros tenemos las listas y quien
anadio que: una consulta de quince lineas sobre `lista_linea` da los productos que
aparecen en mas de la mitad de las compras del ultimo mes. Pantalla: un boton
"anadir lo de siempre" en una lista vacia.

## N10. Avisos de retirada de producto, con AESAN

**Alto nivel.** El 17 de septiembre se construyo la columna `es_recall` y el aviso
rojo de la ficha, y hoy solo puede alimentarlos Aldi, que lo tiene a cero. AESAN
publica las retiradas oficiales de toda Espana. Con esa fuente, el aviso cubre las
cinco cadenas y pasa a ser **lo unico de la lista que ninguna app tiene**.

**Desglose.**

1. Colector nuevo, `projects/cesta/collectors/aesan.py`. Una pagina al dia. El
   listado esta en `aesan.gob.es/.../alertas_alimentarias/`, con una referencia
   estable por alerta (`ES2026/067`) y una URL por alerta. **No hay RSS ni API**:
   es HTML, que es lo que este proyecto ya sabe tratar.
2. Guardar en `data/raw/fuente=aesan/` como todo lo demas, y en
   `data/gold/alertas.parquet`: referencia, fecha, producto, marca, lote, motivo.
3. Emparejar con el catalogo por marca + nombre, con el umbral **alto**: un falso
   positivo aqui asusta a alguien sin motivo, y un falso negativo lo deja sin
   avisar. Escribir cual de los dos errores se prefiere **antes** de elegir el
   umbral (aqui, al contrario que en el alcohol, los dos son malos: hay que ser
   conservador y ensenar la alerta con el texto de AESAN al lado, para que la
   persona juzgue).
4. En la lista de la compra, banda roja arriba si algo de la lista casa con una
   alerta viva. En la ficha, el aviso que ya existe.
5. Caducar las alertas: AESAN no las retira, asi que hay que decidir cuanto dura
   viva una (tres meses es razonable) y escribirlo.

**Criterio de aceptacion.** Una alerta real de las ultimas semanas aparece
enganchada al producto correcto del catalogo, y ninguna alerta engancha con un
producto que no es.

## N11. Eroski y Consum — CERRADO el 19: Eroski se lee entera (ver docs/EROSKI.md)

Comprobadas las dos, y salen distinto: **Eroski se puede leer** y Consum no, por
una razon que no tiene nada que ver con reto alguno.

- **Eroski**: **RESUELTA.** Se lee entera con un cliente HTTP normal: ni
  navegador, ni reto, ni zona AJAX. La categoria hoja trae los productos
  servidos por el servidor con el precio dentro de un `data-metrics` de GA4
  (precio, id, nombre, marca y la categoria en tres niveles), el precio por kilo
  en texto ("1 KILO A 1,95 €") y las **valoraciones de clientes**, que no publica
  ninguna de nuestras cinco cadenas. El menu da **1.593 categorias de una sola
  peticion**: el recorrido esta resuelto antes de empezar.

  No publica **codigo de barras** en el listado ni JSON-LD. Queda por sondear la
  ficha (`/es/productdetail/<id>-<slug>/`), que es lo unico que falta.

  **Lo que decide si entra no es nada de eso**: es cuantos grupos comparables
  nuevos salen al pasar sus productos por el emparejador. Sin EAN hay que
  emparejar por nombre y formato. Bajar 20 categorias hoja, emparejarlas contra
  el catalogo actual y **contar**. Si anade catalogo y no anade comparaciones, no
  compensa.

  Detalle, y las cuatro veces que el sondeo dio un falso veredicto, en
  `docs/EROSKI.md`.

- **Consum**: la ficha de producto es una SPA -- `tienda.consum.es/es/p/<slug>/<id>`
  devuelve un *spinner* y nada mas --, asi que el unico camino al dato es su API.
  Y su `robots.txt` dice literalmente **`Disallow: /api/`**. El unico camino es el
  que el sitio prohibe. Cerrado.

Que otros lo hagan no lo reabre: `github.com/seravifer/supermarket-tracker` baja
Consum, y eso confirma que el dato esta ahi, no que nos toque cogerlo.

**La sexta cadena, si la hay, es Ahorramas** — ver N15.

## N15. Ahorramas — la unica candidata que ha pasado el filtro

Comprobado el 18 de septiembre, desde fuera:

    robots.txt     permisivo para categorias y fichas; prohibe carrito, login,
                   busqueda y `*ver-todo*`. Declara sitemap_index.xml
    sitemaps       sitemap_0-product.xml y sitemap_2-category.xml,
                   actualizados el 16 de septiembre
    fichas         URL limpia: /miel-de-flores-mel-da-anta-800g-47.html
    plataforma     Salesforce Commerce Cloud (el robots.txt menciona demandware)

Tres preguntas, en este orden, y **ninguna necesita escribir un colector**:

1. `GET` de una categoria con un cliente HTTP normal. ¿Viene el precio en el HTML?
   Buscar `€`, `data-product`, `application/ld+json`.
2. Si no: ver que peticion trae la rejilla. En SFCC suele ser
   `.../Search-UpdateGrid?cgid=<categoria>&start=0&sz=24`. Comprobarla contra el
   `robots.txt`, que hoy **no la prohibe**.
3. Si el precio esta: contar productos y comprobar que hay **precio por unidad**.
   Sin eso entra en el catalogo pero no en la comparacion.

Y la pregunta que decide de verdad, antes de la primera linea de colector:
**¿cuantos de sus productos emparejarian con los que ya tenemos?** Cruzar sus EAN
-- si los publica -- contra nuestros 25.094 productos con codigo de barras. Una
cadena que anade 8.000 productos y 30 grupos comparables no anade nada. La
competencia lo demuestra: RadarSuper cubre siete cadenas y ensena **177**
referencias comparables.

## N12. Open Prices: leer si, mezclar no

`https://prices.openfoodfacts.org`, API REST con busqueda por codigo de barras.
**Licencia ODbL, share-alike**: mezclarla con `data/gold` obliga a publicar la
base combinada como datos abiertos el dia que esto salga de casa. Para contrastar
un precio suelto vale; para meterla en el pipeline hay que decidirlo a proposito.
Y para Espana esta casi vacia.

## Reglas nuevas del 18 de septiembre

12. **Una ejecucion sin errores no es una ejecucion correcta.** "Cero errores"
    significa que nadie fallo, no que este todo.
13. **Un control de calidad de una captura tiene que mirar la FORMA del
    catalogo, no solo su tamano.** Un total puede bajar un 13 % por mil razones;
    una rama que se queda en el 3 % de lo que tenia, no.
14. **Un 403 no es un "no" definitivo.** Es "ahora no". Reintentar y volver mas
    tarde recupero el 91 % de lo que Carrefour perdio.
15. **Un dato derivado mas nuevo que su origen es un dato huerfano, y manda.**
    El silver del 18 sobrevivio a su bronze y volvio a colar el catalogo roto.
16. **La misma regla escrita en dos sitios acaba siendo dos reglas distintas.**
    "Diferencia imposible" eran 3 veces en el resumen y 30 en la interfaz.

---

# Datos de las cadenas que todavia no pedimos (18 de septiembre, tarde)

Hasta ahora se auditaba **que campos** no leiamos de las respuestas que ya
bajabamos (`auditar_crudo.py`). Falta la otra mitad: **que respuestas no pedimos
nunca**. Dos hallazgos, uno ya arreglado y otro por investigar.

## Arreglado hoy: 32 categorias de Alcampo que no llegaban por ningun camino

`auditar_recorrido.py` y el arreglo del nodo de navegacion vacio. Ver
`docs/AUDITAR-RECORRIDO.md`. Son, entre otras, "Lacteos sin lactosa", "Sin Gluten
/ Sin Lactosa", "Arroz Ecologico", "Pollo Ecologico", "Sobrasada", "Ron Premium".

## N13. Endpoints que aparecen en el crudo y no pedimos nunca

Buscando rutas de API **dentro de las respuestas que ya tenemos guardadas**,
salen estos. Ninguno esta probado: ninguna de las sesiones que han escrito este
codigo tiene red hacia esos dominios, asi que lo que sigue es una lista de sitios
donde mirar, no una promesa.

### Carrefour — tiene un buscador con API propia

    /search-api/query/v1/search
    /search-api/suggestions/v1/empathize
    /search-api/suggestions/v1/nextqueries
    /search-api/suggestions/v1/relatedtags

Hoy Carrefour se recorre por categorias desde su sitemap: 653 peticiones que
Cloudflare puede cortar, y esta manana corto 373. **Un buscador es un segundo
camino al mismo catalogo**, y sobre todo un camino de rescate: las categorias que
dan 403 se podrian intentar por termino de busqueda.

Alcampo ya usa esa idea para otra cosa (completar las categorias que tocan el
tope de 300 con 600 terminos de busqueda al dia), asi que el patron esta escrito
y probado en `alcampo.py`.

**Desglose**: (1) pedir a mano una busqueda y ver que devuelve y con que forma;
(2) medir cuantos productos distintos da una lista de 200 terminos frente a los
16.416 del recorrido por categorias; (3) si cubre bien, usarlo **solo como
rescate**, no como camino principal: un buscador nunca garantiza el catalogo
entero.

### DIA — buscador, tiendas y folletos

    /search-back-api-service-v1        el buscador
    /plp-back-api-service-v1           el listado, que ya usamos por otra puerta
    /tiendas  /tiendas/buscador-tiendas-folletos

Lo de **folletos** es lo interesante: son las ofertas de la semana, y hoy solo
tenemos 221 textos de oferta de DIA (el 4 % de su catalogo). Un folleto trae
ofertas que no siempre estan marcadas en el listado.

Y `/tiendas` abre una puerta que no tenemos: **que tiendas hay y donde**. Hoy la
app no sabe si tienes un DIA cerca; la preferencia "cadenas cerca" se rellena a
mano. Con las coordenadas de las tiendas se podria proponer.

### Mercadona — 2 categorias sueltas

"Jamon serrano" y "Perfume y colonia mujer" el 18, 1 el 17. Es ruido de un arbol
que cambia, no un agujero. No hay nada que arreglar.

### Lo que NO se va a usar, dicho a proposito

    /cloud-api/carts-api-form/v1/carts/...     el carrito de Carrefour

Aparece en su crudo y no se toca. Esta aplicacion lee precios; no mete nada en el
carrito de nadie ni simula ser un cliente comprando. Anotado aqui para que quede
claro que se vio y se descarto.

## N14. Lo que sigue sin poder mirarse

Eroski y Consum, y las fichas de producto de Alcampo y Carrefour (el 77 % del
catalogo sin composicion). Las tres cosas necesitan red hacia esos dominios, que
ninguna sesion ha tenido. Es la primera tarea de quien la tenga.

---

# Lo nuevo de la tarde del 18 de septiembre

## N16. Las 199 ofertas de Aldi que todavia no han empezado — LA GRANDE

`promotionPrices` trae, en **317 de los 2.175 productos de Aldi (14,6 %)**, la
oferta completa: `validFromLocalDate`, `validUntilLocalDate`, `priceValue`,
`strikePrice.strikePriceValue` y `priceTagLabels.promoText1`. Y de esas 317,
**199 empiezan mas adelante**:

    Vino tinto crianza DOCa Rioja   6,99 -> 3,99   -42 %   del 19 al 22
    Pack de 2 vinos blancos        14,99 -> 11,99  -20 %   del 19 al 22
    Leche omega 3                   1,89 ->  1,69  -10 %   del 21 al 27

El colector **las ve y las tira**: hay un comentario en `aldi.py` que lo dice
("62 de las 174 promociones de hoy aun no han empezado") y solo las usa para
fijar el `validUntil` del precio de hoy.

Ninguna de las aplicaciones estudiadas hace esto. Todas contestan "cuanto cuesta
hoy" o "cuanto costaba antes". Esto contesta **"no lo compres hoy: el sabado baja
un 42 %"**, que es la pregunta que de verdad ahorra dinero. Y no es una
prediccion: es la cadena publicando su calendario.

**Desglose**: (1) cinco columnas nuevas `promo_futura_desde|hasta|cent|antes_cent|
origen`, de bronze a gold; (2) seleccion: de las entradas con `validFromLocalDate
> hoy`, la mas proxima, y a igualdad de dia la mas barata; (3) **jamas** meter ese
precio en `precio_cent` ni en la serie historica, que es el error facil; (4) aviso
en la linea de la lista y pantalla "espera unos dias" ordenada por lo que se
ahorra en esa lista; (5) decir siempre de donde sale, y dejar de ensenarlo cuando
la ventana pasa aunque no haya captura nueva; (6) prueba: una promocion con
`validFrom` en el pasado no puede acabar en `promo_futura_*`.

## N17. `solo_online`: descuentos que no existen si vas a la tienda

No anade una funcionalidad: **corrige un total que hoy esta mal**.

    Carrefour  badge.description con "Exclusivo online"      76 (46 + 30)
    DIA        headband_promotion = exclusive_online        106
    DIA        promotions[].exclusive_online                 ~100

Hoy esos descuentos entran en el total de la cesta como si fueran reales. Un
campo `solo_online` y la regla de siempre: se ensena, no se resta, y la
comparacion entre cadenas se puede hacer con y sin el.

Es el hermano del caso de la tarjeta de fidelizacion, y **Alcampo lo dice ya con
`promotions[].type = LOYALTY` en 534 productos** (hoy se deduce del texto).

## N18. `badge.description` de Carrefour — 2.024 productos

La regla de la oferta escrita en espanol, en el **17,4 %** del catalogo:

    2.711  Compra 2 unidades y te descontamos el 50 % en la 2ª ud
      800  Compra 2 unidades, Ahorra la segunda
      307  Compra 12 unidades de leche ... PASCUAL brik 1 l
      105  Compra 3 unidades y paga solo 2
       52  Compra 4 unidades y paga solo 3
       46  Te descontamos 5 € por la compra de 18 €

Los dos ultimos son la trampa: **no son reglas de producto, son reglas de cesta**
(por marca y por importe). Si se aplican producto a producto, el total sale mal.
Mientras no haya modelo de cesta, se guardan y se ensenan como texto y **no se
restan**. Tambien sin leer: `strikethrough_price`, el precio anterior real, en 190
productos.

## N19. `main_feature` de Mercadona — municion para F2

**1.209 productos (26,4 %)** con el descriptor de variante: *"Yogur griego dulce
Hacendado"* -> *"con dulce de leche, galleta y platano"*. Entra por **N7, los
grupos demasiado anchos**, no por la ficha: dos productos de la misma cadena con
`variante` distinta no son el mismo producto. Entre cadenas no vale como negativa
(las demas no publican el campo).

## N20. Cruces de calidad: los que no dan datos, dan desacuerdos

    DIA  prices.discount_percentage != 0     161 productos
    DIA  prices.is_club_price = True         130 productos

No hay que copiarlos. Hay que **compararlos con lo nuestro**: si nuestro descuento
calculado y el suyo no coinciden, uno de los dos lee mal el formato; si un
producto dice `is_club_price` y nuestro `promo_club` esta vacio, se nos ha
escapado. Un desacuerdo entre dos fuentes es lo unico que encuentra errores que
ninguna de las dos declara.

Los `stamp_code` de DIA (1, 2, 3 y 4, en 1.096 productos) **no se tocan** hasta
cruzarlos con el texto de la promocion de esos mismos productos y comprobar que
cada codigo cae siempre en el mismo tipo de oferta. Un codigo mal interpretado es
peor que un codigo sin leer.

## N21. La extension de navegador con la curva de precios

Idea tomada de `supermarket-tracker`: ensenar el historico **dentro de la web del
supermercado**, mientras compras. Es la unica forma de que trece dias de serie
sirvan en el momento de decidir, y para nosotros es **un cliente mas de la API que
ya existe**, no una pieza nueva de datos.

**Y el lector de direcciones de Alcampo estaba mal, arreglado el 23 de septiembre de
2026.** Lo que se corta en el mostrador lleva **el corte pegado al identificador**
(`products/39529-TROZO`, `products/94846-LONCHA-NORMAL-2-A-3-MM`) y ese sufijo **es parte
del `id_fuente`**, no un adorno de la direccion: la ficha de Cesta se guarda como
`alcampo:39529-TROZO`. El patron viejo pedia digitos hasta el final del segmento, asi
que en esas fichas la extension se quedaba muda. Son **335 de 23.842 productos** (el
1,4 %), y son justo el mostrador de quesos y embutidos, que es donde una persona se para
a comparar.

Ahora se admite un sufijo en **MAYUSCULAS** dentro de lo capturado, y sigue sin casar la
direccion vieja con UUID (`products/72bccb32-...`), que devolvia un identificador
inventado: tras los digitos se exige un guion y una mayuscula. Comprobado sobre las
23.842 direcciones del bronze de ese dia -- las reconoce todas y el identificador que
saca es exactamente el `id_fuente` en las 23.842. La prueba esta en
`tests/test_extension.py`, con los dos casos del mostrador.

## N22. Pantalla "bajadas de esta semana" y "verificador de ofertas"

Las dos salen de la competencia (Precios del Super y PrecioReal) y las dos las
podemos hacer mejor porque el calculo ya esta hecho:

- **bajadas**: ellos comparan con la captura anterior; nosotros tenemos trece dias
  de serie y el `FACTOR_INCREIBLE` para no confundir una bajada con un formato mal
  leido.
- **verificador**: la regla `dudoso` ya esta calculada y hoy es solo un campo.
  Merece pantalla propia: *"esta oferta no lo es"*.

## Reglas nuevas de la tarde del 18 de septiembre

- Un control que aprueba cuando no tiene con que comparar es peor que no tenerlo:
  se confia en el.
- Una comprobacion se escribe donde todavia tiene arreglo barato.
- Arreglar el dato de ayer puede cegar el control de manana. Antes de restaurar
  algo, mirar contra que se compara.
- **Bronze no se borra nunca. Si no esta en su sitio, es que lo apartaron.**
- **Las cadenas se suman; el emparejamiento se gana.** Un comparador con siete
  cadenas ensena 177 referencias comparables; nosotros con cinco ensenamos 6.448.
- **Antes de medir un campo "nuevo", mirar si ya se lee un hermano suyo.**


---

# Lo del 19 de septiembre por la tarde: la auditoria de FICHAS

Hasta hoy se habia auditado el crudo de los **listados** y nunca el de las
**fichas de producto**, que es donde esta lo bueno. Detalle en `docs/FICHAS.md`.

## HECHO hoy

- **`conservacion` de DIA: 0 % -> 34 %.** `storage_instructions` estaba en el
  44 % de las fichas y `sellos.conservacion_de_prosa` ya sabia leerlo desde que
  se escribio para Mercadona. Cierra **N2**.
- **`origen` de DIA: 0 % -> 69 %**, de `manufacturer_contact_country` (29 %) y
  `manufacturer_name` (41 %). La direccion postal no se usa: un domicilio social
  no es un origen.
- **`solo_online`**, la marca que faltaba (era N17): 397 promociones de Alcampo
  lo dicen en su texto y entraban en el total de la cesta como si fueran a bajar
  el ticket de la tienda. Ahora `Mecanica.util` las excluye igual que a las de
  tarjeta, y la busqueda por ofertas tampoco las cuenta.
- **Carrefour: las categorias difuntas ya no se repaginan.** Una categoria que ya
  no existe no da 404: sirve **el catalogo de su padre**, con su paginacion
  entera. Medido sobre el crudo del 19: **531 de 2.634 paginas, el 20 % de todo
  lo que se pidio ese dia**. El caso gordo, `cat20001`: 462 paginas servidas para
  1.008 productos. Se detecta por `navigation_id` y se corta.
- **Carrefour: un cuerpo cortado ya no envenena el rescate.** Una pagina llego con
  220.978 de sus ~468.000 caracteres, el objeto de JavaScript no cerraba, y el
  cuerpo malo **se habia guardado en el crudo del dia**: las tres vueltas de
  rescate lo releyeron de disco y fallaron igual, sin tocar la red. Ahora, si el
  parseo no traga, se vuelve a pedir saltandose la cache.

## N23. El arbol de categorias de DIA, en palabras (sustituye a N3)

`category_description`, `family_description` y `section_description` vienen en el
**100 %** de las fichas: "SECO", "INFUSIONES", "ALM DULCE Y LECHE". Es el arbol
que faltaba, y no hay que pedir nada nuevo: ya esta en el maestro.

## N24. Los "free" de DIA, con cuidado

`gluten_free`, `lactose_free`, `nuts_free`, `salt_free`, `caffeine_free`, `bio`,
entre el 15 % y el 72 % de las fichas. **Trampa**: el valor es "SI", "NO" o
**"No Aplica"**, y "No Aplica" es el 72 % de los `gluten_free`. Solo un "SI"
explicito cuenta. Es la asimetria de siempre: en un filtro de inclusion como "sin
gluten", pasarse marcando es peligroso.

## N25. `stamp_description` desbloquea los `stamp_code`

En la auditoria de listados del 18 quedaron 1.096 productos de DIA con
`stamp_code` 1, 2, 3 o 4 y la nota "no se tocan hasta saber que significan". La
ficha trae `stamp_description` ("Air Fryer"). Cruzando los dos se sabe.

## N26. Codigos de barras secundarios: guardados, sin usar

`secondary_eans` en el 22 % de las fichas de DIA (187 en 460). Se capturan y
**no se usan para emparejar**, a proposito: entre ellos esta el codigo del
**pack**, y emparejar por ahi haria que un pack de seis y una unidad suelta
fueran el mismo producto. Para usarlos hay que saber cual es cual, y la ficha no
lo dice.

## N27. Lo que queda en la ficha de DIA

`drained_weight` (100 %), `item_vat_code` (100 %), `net_contents` (48 %),
`manufacturer_warnings` (22 %), `serving_size` (17 %), `alcohol_content` (7 %),
`nutritional_claim` (5 %), `health_claim` (3 %), `nutri_score` propio (2 %),
`hazard_info` con codigos CLP estructurados (2 %), y micronutrientes (1-2 %).

## N28. Mercadona: `extra_info`

100 % de las 11 fichas del crudo de hoy: `['Nota olfativa floral']`. Muestra
corta -- el maestro es incremental y el crudo viejo se limpia --, pero es un
descriptor mas, hermano de `main_feature` (N19).
