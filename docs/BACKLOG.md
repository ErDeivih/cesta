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
   9. ~~**"Darme de baja"**~~ — **hecho el 24 de septiembre de 2026**: el boton esta en
      `Ajustes.tsx`, con la confirmacion por usuario de la interfaz vieja (escribir tu propio
      usuario, no un «¿seguro?», que se pulsa sin leer) y `borrarme()` en `src/api/cesta.ts`
      sobre `DELETE /api/yo`. Comprobado en un navegador: el boton esta deshabilitado sin
      escribir y con un texto que no es el usuario, y al pulsarlo la cuenta desaparece de
      verdad (entrar despues contesta 401) y la aplicacion vuelve a su estado sin sesion.

      Y al comprobarlo salieron **dos fallos de verdad**, los dos arreglados:

      - **La linea que alguien anadio a una lista ajena desaparecia de la pantalla** cuando
        esa persona se daba de baja. La fila seguia en la base (con `anadido_por` a NULL, que
        es lo que promete `sql/003`: *"las lineas en listas ajenas pierden el autor pero no
        desaparecen"*), pero `almacen.lineas_de` hacia `JOIN usuario` en el autor y no la
        devolvia: medido, 4 lineas en la lista -> se da de baja quien anadio una -> la
        pantalla ensena **3**. Arreglado con `LEFT JOIN`, como ya estaba el de `tachado_por`.
      - **La pantalla de ajustes sin sesion era un callejon sin salida**: decia «Entra para
        cambiar tus ajustes» y **no habia ni un enlace ni un boton** (lo tenia apuntado
        `docs/DISENO.md` §3.4). Ahora dice por donde se entra, como la de favoritos.

      Y un tercer fallo, este de la prueba: elegia los grupos por numero de cadenas **sin
      desempate**, y DuckDB devolvia cualquiera de los empatados. El 24 sep se puso roja ella
      sola -- «la alerta no se apunto» -- porque habia caido en un grupo cuyo precio no estaba
      en su minimo de 90 dias. Ahora ordena por lo cerca que estan de su minimo, con
      `grupo_id` de desempate, y la prueba se ha corrido dos veces seguidas en verde.
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
      ~~sin contador de lo que falta por coger en la barra de abajo~~ -- **hecho el 24 de
      septiembre de 2026**: la chapa con el numero va en el icono de la cesta
      (`usePorCoger` en `api/consultas.ts`, `Nav.tsx`), sale de las lineas sin tachar de
      la lista de casa, comparte cache con la cesta y desaparece con cero. Medido en un
      navegador con una cuenta nueva: 0 -> no hay chapa, 1 -> dice 1, todo tachado -> fuera
      (`app.js:284-295`), el estado vacio del buscador no distingue "nada
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
    codigos con el pack contradicho               85   (por eso el pack NO es guarda:
                                                       `1` es el silencio, no una
                                                       declaracion. Ver mas abajo.)

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

Esta en `Claude outputs/ENCARGO-UX-23SEP.md` (328 lineas, 11 secciones). **El indice de
cierre, seccion por seccion y con la barra condicion a condicion, esta en
`docs/CIERRE-ENCARGO-UX.md`**: es lo que hay que leer para decidir si el encargo esta
cumplido, y aqui queda el detalle del dia a dia. Lo que
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
    punto 2  la lista                             HECHO: dos secciones, pasillo pegajoso,
                                                  deshacer, y los cambios SIN COBERTURA
                                                  se guardan en el movil y se suben solos
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
    punto 6  los avisos que no avisan             HECHO de punta a punta: el vigilante
                                                  los mira cuando cambia gold, y hay
                                                  campana, pantalla y punto en el icono

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

### El escaner, con un codigo de verdad: la pregunta 2 como se pregunta en la tienda

La pregunta 2 del encargo -- *"esto que tengo en la mano, ¿esta caro?"* -- empieza, de pie en
el pasillo, **escaneando el codigo de barras**. Hasta hoy la pantalla del escaner no la habia
abierto un navegador: se probaba el endpoint (`/api/ean`), no la pantalla. Y son dos cosas
distintas: el endpoint puede contestar perfecto y la pantalla no ensenarlo.

Se anadio a la puerta, con **el camino manual** -- que es el que funciona cuando no hay camara
o no hay permiso -- y con un codigo **de verdad**, sacado de gold (uno que este en tres
cadenas o mas, porque un codigo que solo exista en una no puede contestar "¿esta caro?"):

    ok  el escaner deja escribir el codigo a mano (sin camara tambien vale)
    ok  el codigo 3700123300014 contesta con el producto y su precio
    ok  y no dice que no lo conoce, porque lo conoce
    ok  un codigo que no esta dice que no lo sabe, en vez de callarse
    ok  y la pantalla no se rompe

    1,0 s   escanear un codigo

El ultimo caso es el del «no lo sé», que es la regla de siempre: un codigo que no esta en el
catalogo tiene que decirlo con palabras, no quedarse en blanco ni inventarse nada.

### El enlace de invitacion, abierto por otra persona: la otra pantalla que no habia visto un navegador

`docs/AMIGOS.md` cuenta desde el 21 de septiembre que la lista es de quien la creo **y de
quien entre**, y que entrar se hace con un enlace. Estaba probado contra la API
(`tests/test_invitaciones.py`) y **nunca contra la pantalla**: el mismo hueco que tenia el
escaner, y por el mismo motivo -- el endpoint puede contestar perfecto y la pantalla no
ensenarlo, ni llevar a donde tiene que llevar.

La puerta mecanica tiene ahora una seccion que hace **el viaje entero y con dos personas**:
la cuenta de siempre crea el enlace desde su cesta, y una **segunda sesion del navegador**
-- otro contexto, sin cookies, como el movil de quien lo recibe -- lo abre sin tener cuenta,
entra desde ahi y acaba dentro de la lista:

    ok  quien creo la lista manda el enlace desde la pantalla (no por API)
    ok  el enlace sale escrito entero, con su codigo (e/743lEovwQc5Z)
    ok  y dice cuando caduca y para cuantas personas vale
    ok  quien abre el enlace sin cuenta ve que le han invitado, no un error
    ok  y le dicen que el codigo no se pierde al entrar
    ok  el alta de prueba-invitada pide nombre, usuario y clave (3)
    ok  al aplicarse lleva a la cesta, y no deja el enlace a mano
    ok  y dice a que lista ha entrado, con el nombre que le puso quien la creo
    ok  la invitada ve las lineas que ya estaban puestas
    ok  y no le sale el boton de invitar, porque la lista no es suya
    ok  quien invito ve a la otra persona en «Quién está dentro»
    ok  quien creo la lista puede anular los enlaces
    ok  y la pantalla dice cuantos ha anulado (o que no habia ninguno)

**No encontro ningun defecto, y eso tambien es un dato**: hay flujos que estan bien y lo que
faltaba era la prueba. Lo que si hubo que arreglar fue **la prueba misma**, dos veces, y las
dos son la misma leccion de siempre -- una puerta que se pone roja sola no sirve de nada:

    el presupuesto de enlaces   la API admite **tres enlaces vivos por lista** y contesta 409
                                al cuarto. La cuarta pasada de la prueba se quedaba sin
                                enlace y fallaba ella, no la aplicacion. Ahora **anula los
                                que haya antes de crear uno** -- y con eso se comprueba
                                ademas el camino de anular, que no habia visto nadie.
    la segunda pasada          la cuenta es fija (las altas estan limitadas por hora), asi
                                que a partir de la segunda vuelta la API contesta «ya estabas
                                en la lista» en vez de «ya estas». La prueba acepta **los dos
                                estados**, como ya hacia con «Te aviso» / «Avisarme si baja».

Corrida **tres veces seguidas** contra la misma base: `TODO BIEN` las tres.

### Los documentos estaban doble codificados (y ahora hay una regla que lo ve)

En la misma pasada salio otra cosa, esta vez en el repositorio y no en la pantalla:
`docs/CIERRE-ENCARGO-UX.md` tenia las comillas angulares y los signos de interrogacion
convertidos en **dos caracteres cada uno** -- `\u00c2\u00ab\u00c2\u00bf` donde tenia que haber
`«¿` --, y `docs/OPERACION.md` tenia `s\u00c3\u00b3lo` donde tenia que decir `sólo`. (Los
ejemplos van con escapes **porque este documento tambien tiene que pasar la regla que
cuenta**: escrito con los caracteres de verdad, este mismo renglon la incumpliria.) Los dos
venian de renglones escritos con PowerShell en pasadas anteriores: el texto se leyo como
Latin-1 y se volvio a escribir como UTF-8, de modo que cada byte acabo siendo dos caracteres.
Y los dos empezaban por una marca invisible (U+FEFF) que no llevaba ningun otro fichero del
repositorio.

Nada de eso rompe la aplicacion -- por eso vivio ahi sin que nadie lo viera --, pero rompe
**lo que se lee**, que en este proyecto es la mitad del trabajo: quien abre el documento ve
basura donde deberia haber una coma y deja de fiarse de lo que pone dentro. Arreglado en
**28 renglones** entre los dos ficheros (y la marca de `plataforma/web/estilo.css`, la unica
del repositorio), sin tocar nada mas: ni un salto de linea, ni una palabra.

Y con una **regla nueva** para que no vuelva, `tests/test_documentos.py`: ningun fichero de
texto del repositorio empieza por U+FEFF, y ninguno lleva la firma del doble codificado. Con su
prueba de que el detector mira (una linea doble codificada metida a mano tiene que salir), que
es la leccion que ya dejo la trampa del contraste. Las pruebas de la regla estan escritas con
escapes a proposito: el fichero tiene que pasar su propia regla.

**Y la regla tenia un punto ciego, que se descubrio una pasada despues.** La primera version
solo miraba la familia de dos bytes (`Â`/`Ã` pegados a la banda 0x80-0xBF), asi que **aprobo
un fichero que seguia mintiendo**: `docs/OPERACION.md` tenia siete renglones con la raya larga
y las comillas tipograficas partidas en tres caracteres, y la prueba decia que todo estaba
bien. No salio del control: salio de leer el fichero al escribir la receta de otra cosa.

La causa de esos siete es que el codec no era Latin-1 sino **Windows-1252**, que es lo que usa
PowerShell en un Windows en castellano: cp1252 tiene caracteres imprimibles (la raya, las
comillas, el euro) donde Latin-1 tiene controles, asi que los tres bytes de una raya larga
acaban en tres caracteres que se salen de Latin-1 y el arreglo renglon a renglon los dejaba
pasar. Arreglados con el codec correcto, y el detector mira ya las dos familias. Un control
que aprueba lo que no mira es peor que no tenerlo, porque se confia en el -- y este lo hizo
durante una pasada entera.

Lo que **no** se ha normalizado, dicho a proposito: los saltos de linea. `core/matching.py`,
`docs/CIFRAS.md` y `docs/DIAGNOSTICO-MATCHING.md` estan en CRLF desde antes de esto, y
cambiarlos seria un diff enorme que no arregla nada de lo que se ve en la pantalla.

### La ficha del grupo servia campos de otra columna (y 482 grupos daban 500)

Lo encontro la puerta del navegador, y no buscandolo: anadiendo la comprobacion del reparto
entre dos tiendas salio un `FALLO` en la seccion del grupo de una sola cadena -- *"y dice por
que no la lleva"* --, y el motivo era que **`/api/grupo/0` contestaba 500**.

`catalogo.grupo()` leia cada fila **por posicion** (`f[35]`, `f[36]`...). El dia que alguien
anadio una columna a la lista de `nuevas`, todo lo que iba detras se quedo **uno a la
izquierda**, sin que nada avisara. Medido el 24 de septiembre de 2026 sobre el gold del 23:

    482 grupos daban 500         el producto mas barato tiene `advertencias` (texto) y el
                                 codigo hacia `(f[40] or 0) > 1`: comparar texto con un numero
                                 revienta. Es el 1,1 % de los 44.434 grupos.
    3.844 productos con alcohol  salian marcados como **retirados** (`es_recall` leia
                                 `es_alcohol`): la mentira mas cara que puede decir esta
                                 pantalla es decir que un producto esta retirado
    341 promociones solo online  salian como alcohol, y con eso el filtro de "sin alcohol"
                                 escondia productos que no lo son
    544 productos                ensenaban su `peso_variacion_pct` en el sitio del `distintivo`
    unidades_pack                no llegaba nunca a la pantalla (leia `advertencias`)

Arreglado leyendo **por nombre**: los nombres los da la propia consulta
(`cursor.description`), asi que anadir una columna no puede mover ninguna otra. Comprobado por
HTTP: `grupo 0` pasa de 500 a **200** con sus advertencias en su sitio, y un grupo con alcohol
da `es_alcohol: true` y **`es_recall: false`** (antes: retirado).

Y con la prueba que lo habria cazado: `tests/test_campos_del_grupo.py` construye un grupo de
mentira con **un valor distinto en cada columna** y comprueba campo a campo. Un desajuste se ve
ahi como lo que es -- un campo con el valor de otro -- en vez de como un 500 tres capas mas
arriba.

### El numero de la barra: cuantas quedan por coger, desde cualquier pantalla

La pregunta 3 del encargo -- *"¿voy tachando bien?"* -- se contesta **sin abrir la lista**: la
chapa con el numero va en el icono de la cesta. Lo tenia la interfaz vieja en el mismo sitio
(`app.js:507-509`, el `pin-lista`), asi que entra en la cuenta de paridad.

Sale de las lineas **sin tachar de la lista de casa**, por las **mismas claves de cache** que la
cesta (`['yo']`, `['listas']`, `['lista', id]`): abrirla no pide nada dos veces. Sin sesion no
pide nada y devuelve 0, y si la peticion falla (sin cobertura) tambien: **un cero callado es
mejor que un aviso rojo en la barra**, porque estar sin red en el pasillo no es un fallo de la
aplicacion. Con cero no se pinta.

Medido en un navegador con una cuenta recien creada: sin nada no hay chapa, con una linea dice
1, y con todo tachado desaparece. Y en la puerta, en cada pasada, comparado con lo que hay en la
lista (destacha una a proposito, para que la comprobacion no sea un "0 contra 0" que no prueba
nada).

Y la septima leccion de instrumento de la sesion: la primera version de esa comprobacion leia
el `innerText` **del enlace** y saco **22** donde ponia 2 -- `innerText` pega la chapa con la
etiqueta, «Cesta22 por coger» --. El numero estaba bien y el que mentia era el que miraba.
Ahora lee la chapa (el `span` con `aria-hidden` y solo digitos) y el texto para quien no ve el
color sigue en el `sr-only`.

### El reparto entre dos tiendas ya se pintaba (y no lo sabia nadie)

En la lista de paridad figuraba como que falta el reparto, y estaba hecho:
`Cesta.tsx:1319` pinta `Repartido` cuando la API manda `repartido`, y el componente ensena el
total, el ahorro y **cuantas cosas van a cada cadena** -- el "N en CADENA" de la interfaz
vieja (`app.js:718`), que era lo que la hacia planificable.

Lo que faltaba era la prueba, y ahora esta: la puerta intercepta `donde` con una respuesta
puesta a mano -- porque hace falta una lista cuyos productos mas baratos esten en cadenas
distintas, y eso no se puede pedir "que salga" en una pasada -- y comprueba que se pinta el
titulo, el total, el ahorro, el desglose por cadena y la etiqueta **«no compensa»** cuando el
ahorro no llega a 1,50 EUR. Medido antes: seis productos de la compra basica salen todos mas
baratos en Alcampo, la API contesta `repartido: null` y **no hay reparto que ensenar**, que es
lo correcto y no un fallo.

Con esto, servir `dist` quitaria **una sola cosa**: las tres pantallas del panel (indice,
posicion, ofertas dudosas). El interruptor de repartir entre dos tiendas se puede quitar
teniendo el aviso de "no compensa": el que no quiere dos viajes ya ve cuando no los quiere.

### Puesta en produccion: la imagen, el puerto de la base y el contexto de construccion

Las tres cosas que quedaban de la puesta en produccion, hechas y medidas el 24 de septiembre
de 2026 **sobre el mismo gold del 23** (los datos no han cambiado; cambia el reloj).

**1. La imagen de la API, reconstruida.** Lo que corre en el 8080 llevaba dos dias sin las
cosas del repositorio. Medido por sus rutas, antes y despues:

    /api/habituales                    404 Not Found   ->  401 «Hay que entrar primero.»
    /api/buscar?q=lece entera          resultados: []  ->  encuentra «Leche entera» de
                                                           MILSANI en Aldi a 0,96 EUR/l
                                                           (con su `corregido`)
    /api/alertas, /api/salud           401 / 200       ->  igual

Y las migraciones **006** y **007** se aplicaron solas al arrancar (`almacen.migra()`), que es
lo que se pidio comprobar antes de recrear el contenedor: `alerta` tiene ya `salto_en` y
`salto_texto` con su indice parcial, y `lista_linea` ya **no** tiene `tachado_coherente`. Antes
de tocar nada se comprobo lo unico que podia hacer fallar la 007 -- una fila con `tachado_por`
sin `tachado_en`: **0**. Y la interfaz vieja, que era la que se servia entonces, seguia
funcionando con la API nueva: entrar, buscar y ver los resultados, comprobado en un navegador
(con una cuenta de prueba, borrada despues; la base quedo con su usuario y su linea de
siempre). *(Desde la tarde de ese mismo dia se sirve la nueva: ver «La interfaz nueva,
servida», mas abajo.)*

**2. El puerto de la base, publicado en `127.0.0.1` y solo ahi.** Era la condicion para que el
paso de los avisos de la cadena pudiera preguntar algo. La clave **no se copia a ningun sitio**:
`projects/cesta/avisos.py` la lee de `plataforma/.env` -- que es de donde la saca Compose -- si
no hay un `CESTA_POSTGRES` en el entorno. Asi la cadena de las 06:00 funciona **sin tocar
`ejecutar.bat`** ni el Programador de tareas, y no hay una segunda copia de la clave que se
quede vieja:

    antes   [avisos] avisos: no lo se -- la base de datos no se alcanza desde aqui: ...   6,5 s
    ahora   [avisos] avisos: 0 saltaron hoy | 0 en esta pasada de 0 miradas (11:03)      1,1 s

**3. El contexto de construccion, que era el repositorio entero.** El `Dockerfile` de la API
se construye con contexto de la **raiz** (`context: ..`), asi que Docker busca el
`.dockerignore` en la raiz… y **no habia**: habia uno en `plataforma/`, que con ese contexto
no se usa para nada. El daemon recibia **11 GB de `data/`**, 541 MB de `.venv` y 96 MB de
`node_modules`, y `COPY plataforma/` metia el arbol del front dentro de la imagen de la API.
Arreglado con un `.dockerignore` en la raiz que excluye lo que la API no necesita (`core/` y
`plataforma/` es todo lo que copia el `Dockerfile`, y el front lo sirve Caddy desde el
volumen). La reconstruccion tarda **segundos** en vez de minutos.

Lo que quedaba de la puesta en produccion era una sola cosa, y era la que cambia lo que se
ve: **cambiar el montaje de la interfaz** (`docker-compose.yml`: `./web/dist:/srv:ro` en vez
de `./web:/srv:ro`). Antes de hacerlo habia que medir la paridad que faltaba, porque el dia
que se cambiara, lo que la interfaz vieja hace y la nueva no **desaparece** de la mano de
quien la usa. **Se hizo el 24 de septiembre de 2026 por la tarde, con la paridad cerrada y
medida: ver «La interfaz nueva, servida», mas abajo.**

### El material de aprendizaje, y la web de documentación

**Por qué.** El proyecto llevaba **1,1 MB de documentos** (60 ficheros: el registro del día a
día, los informes, la operación, las decisiones) y ninguna forma de leerlos como lo que son:
un material de estudio. Faltaba lo que convierte un proyecto en algo que se puede enseñar (y
en una destreza de portfolio): **la parte teórica escrita y con números medidos**, y un sitio
por donde recorrerla.

**Lo que se hizo.** Dos cosas separadas a propósito:

    docs/aprende/*.md            el CURSO: capitulos en orden, con teoria y con los numeros
                                 de este proyecto como caso practico
    docs/*.md                    la REFERENCIA: todo lo demas, tal cual se escribio
    plataforma/aprende.py        el conversor: markdown -> un sitio que se puede leer

El conversor no inventa nada: lee los documentos, reescribe los enlaces entre ellos (los
documentos se citan por nombre: `docs/BACKLOG.md`) para que funcionen como páginas planas, pone
anclas a los encabezados, y genera un índice con buscador **embebido** (funciona desde
`file://`, sin servidor y sin pedir nada por red). Dos paquetes puros de Python
(`markdown-it-py`, `linkify-it-py`) en un extra nuevo `docs`: el scraper y la API no los
necesitan, y si faltan el comando dice la instrucción exacta.

**Lo que ya está escrito** (21 capítulos en 8 secciones y 36.187 palabras, y el temario completo
en el índice):

    00  como usar este material          el mapa, las reglas de la casa, los comandos
    01  el problema y los datos          que publica cada cadena, cuanto ocupa cada capa, y
                                         **que NO se puede concluir** con estos datos
    02  ingenieria de datos              capas, Parquet, DuckDB/Polars, idempotencia, la cadena
                                         diaria, calidad, observabilidad, coste, privacidad
    03  unidades y comparabilidad        por que un catalogo es una tabla de envases; el pack
                                         medido y **no** usado como cuchillo; el `en_disputa`
    04  emparejar productos              entity resolution: bloqueo, similitud, hungaro, ejes,
                                         y las trampas con el caso que las enseño
    05  medir el emparejador             el banco de pares, el **techo del bloqueo** (75,7 %),
                                         las invariantes, la fuga de informacion y la auditoria
    06  estadistica del catalogo         la media es 2,31x la mediana; el 79 % de los grupos no
                                         permite comparar; el p90 de la dispersion (112 %); los
                                         recortes contados (0,21 %) y los movimientos falsos
                                         (1.943 de 18.185)
    07  indices de precios               Jevons encadenado y por que (Carli tiene sesgo al
                                         alza); el **sesgo de encadenamiento medido** con el
                                         SQL de la app: 0,38 pp como mucho, y el primer
                                         intento de medirlo que daba +8 pp porque comparaba
                                         dos cosas que no eran la misma
    08  promociones y anomalias          el 80 % de las ofertas anunciadas no baja, pero **la
                                         mayoria no se puede juzgar** (3.658 dependen de
                                         cuantas compres, 288 no anuncian precio): se juzgan
                                         1.538. La ventana legal de 30 dias no cabe en 19
                                         dias de historico, y la regla propia esta dormida
                                         (0 de 872.650 filas)
    10  cuando NO usar machine learning  los tres intentos medidos y descartados: el canal de
                                         vectores (+8 puntos de recall con 861 conflictos),
                                         el medoide (0,511 de cohesion del banco contra 0,719
                                         del grupo malo: no separa) y los modelos de decision
                                         (73,1 % frente a 97 %, y 54 % de declaraciones sin
                                         prueba; dejo 27 bugs propios)
    12  medir sin enganarse              los diecisiete instrumentos que mintieron en este
                                         proyecto, por tipo de mentira: el andamio, el objeto
                                         equivocado, leer antes del estado final, el filtro
                                         que no filtra, la configuracion que nadie mira, la
                                         prueba que pasa con produccion rota y comparar dos
                                         cosas que no son la misma. Con la senal que delata
                                         cada uno y las seis preguntas que auditan un
                                         instrumento
    11  servir los datos                 leer (DuckDB/Parquet, solo lectura) contra escribir
                                         (PostgreSQL, transaccional); 38 endpoints, 23
                                         publicos; la API que dice lo que ha hecho
                                         (`solo_mios: false`); migraciones idempotentes y las
                                         dos que rompieron algo; un solo origen y su CSP; y el
                                         andamio que engana: un endpoint vacio tarda 450 ms
                                         con TestClient frente a 9-16 ms de verdad

**Y los cinco que cierran el material** (escritos después, y son los que más se van a leer):

    13  fundamentos del dato             que es un dato: valor, unidad, momento y procedencia; el
                                         grano y como se comprueba (0 duplicados sobre la clave);
                                         que una clave no es unica (25.413 filas con EAN y 1.627
                                         codigos repetidos); «no lo se» no es cero (98,8 % sin
                                         certificados, 93,3 % sin tabla nutricional); el dinero en
                                         centimos enteros (sumar en coma flotante desvia 1,41
                                         centimos); los dos tiempos del dato; y las seis
                                         dimensiones de la calidad, cada una con su numero
    14  el stack explicado               las piezas, una a una: que resuelven, cuanto cuestan y
                                         **que se rompe si se quitan**. Los extras de dependencias,
                                         el Programador de tareas en vez de Airflow, el generador
                                         propio en vez de MkDocs (el CSP prohibe el script en
                                         linea), la tabla de los «no estan» cada uno con su
                                         condicion de cambio, y la medida incomoda: **el 90,3 %
                                         de gold es un experimento apagado** (190,9 MB de
                                         embedding de 211,3 MB de tablas)
    15  scraping                         cinco webs, cinco trucos: la API publica de Mercadona (el
                                         precio depende de la tienda), el sitemap y el lote de
                                         Aldi, el `window.__INITIAL_STATE__` de Carrefour, la
                                         paginacion con Akamai de DIA y el WAF de Alcampo; por
                                         que el crudo es sagrado; y como se detecta un fallo
                                         **silencioso** (el 18 de septiembre, Alcampo 20.571 en
                                         vez de 23.573 y la rama de Frescos entera ausente:
                                         2.646 -> 91)
    98  glosario                         todo el vocabulario del material, en una linea cada uno,
                                         agrupado por tema y con el capitulo donde se explica
    93  las formulas                     **todas** las formulas del proyecto, una a una: que
                                         significa cada simbolo, de donde sale y el numero que da
                                         hoy. Dice y Jaccard (y por que Dice: 0,600 contra 0,429
                                         con el mismo ejemplo), el IDF (`ln(n/(1+c))+1`, de 1,000
                                         a 8,917 segun la palabra), la mezcla con los trigramas y
                                         su aritmetica (0,55/0,85 = 0,647), el reparto hungaro y
                                         su ganancia (`max(0, s-umbral)`), los cuatro frenos, el
                                         recall y el intervalo de Wilson (64,5 % +- 2,2 puntos),
                                         las cinco formulas de indices de precios, el dinero en
                                         centimos (`0,1+0,2`), la nota de calidad con sus pesos y la
                                         tabla de las constantes con el valor de cada una
    93  ...y la captura                 el apartado 11 del mismo anexo: el intervalo del ritmo y
                                         su ruido (hasta el 40 %, y por que: pedir cada 1,000 s
                                         exactos se delata), la tabla de ritmos por cadena
                                         (mercadona y aldi 2/s, carrefour y dia 1/s, alcampo
                                         0,15/s porque a 1/s cortaba y a una cada 4 s el reto
                                         escalo a pedir un clic humano), la espera creciente de
                                         los reintentos (`2^intento + U(0,1)`) y **por que el 403
                                         no se reintenta ahi** (45 s por categoria bloqueada x 373
                                         = cuatro horas y media en una tarea de 38 minutos), la
                                         huella TLS (JA3/JA4: por que Akamai decide antes de leer
                                         el User-Agent) y el reto de un WAF, con los cuatro
                                         detalles que se aprendieron fallando: validar por
                                         resultado y no por el nombre de la cookie, copiar el
                                         User-Agent, probar contra una pagina protegida y que con
                                         ventana se pasa mas

**El temario esta completo**: 21 capitulos en 8 secciones (00 a 15 y los cuatro anexos), y se leen
seguidos. Aquí van el de análisis y los tres primeros anexos, para que la lista no se corte:

    09  que mas se puede hacer           12 analisis en una tabla, con «si/parcial/no» y el
                                         riesgo de conclusion falsa de cada uno
    90  anexo: la investigacion entera sobre emparejamiento, con sus fuentes
    91  anexo: la investigacion sobre indices de precios con datos de escaner, y una
               auditoria de lo que hace este proyecto, con 12 filas y veredicto
    92  anexo: como se hizo la investigacion, que no se pudo verificar, y un error propio
               que enseña por que hay que citar la linea de codigo

**Y la primera medición que pedía la investigación, hecha** (`projects/cesta/bloqueo.py`, con su
trinquete en `tests/test_bloqueo.py`): cuántos de los pares ciertos por EAN **puede ver** el
bloqueo, que es el techo del recall. Medido hoy sobre el gold:

    pares ciertos (mismo EAN, dos cadenas)      1.795
    el bloqueo los puede ver                    1.359   (75,7 %)   <- el techo
    el bloqueo los pierde                         436
        no se le pudo leer el formato             336
        misma unidad y cantidad distinta           61
        una cadena por unidad y la otra al peso    39

Eso cambia la lectura del 65 % de recall: **es el 86 % de lo que el bloqueo deja ver**, así que
el margen no está en el matcher sino en las 436 parejas que se pierden antes de comparar (datos
y presentaciones, no modelo). La misma medida se hizo el 8 de septiembre (579 de 1.767) y de
ella salió la segunda pasada sin bloque con el listón alto (`UMBRAL_SIN_FORMATO = 0.82`).

**Y el cruce, que es el diagnóstico que faltaba** (`projects/cesta/auditar_pares.py`, offline:
corre el emparejador de verdad y recalcula el parecido de cada par perdido con las mismas
funciones). De los 1.799 pares ciertos:

    encontrado                                                1.161   (64,5 %)
    A  el bloqueo por formato no los junta                      368   (20,5 %)
    B  mismo formato, ninguna palabra en comun                    3   (0,2 %)
    C  se comparan y no se parecen (por debajo del umbral)      177   (9,8 %)
    D  se parecen y aun asi no se enlazan (asignacion 1-a-1)     90   (5,0 %)

Lo que enseña el reparto: **el montón grande no lo arregla ningún modelo** (A: el formato, o dos
nombres comerciales distintos para el mismo producto), el montón donde un matcher mejor tiene
margen son 177 pares (**+9,8 puntos de recall como techo**), y hay 90 pares que el nombre ya
aprueba y que **se pierden después**, en el reparto 1-a-1: o el que ganó el hueco es mejor (hay
duplicados), o es un falso positivo ganando una suma mayor. Ese último montón es el que nadie
audita y el que conviene mirar antes de tocar el umbral.

**De dónde sale lo que dicen.** El 24 de septiembre de 2026 se lanzaron **cuatro
investigaciones** sobre fuentes públicas (2020-2026), cada una con las mismas cuatro reglas: en
castellano, sin relleno, cada afirmación con su fuente, y «no lo sé» cuando el dato no
aparece. Salieron **siete cosas medibles** con lo que ya hay, y la primera es la que más puede
cambiar el proyecto: **medir la *pair completeness* del bloqueo del emparejador**, porque si el
bloqueo ya deja fuera al 35 % de los pares ciertos, el 65 % de recall no es una nota del
matcher sino un techo estructural.

**Lo que descubrió el despliegue, otra vez.** El material se sirve en `/aprende/` del 8080. El
primer montaje fue `./web/aprende:/srv/aprende:ro`, y **el contenedor no arrancó**: `/srv` ya
está montado de solo lectura, y Docker no puede crear un punto de montaje dentro de otro de
solo lectura (`read-only file system`). Se movió a `/aprende` (fuera de `/srv`) con
`handle_path /aprende/*` en el `Caddyfile`, y `tests/test_aprende.py` fija las dos mitades de
la configuración —el montaje y la ruta— para que no vuelvan a separarse. Es la misma clase de
fallo que ya documenta `test_interfaz.py`.

**Y un error propio, que se deja escrito.** El encargo de la investigación sobre índices
describía el recorte de relativos como «0,5×-2×»; el código usa `1.0/3`–`3.0`
(`plataforma/api/analisis.py:55-56`) y ningún documento decía otra cosa. La investigación lo
detectó y lo señaló como discrepancia: un auditor que no comprueba el dato que le dan no está
auditando. Está contado en el anexo 92.

**Como se mantiene, que era la otra mitad del encargo.** El material no es un documento que se
escribe una vez: crece con lo que se mide. Un capítulo nuevo es un fichero en `docs/aprende/` con
su cabecera (`seccion:`, `resumen:` y `en_una_frase:`) y **aparece solo** en su sección, en el
índice lateral, en la portada y en el buscador; el número del nombre del fichero manda en el
orden dentro de la sección. La sección tiene que estar en `SECCIONES`, o el generador avisa por
consola y el capítulo sale en «Otros». Está escrito en `docs/OPERACION.md`, y lo vigilan las 13
pruebas de `tests/test_aprende.py` —incluida la nueva: **todo capítulo declara su
`en_una_frase:`** y se pinta en un recuadro debajo del título—.

**La legibilidad, mejorada a propósito.** El encargo pedía que se leyera como la documentación de
una empresa grande y que lo técnico se entendiera sin ser del oficio. Lo que se cambió, y se
puede ver abriendo el sitio:

0. **El anexo 93, «Las fórmulas, una a una»**: el capítulo que faltaba para que esto sea material
   de estudio y no un diario. Reúne todas las fórmulas que usa el proyecto con el significado de
   cada símbolo, de dónde sale cada una y el número que produce hoy, más una tabla con las trece
   constantes y lo que gobierna cada valor. Los capítulos 03 a 08 apuntan a su apartado, así que
   quien lea «listón de 0,55» tiene a un clic por qué es 0,55 y qué pasaría con otro número.

1. **Recuadro «En una frase» en los 20 capítulos**, justo debajo del título: es la línea que se
   lee desde el móvil, y la única que hay que entender si no se lee nada más. Vive en la cabecera
   del documento, así que no se puede quedar desfasado respecto al capítulo.
2. **Los cuatro recuadros con nombre** —Nota, Trampa, La lección y Regla— en los capítulos donde
   hacen falta, en vez de prosa seguida: cada capítulo dice también **qué se aprende** al final.
3. **Navegación de sitio de documentación**: índice por secciones a la izquierda, índice de la
   página a la derecha, migas de pan, y tarjetas de anterior/siguiente.
4. **La referencia** (`/aprende/referencia.html`): los documentos del proyecto con su primer
   párrafo, que es donde se comprueba de dónde sale cada cosa.
5. **El glosario**, porque la mitad de los atascos al leer material técnico son una palabra.

Y una trampa de mantenimiento que conviene saber: el número del nombre del fichero manda en el
orden dentro de su sección, y ese orden es **alfabético**. Hoy funciona porque todos los capítulos
llevan dos cifras (`09` va antes que `10`); un capítulo `100` se colaría delante de `11`.

### La ingesta del día, comprobada contra las cadenas (24 de septiembre)

**Por qué.** El dueño preguntó si la ingesta de hoy se había hecho bien, con las categorías y los
productos y sus enlaces, comprobándolo **en las propias cadenas**. Los controles que había no
contestaban eso: `runlog` mira el total, `cobertura` mira las ramas que desaparecen,
`auditar_recorrido` mira las categorías que no se piden y `verificar_precios` sale a la calle a
mirar precios. Lo que no se miraba en ningún sitio es lo más tonto y lo que más duele: **de los
productos que la cadena dio hoy, cuántos están en bronze**, y **de las páginas que la cadena dice
que tiene una categoría, cuántas se pidieron**.

**Lo que se escribió.** `projects/cesta/verificar_ingesta.py`, con sus 7 pruebas en
`tests/test_verificar_ingesta.py` y su informe en `docs/VERIFICACION-INGESTA.md`. Compara el crudo
del día contra bronze en cuatro cosas: productos declarados/guardados, categorías, paginación
declarada/pedida y enlaces. Sale 0 si todo cuadra.

**El resultado de hoy: 0 problemas.**

    3.432 respuestas · 57.616 productos declarados · 57.603 en bronze
    13 faltan, y los 13 con explicación (3 de Aldi sin precio en su API, 7 de Carrefour
    en bloques de recomendaciones fuera de la rejilla, 3 en páginas que su web sirve sin rejilla)
    0 sobran  ·  0 filas sin enlace  ·  0 enlaces repetidos  ·  0 fuera de su dominio
    paginación completa: carrefour 2.065/2.065 · dia 520/520

**Y tres hallazgos que valen más que el 0:**

1. **Los enlaces llevan su propio id**, que es la comprobación que faltaba el 21 de septiembre
   (23.776 enlaces de Alcampo en 404 por guardar el `productId` interno en vez del
   `retailerProductId`). Con una excepción medida: **Carrefour publica `R-<referencia>`**, así que
   su `product_id` no aparece en la URL en 1.212 filas de 16.452 (7,4 %) — y ahí el enlace no lo
   construimos nosotros, lo da la cadena, así que exigirlo daría 1.212 falsas alarmas al día.
2. **Las 34 categorías de Alcampo que no se piden no pierden ni un producto**: se preguntó a
   Alcampo una a una con su sesión del WAF, devolvió 477 ids en esas 34 categorías y **los 477
   están en bronze**. Son las mismas 32 que `docs/AUDITAR-RECORRIDO.md` contaba el 17 de
   septiembre, con los mismos nombres («Sin Gluten / Sin Lactosa», «Arroz Ecológico», «Pollo
   Ecológico»); lo que falta no es el producto, es **la palabra que los agrupa** (navegación por
   pasillo, no dato). La de Mercadona es la misma clase en pequeño: la categoría 491 «Pizzas
   refrigeradas» es de tercer nivel dentro de la 138 y sus 24 productos están los 24.
3. **Dos puntos ciegos del instrumento, dichos en voz alta.** `verificar_precios` da 10/10 en DIA,
   9/10 en Carrefour, 9/10 en Mercadona, **3/10 en Alcampo y 0/10 en Aldi**, y esos dos números no
   son un suspenso del dato: Aldi pinta el precio con JavaScript (su HTML de 70 KB no trae ni una
   cifra con euro) y la página de Alcampo devuelve 2.491 bytes, que es el reto del WAF. Lo que sí
   se comprobó: en Aldi el nombre del producto aparece en su página en 8 de 8, y en Alcampo la API
   responde con la sesión del colector (así se comprobaron las 34 categorías). Queda apuntado que
   la comprobación use la sesión del WAF y la API, y que diga «no puedo comprobar esto» en vez de
   «sin precio» cuando el motivo es suyo.

**Un detalle de método que hay que dejar escrito.** La comprobación en vivo de las 34 categorías
guardó 34 respuestas dentro de `raw/2026-09-24`, y eso **ensuciaba la evidencia del día** (el
recorrido no las pidió, y el crudo tiene que seguir diciendo eso): se movieron a
`data/debug/verificaciones/2026-09-24/`. Un control que altera lo que está midiendo deja de ser un
control.

**Y dos sustos de la puerta de producción, que eran del reloj y no del dato.** Ese día, con el
código sin tocar, `plataforma/prueba_produccion.py` fallo dos veces en dos comprobaciones
distintas: una pestaña del panel («el panel de indice contesta») y la frase de la ficha. Las dos
tenían la misma causa, la que documenta el capítulo 12 como *leer antes del estado final*: el
elemento ya existía pero se leía **antes** de que se rellenara. Se arreglan esperando a la
condición que se va a comprobar —no a un tiempo fijo— y con **un reintento con recarga** en el
panel. Ninguna de las dos bajó el listón: si el texto no aparece tampoco a la segunda, sigue
siendo un fallo.

### Los toques hasta cada respuesta: lo medible de la barra (a)

La condicion (a) -- *"las cuatro preguntas contestadas en menos de quince segundos con el
movil y sin saber donde esta el boton"* -- **no la puede cerrar quien escribe el codigo**: se
juzga contra la madre del dueno. Pero tiene una mitad que si es de codigo y hasta ahora no se
media: **cuanto hay que andar**. Un boton a cinco toques no se pulsa en quince segundos ni
sabiendo donde esta.

Asi que la puerta **cuenta los toques andando de verdad** desde la primera pantalla, no
leyendo el mapa de rutas (`prueba_navegador.py`, «cuantos toques hay desde la primera
pantalla hasta cada respuesta»). Medido el 24 de septiembre de 2026:

    1. que me falta y donde lo compro   1 toque    Buscar -> Cesta
    2. esto esta caro                   1 toque    escribir en Buscar -> el resultado
    3. voy tachando bien                0 toques   el numero esta en la barra de abajo
    4. ha bajado algo de lo mio         1 toque    Avisos (si tienes avisos pedidos)
                                        3 toques   Panel -> Bajadas -> «Solo lo mío»

**La primera version de este bloque fallo TRES veces con la aplicacion bien**, y las tres se
cuentan porque son de instrumento, no de pantalla:

  1. daba por hecho un estado de la cesta («Lo que cuesta ahora», «Por coger») y la pasada
     anterior la deja como la deja -- con todo tachado, o vacia con la cuadricula --. Ahora
     la marca de cada caso es **una lista de frases validas**, y lo que se mide son los
     toques.
  2. pulsaba la barra **por su texto**, y «Cesta» tambien es el titulo de la cabecera, cuyo
     enlace lleva a la portada: la medida se quedaba en el buscador y las dos comprobaciones
     de la cesta fallaban con los toques ya bien contados.
  3. pulsaba **la primera barra del DOM**, que es la del escritorio (`NavEscritorio`,
     `hidden lg:block`): en un movil de 390 px no se ve, y Playwright espera a que sea
     visible hasta morir. Hay que pulsar la visible, y las pestañas del panel son
     `role="tab"`, no botones.

Y con esto, `docs/PRUEBA-15-SEGUNDOS.md` queda listo para que lo ejecute una persona: la
direccion (el 8080, por Tailscale), la cuenta nueva por persona (con el limite de altas por
hora dicho), los toques de cada respuesta, y **la tabla para escribir los segundos**.

### Los avisos, mirados en la cadena diaria: el §6 entero (y el instrumento que mintio otra vez)

El §6 del encargo pedia cuatro cosas. Dos ya estaban desde la pasada del vigilante -- *"dejar
el resultado guardado"* (`salto_en` y su frase, que es lo que pinta la pantalla) y *"un punto
en el icono, y al abrirlo la frase entera"* --, y le faltaban las otras dos:

    - *"Evaluarlas en la cadena diaria, despues del pipeline."*
    - *"Que el resumen diario diga cuantas saltaron."*

Ahora estan. El paso es **`projects/cesta/avisos.py`**, va en `run.py` justo despues de
`emparejar` y antes del resumen (que es quien lo cuenta), y **no toca `ejecutar.bat`**: el
`.bat` sigue llamando a `run.py` como siempre, asi que la tarea de las 06:00 no cambia de
forma. Lo que deja escrito es `data/avisos.json`, y la linea del resumen sale de ahi:

    avisos: 1 saltaron hoy | 0 en esta pasada de 0 miradas (19:53)

Los numeros los cuenta `almacen.avisos_del_dia()`, **en la zona de casa** y no en la del
servidor: `salto_en` es un `timestamptz` y el contenedor de PostgreSQL corre en UTC, asi que
a las 06:00 los dos dias coinciden pero a las 00:30 no, y un "hoy" que unas veces es hoy y
otras ayer no se puede leer.

**Lo mas importante del paso es lo que hace cuando no puede, y no es un caso raro.** La base
de datos de casa **no publica su puerto** -- `docker-compose.yml`, *"solo lo alcanza la API,
por la red interna"* --, asi que desde el PC la cadena no la alcanza. Medido hoy en este
equilibrio: `127.0.0.1:5432` no contesta, `127.0.0.1:8080` si (Caddy). Y el paso, en ese caso:

    [avisos] avisos: no lo se -- la base de datos no se alcanza desde aqui (la cadena corre
             en el PC y PostgreSQL no publica su puerto): ConnectionTimeout
    6,5 s (dos pasadas: 6,7 y 6,5) y **codigo de salida 0**

Un cero en esa linea se leeria como "no ha saltado nada" y lo que pasa es que no se ha
mirado. Y **no puede fallar el dia**: detras de este paso van el resumen, la comprobacion de
precios y `verificar_docs`, asi que un paso que se cayera por no llegar a la base
convertiria un dia bueno en un dia fallido por una linea.

Con la base delante si hace su trabajo, y eso se comprueba en `plataforma/prueba_e2e.py`
(receta en `docs/OPERACION.md`): alli hay PostgreSQL de verdad, la alerta salta, y el resumen
dice `1 saltaron hoy | 0 en esta pasada de 0 miradas` con la cola del vigilante vacia.

**Y midiendo esto se descubrio que el instrumento mentia, por segunda vez en el proyecto.**
La primera medicion de "abrir los avisos" dio **469 ms** y puso en marcha un arreglo. Al
comprobarlo pieza a pieza salio esto:

    GET /api/salud por TestClient (no hace nada)         409-419 ms   <- el andamio
    la ruta, en frio (gold recien cambiado)                   47 ms   <- la aplicacion
    la ruta, en caliente (lo que vive una persona)    13 ms (0-16)
    catalogo.conexion(), la primera vez del proceso          406 ms   <- una vez por arranque
    alertas.evalua (frio) -> evalua_con_memoria (caliente)  47 -> 0 ms

Los 469 ms eran **httpx en el mismo proceso**, no la aplicacion: la prueba se estaba midiendo
a si misma. La prueba de punta a punta se quedo con las dos medidas -- la del andamio, escrita
para que nadie la confunda, y la de la ruta --, y el andamio esta ahora en el registro de la
salida para que la siguiente persona que mida no vuelva a creerse ese numero. Es exactamente
la leccion de la trampa del contraste: **una medida tiene que demostrar que mira**.

Lo que si quedo del hallazgo es `alertas.evalua_con_memoria`: el veredicto de una alerta se
recuerda mientras gold no cambie (`47 -> 0 ms`), y como el vigilante pasa por ahi a las 06:00
**en el mismo proceso**, la primera persona que abre la pantalla encuentra la respuesta hecha.
Lo que se guarda **no lleva el id de nadie** (la clave es la pregunta, no quien la hace), y
por eso dos personas con la misma alerta comparten respuesta sin compartir nada suyo.

Lo unico que sigue pagando la primera visita despues de arrancar la API son los **406 ms** de
la conexion a gold. No se ha tocado: es una vez por arranque, no cambia ninguna de las cuatro
preguntas, y calentarlo "por si acaso" seria trabajo en cada arranque para casi nadie. Queda
dicho y medido, que es lo que hace falta para decidirlo con el numero delante.

### La curva con su frase, el ahorro en euros, y **el ahorro que cruzaba unidades**

El §4 del encargo pide cuatro cosas en la ficha, en este orden: *"1. Una frase. 2. Donde
esta mas barato y cuanto se ahorra en euros por unidad de uso. 3. La curva, que ya existe,
**con una frase debajo**. 4. Y solo despues, la tabla"*. La 1 y la 4 estaban; las otras dos,
a medias, y buscarlas destapo un tercer fallo que no estaba en la lista.

**La frase debajo de la curva** (`logica/curva.ts`, nueva). La curva estaba desde el primer
dia y no decia nada: `Chispa.tsx` ya avisa de que *"la chispa es un adorno del dato, no el
dato"*. Ahora dice una de estas cuatro, y cual es cosa del historico:

    Es el precio más bajo de los 17 días que tenemos.
    Es el precio más alto de los 17 días que tenemos: un 12 % por encima del más bajo.
    Lleva 6 días al mismo precio.
    Está un 3 % por encima del más bajo de los 17 días que tenemos.

**Y la regla que mas importa de esa frase es el plazo.** El encargo pone como ejemplo *"esta
mas barato que en los ultimos 90 dias"* porque suena bien; hoy el historico son **18 dias**.
Decir 90 seria una mentira tranquila -- suena mejor y no es verdad --, asi que la frase dice
los dias que hay de verdad, y la puerta del navegador comprueba ya pintado que no prometa
noventa. Es la misma regla del "no lo se" del resto de la aplicacion.

**El ahorro en euros** (apartado 2): un dato nuevo en la cabecera de la ficha,
«MÁS BARATO EN / Dia · 0,98 €/l · te ahorras 0,27 €/l», solo cuando hay algo que ahorrar.

**Y el fallo que salio de ahi, que no estaba en el encargo.** La primera version de ese dato
se pinto en el navegador diciendo **«te ahorras 6.872,01 EUR/kg»** en la ficha de un azafran
de 0,4 g: estaba comparando su precio por kilo con el de un bote medido en unidades. La
misma cuenta, en la pantalla del grupo, decia **«+229.833,1 % frente al mas barato»**.

La regla llevaba escrita en el proyecto desde el primer dia -- `core/comparacion.py`,
`resumen.ahorro()` (*"una sola unidad por grupo, la misma regla que usa la interfaz"*) y
`api/alertas.py` (*"si la unidad cambio, no es una bajada"*) -- y **la interfaz se la saltaba
en tres sitios**: el dato nuevo, la columna «Diferencia» de la tabla, y el `ahorro_pct` que
la propia API calculaba para la ficha del grupo. Los tres arreglados con la misma regla:
**solo se compara con lo que se mide igual**, y quien no tiene con quien compararse no saca
un porcentaje, saca una frase que lo dice (*"sin otra cadena que lo mida igual"*).

Y el arreglo deja las **tres consultas que comparan precios** -- `buscar` (el buscador),
`tarjetas` (el mosaico y los avisos) y `grupo` (la ficha) -- con la misma regla, que es lo
que faltaba: las dos primeras ya elegian una unidad por grupo (`catalogo.py`, el bloque
`unidades`/`manda`) desde que el buscador anunciaba ahorros del 229.833 %; la ficha se
quedo sin arreglar y era la que se ve al abrir un resultado de la busqueda.

Medido sobre el gold de hoy, antes y despues, con los topes del resumen:

    grupos que mezclan unidades                        125 de 39.592
    grupos comparables (mas de una cadena)        8.771  ->  7.918
      diferencias imposibles (> 2.900 %)             54  ->  0
      diferencias llamativas (> 200 %)              370  ->  226
    mediana de la diferencia                      16,5 %  ->  16,0 %

La mediana no se mueve -- el apaño es para la cola absurda -- y **54 numeros imposibles
dejan de salir en pantalla**. Los 853 grupos que se quedan sin comparacion pierden un numero
que no era comparable en vez de ensenarlo mal.

Lo encontro **la puerta del navegador**, no una prueba de codigo: el numero se calculaba en
el JSX, y ningun `grep` lo ve. Por eso se anadio tambien la medida que lo caza sola: la
puerta mira **todos los porcentajes pintados** de la ficha y de la pantalla del grupo y
ninguno puede pasar del tope de *"esto ya no es una oferta"* (`core/comparacion.py`: mas de
29 veces no es una oferta, es una unidad mal leida). Con su trampa, para que la medida
demuestre que mira: con el tope a cero tiene que encontrar algo.

### La cesta vacía deja de ser un cartel: la cuadrícula de un toque

El §2 pone **las tres cosas juntas** como el peor momento de la aplicación: *"un amigo que se
registra ve un buscador vacío, **una cesta vacía** y un panel de índices que no significa
nada"*. El buscador se arregló el 23 de septiembre (`LoQueSeCompra` + `Mosaico`); la cesta se
quedó con un cartel: *"Busca un producto, abre su ficha y pulsa «Añadir a la cesta»"*, o sea
tres pasos para volver al mismo sitio, con la aplicación sin hacer nada por quien acaba de
llegar.

Ahora las dos ramas vacías de `/cesta` —**sin ninguna lista** y **con la lista sin líneas**—
pintan la cuadrícula (`Mosaico`, seis tarjetas) además de la frase:

    No tienes ninguna lista
    Todavía no hay listas guardadas. Busca un producto o toca uno de abajo: se apunta en
    la lista de casa, que se crea sola, y la cantidad se cambia aquí.

    La compra basica                                  <- el titulo dice de donde sale
    Un toque y a la lista. Lo tocado se cambia en la cesta.
    Leche entera   0,96 EUR/l  en Aldi     [Añadir]
    Pan de molde blanco  1,33 EUR/kg  en Aldi   [Añadir]
    ...

Medido en un navegador con una cuenta recién creada, sobre este mismo bronze:

    la pantalla        seis productos reales con su cadena más barata, y el título
                       «La compra básica» (que es lo que son: no se titula «Lo de siempre»)
    un toque           la lista se crea sola y la cesta queda con su línea, su total
                       (0,96 €), sus dos secciones y su pasillo

**Y `vacia` es una excepción escrita, no un descuido.** En el buscador, sin historial, la
cuadrícula de básicos **no** se pinta a propósito (`Mosaico.tsx`, regla 1: 24 recuadros no
explican nada y ahí sale la tarjeta de la primera vez). En la cesta vacía sí, porque la
pregunta que se trae a esa pantalla es *"¿qué me falta?"* y con la lista vacía la respuesta es
"todo": seis recuadros que se apuntan de un toque la contestan; un cartel que manda a buscar,
no. Lo que no puede pasar es enseñarla **sin decir de dónde sale**: con la cuadrícula de
básicos el título pasa a ser el de su origen, porque titulada «Lo de siempre» sería una
mentira dicha en un título.

Los dos estados están en `tests/test_primera_vez.py` (que existan, que estén en **las dos**
ramas, y que la excepción esté escrita), y el guion de los quince segundos ya los apunta en
el apartado de «la primera vez».

### Las cuatro respuestas, en la primera pantalla de un movil

La condicion (a) —*"las cuatro preguntas contestadas en menos de quince segundos con el
movil y sin saber donde esta el boton"*— **no la puede cerrar quien escribe las pantallas**:
se juzga contra la madre del dueño. Pero si se puede descartar de antemano lo que la haria
imposible, y eso es lo que faltaba medir: **una respuesta que obliga a desplazar la pantalla
no se lee en quince segundos ni sabiendo donde esta**.

La puerta del navegador mide ahora la **banda util** de un movil de 390 x 844 —la cabecera
de arriba y la barra de abajo no son pantalla— y comprueba que lo que contesta cada pregunta
cabe entero dentro, con la pantalla arriba del todo:

    la banda util                                       109..787 px de 844
                                                        (109 de cabecera, 57 de barra)
    1 y 3  la primera linea de la lista (input)          557..573   dentro
    2      la frase del grupo al que se llega buscando   520..564   dentro
    4      «lo tuyo que ha bajado», con su tabla         437..557   dentro
    4      la seccion de los avisos                      186..210   dentro

Las cuatro dentro, medido el 23 de septiembre de 2026 sobre este mismo bronze. Y la medida
sale de la cabecera de verdad (`--alto-cabecera`, que la pone `Cabecera.tsx` con un
`ResizeObserver`) y de la barra de abajo, no de dos numeros escritos a mano: el dia que la
cabecera crezca, esto lo dice.

**Lo que esto NO dice, y se dice en el mismo sitio**: no cierra (a). Que una respuesta quepa
no quiere decir que se entienda. Lo que queda de (a) es exactamente eso, y se mide con una
persona y el guion de `docs/PRUEBA-15-SEGUNDOS.md`, que ahora empieza por la lista de lo que
**ya esta descartado** para que nadie vuelva a medirlo.

### La ficha del producto tenía cuatro objetivos de 19 px (y ninguna pantalla se desliza de lado)

La puerta del navegador medía **todas las pantallas menos dos**: la ficha del producto y el
escáner. Al añadirlas salió lo de siempre -- lo que no se mide no se ve --, y en la ficha del
producto, medida en un móvil de 390 x 844 el 23 de septiembre de 2026:

    el enlace al producto de al lado, en la tabla    161 x 19   <- 19 px de alto
    el mismo enlace, con el nombre en dos lineas     158 x 39
    el desplegable «Ingredientes»                    324 x 20

El enlace es **la forma de saltar a la ficha de otro producto del grupo**, que es justo lo
que se hace con el paquete en la mano; y el desplegable abre los ingredientes, que es donde
se mira si algo lleva lo que no se puede comer. Ninguno de los dos se acierta de pie a 19 px,
y llevaban ahí desde el primer día.

Los dos arreglados (`inline-flex min-h-[44px] items-center`), y **las dos pantallas entran en
la pasada de la puerta**: la ficha del producto también en el contraste de los dos temas
(tiene avisos de color propios, como los alérgenos en rojo, que es donde un `dark:` que falte
se ve).

**Y de paso entra una clase de fallo que no se medía: que la página se deslice de lado.** Una
pantalla que se sale obliga a moverla con el pulgar para leer el final de las líneas, y en la
tienda eso es soltar el carro. Las tablas anchas se deslizan **dentro de su caja**
(`TablaScroll`, con su «Desliza la tabla para ver todas las columnas»), que es a propósito; lo
que no puede deslizarse es la página. Medido en las ocho pantallas que visita la puerta
(`scrollWidth` contra `clientWidth`): **390 de 390 en todas**.

    /  /cesta  /grupo/0  /avisos  /panel  /ajustes  /escaner  /producto/dia/147509
    ocho pantallas: ninguna con algo que pulsar por debajo de 44 px, ninguna que se salga

### Cuando la API falla: la cesta era la única sin «Volver a intentarlo» (y dos instrumentos que mentían)

La fila «errores + reintentar» del §8 no la había mirado un navegador: se probaba el endpoint
que devuelve 500, no la pantalla que lo recibe. Al medirla, con la API devolviendo 500 de
verdad en cuatro pantallas, salió un hueco y dos fallos de instrumento.

**El hueco.** La cesta era **la única** pantalla que escribía su error a mano (`Vacio` +
`textoDeError`) en vez de usar `Fallo`, y por eso era la única **sin «Volver a intentarlo»**:

    la cesta, /api/listas -> 500   «No he podido traer tus listas» y **ni un botón**
    los avisos, /api/alertas       «No he podido traer esto» + «Volver a intentarlo»
    lo mío que ha bajado           + «Volver a intentarlo»
    el buscador, /api/buscar       + «Volver a intentarlo»

Había que recargar la página a mano, que en el móvil no es evidente. Ahora usa `Fallo`, que
además es quien decide **el tono**: sin cobertura no es rojo, es un móvil en un pasillo
(`ui.tsx`), y esa decisión tiene que estar en un sitio y no repetida en seis pantallas.

**El primer instrumento que mentía** (el cuarto del proyecto, contando el contraste, el
`TestClient` que medía 469 ms de andamio y el detector de codificación): el patrón
`**/api/alertas*` no coge solo el endpoint, coge también **`/src/api/alertas.ts`** del
servidor de desarrollo, porque la cadena `/api/alertas` está dentro de esa ruta. El módulo se
quedaba con un 500, la aplicación no llegaba a montarse y la pantalla se veía en blanco: iba a
escribir «un 500 en los avisos deja la aplicación en blanco», y era mentira. Lo delató el
control (`/api/buscar` con 500 sí pintaba su error) y la lista de peticiones, que enseñó
`500 http://localhost:5173/src/api/alertas.ts`.

**El segundo**: `unroute` quita la ruta que se registró, y para eso necesita **el mismo
objeto**. Con un filtro nuevo en cada llamada, la intercepción se quedaba puesta y las
pantallas siguientes seguían recibiendo 500 —el fallo aparecía tres secciones más tarde y
parecía otra cosa—.

**Y el tercero, el de siempre**: leer la pantalla nada más cargar mide «Cargando…», porque
React Query reintenta antes de darse por vencida (y hace bien: un 500 de un segundo no es un
fallo). Ahora la puerta **espera al botón**, no a un número de milisegundos.

Las cuatro pantallas quedan medidas en la puerta en cada pasada (`tests/test_errores_de_la_api.py`
guarda las tres lecciones escritas, para que no se repitan).

### El contraste, medido ya pintado y en los dos temas (y el instrumento que mentia)

El §1 del encargo pone esto el primero de *"lo que ya esta bien y no hay que tocar"*: *"el
contraste y los limites de los campos, con las formulas dentro de las pruebas. Eso es
accesibilidad de verdad y esta medida."* `tests/test_contraste.py` mide los **tokens** del
CSS. Lo que faltaba era medir **el texto pintado**: el color real de cada texto sobre **su**
fondo (que casi nunca es el de su propio elemento, sino el de un padre, o un `bg-white/95`), y
**en los dos temas** -- un `dark:` que falte no se ve en los tokens y si se ve aqui.

**Resultado, en cinco pantallas y dos temas: 0 textos por debajo del minimo.** Ni uno en `/`,
`/cesta`, `/avisos`, `/panel` ni `/ajustes`, ni en claro ni en oscuro. Es un resultado
aburrido y es el que se queria: los tokens estaban bien y el pintado tambien.

**Pero el primer intento de medirlo mentia, y eso hay que contarlo.** La primera version decia
"0 textos malos" y era mentira: el JavaScript llevaba el regex de `rgba(...)` con una barra
invertida, se perdio al pasar el texto de Python al navegador, `parse()` devolvia `null`
siempre y **la medida no estaba mirando nada**. Se descubrio poniendo una trampa: un texto
gris claro sobre blanco (contraste 1,13) metido a mano en la pagina. Si la medida no lo ve, la
medida no sirve -- y `verificar_docs.py` ya tenia escrita esa leccion para otro caso (*"un
control que aprueba cuando no tiene con que comparar es peor que no tenerlo: se confia en
el"*). Ahora **la trampa esta dentro de la puerta**: cada pasada comprueba que la medida ve un
texto ilegible puesto a mano, antes de creerse el cero.

### Lo que se pulsa, medido **ya pintado**: siete objetivos por debajo de 44 px

El §3.3 del encargo lo pide con estas palabras: *"lo que se toca con el carro en marcha
--tachar, sumar uno, quitar uno, meter en el carro-- va abajo y grande. **Las siete zonas por
debajo de 44 px que estan medidas son solo el minimo legal**: en la lista, el objetivo no es
44, es que se acierte sin mirar."*

Las pruebas de codigo comprobaban que la clase `min-h-[44px]` **esta escrita**. Medir lo que
el navegador **pinta** es otra cosa, y son siete cosas distintas:

    «−» y «+» de la cantidad      37 x 44   <- justo lo que se toca con el carro
    «Estado de las cadenas»      358 x 24   el desplegable de la cabecera, en todas las pantallas
    «Por que esta en esta posicion» 306 x 16  uno por alternativa, en la ficha del grupo
    «Cesta» (cabecera)            43 x 44   **un pixel** por debajo del minimo
    «Favoritos» / «Ajustes» / «Salir»  20 de alto
    el nombre del producto en /avisos   21-24 de alto
    «Salir» y las cadenas en /ajustes   20 y 30 de alto

**El caso que mas importa es el primero**, y es el que el encargo nombra: los botones de
sumar y quitar uno median 37 px de ancho porque un solo caracter con `px-3` no llega a 44 --
el alto estaba, el ancho no. Ninguna prueba de codigo lo veia: la clase estaba puesta y el
boton se veia bien. Un `min-w-[44px]` en el boton compacto (`ui.tsx`) lo arregla en todas las
pantallas a la vez.

Los otros seis se arreglaron uno a uno (el desplegable de la cabecera y los de la ficha a 44;
los enlaces de la lista, los de los avisos y los de ajustes con `min-h` y `min-w`). Y quedan
**dos que se dejan a proposito**, dichos en la propia puerta para que no parezcan olvidos:

  - **Un `input` dentro de un `<label>` no es el objetivo**: el objetivo es el label, que es
    lo que se pulsa. Los cinco filtros del buscador salen como `input` de 16 px y su etiqueta
    mide los 44 que manda el diseno.
  - **Un enlace dentro de una frase no es un control**: «...buscalo en la cesta» son
    palabras, no un boton, y agrandarlas romperia el texto. Se marcan como `(frase)` y se
    dejan estar.

**Medido despues, en las seis pantallas**: `0` cosas por debajo de 44 px en `/`, `/cesta`,
`/grupo/<id>`, `/avisos`, `/panel` y `/ajustes`. La comprobacion se queda en la puerta del
navegador (`_toques_pequenos`), que es donde se puede medir: una prueba de codigo no puede
saber cuanto mide un boton pintado.

### La puerta del navegador, a fondo: (b), el §3.4, los avisos y la regla que no se salta

Tercera pasada por la interfaz en un navegador de verdad, esta vez para cubrir lo que aun no
miraba. **No salio ningun fallo del producto**, y eso tambien es un resultado: los tres
fallos de la primera vez (React Query pausando los cambios sin cobertura, la frase ausente en
la pantalla a la que se llega buscando, el arranque con dos listas de casa) y los dos de la
segunda (el ejemplo disparate de la primera vez y el «Deshacer» que se escondia) ya estan
arreglados, y lo que se anadio ahora lo pasa a la primera.

**Lo que se anadio, y que ya se comprueba:**

    la campana pide el aviso y dice «Te aviso»                  punto 6, la mitad de pantalla
    el aviso pedido aparece en /avisos, con lo que promete       y sin el, esa pantalla esta
                                                                 vacia para siempre
    el cambio sin cobertura QUEDA GUARDADO en el movil           se mira `localStorage`, que es
                                                                 la mitad que no se ve
    la cola se vacia SOLO cuando el servidor los aplica          `{}` despues de «Se ha subido»
    un grupo de UNA SOLA CADENA no lleva frase                   la regla que no se salta (§4)
    y dice por que no la lleva                                   «sin comparación: está en una
                                                                 sola cadena»

El caso de «una sola cadena» se busca **en gold y no con el buscador**, y eso se aprendio
intentandolo: en los primeros cuarenta resultados de cinco busquedas **no sale ninguno de una
sola cadena** -- los productos sin pareja no aparecen ahi --, asi que la unica forma de
comprobar esa regla es ir a un grupo concreto. Medido hoy: hay **30.821 grupos de una sola
cadena** con precio, o sea que el caso no es un rincon: es la mayoria del catalogo, y la frase
no se puede decir en ninguno de ellos.

**Y la puerta es ahora repetible**, que es lo que la hace util de verdad. Las tres cosas que
lo impedian eran de la prueba, no del producto, y las tres se arreglaron:

  - **La cuenta es fija** (`prueba-navegador`), no nueva en cada pasada: la API limita las
    altas por hora (`ALTAS_POR_HORA`) y la sexta pasada se quedaba sin cuenta.
  - **Se cuentan las lineas de forma relativa** (`5 -> 4`), no «cero despues»: la lista va
    creciendo entre pasadas.
  - **Se espera a que la pantalla cambie**, en vez de leer justo despues del clic: quitar una
    linea manda un PATCH y vuelve a pedir la lista, asi que leer en el acto mide la pantalla
    de antes. Es el mismo error que ya habia cometido en la ficha.

Comprobado con **dos pasadas seguidas**: las dos en TODO BIEN.

### La primera vez y el «Deshacer»: dos cosas que el navegador enseno mal

La puerta del navegador ya estaba; lo que faltaba era que **mirara tambien las dos
condiciones que aun no tocaba** -- (b) la primera vez, y el «Deshacer» del §3.4 --. Al
hacerlo salieron dos fallos mas, y los dos son de los que no se ven leyendo el codigo.

**1. El ejemplo de la primera vez era un disparate.** Buscar «aceite de oliva» devolvia
**«Picos sin gluten»** el primero, y la tarjeta de la primera vez -- lo unico que ve quien
acaba de llegar -- lo pintaba tal cual: «Picos sin gluten 13,90 €/kg · un 9 % menos» como
ejemplo de comparar precios. Cualquiera que lo lea piensa que la aplicacion esta rota, y con
razon. Arreglado con la regla que ya estaba escrita para elegir los cuatro basicos: **el
nombre tiene que repetir la palabra buscada**, se piden cinco resultados y se coge el primero
que la cumpla; si ninguno la cumple, esa busqueda se cae sola. Medido despues en el
navegador: los cuatro ejemplos son «Leche entera», «Pan de molde integral sin corteza»,
«PRODUCTO ALCAMPO Aceite de orujo de oliva» y «Agua mineral Dia 1,5 L», cada uno hablando de
lo que se busco.

**2. El «Deshacer» desaparecia justo cuando mas falta hace.** El bloque estaba bien escrito,
pero vivia **dentro del lado "si hay lineas" de un ternario**: al quitar **la ultima** linea
la lista se queda vacia, ese lado no se pinta, y con la linea se iba el «Deshacer». Es el
momento exacto en que alguien quiere volver atras. Arreglado dejando de partir la lista con
un ternario: el «la lista esta vacia» es una pieza mas y el «Deshacer» es hermano suyo.
Medido en el navegador: quitar la unica linea -> «Has quitado · Leche semidesnatada ·
Deshacer» -> y «Deshacer» la trae de vuelta.

Los dos tienen su prueba en el mismo commit: `tests/test_deshacer.py` (3, que fija **la
forma** -- que no vuelva el ternario --, porque el fallo era donde estaba el bloque y no lo
que decia) y `tests/test_primera_vez.py`, que ahora exige la regla del nombre.

**Y la puerta del navegador cubre ya (b) y el §3.4**, con sus tiempos:

    ok  sin sesion sale la tarjeta de la primera vez (no un esqueleto)
    ok  y no es una visita guiada: no hay pasos que pasar
    ok  los cuatro ejemplos hablan de lo que se ha buscado
    ok  al quitar sale «Has quitado … Deshacer», sin preguntar nada
    ok  «Deshacer» la trae de vuelta, tambien si era la ultima linea

### La interfaz, en un navegador de verdad: tres fallos que no se veian de otra forma

Hasta hoy todo lo de la interfaz estaba comprobado **leyendo el codigo** (las pruebas de
contraste, de movil, de la cola...) y en un `tsc` limpio. Eso deja fuera lo que solo pasa
cuando alguien pulsa: que un boton no este, que una peticion se quede pausada, que los
numeros salgan sin sujeto. Con `patchright` -- el navegador que ya estaba puesto para los
colectores -- se puede abrir la aplicacion **en un movil de 390 x 844 con `has_touch`** y
hacer el recorrido entero. Eso es `plataforma/prueba_navegador.py`, y en su primera pasada
encontro tres cosas:

**1. React Query pausaba los cambios sin cobertura, y la cola no se llenaba nunca.**
Por defecto, una mutacion con `navigator.onLine` falso **no se manda, no falla y no avisa**:
queda pausada en memoria y se reintenta sola al volver la red. Medido en el navegador:
tachar sin cobertura no pintaba la linea tachada, no encolaba nada y no decia nada; y el
`PATCH` salia al volver la red -- o sea que el cambio vivia en memoria y se perdia al cerrar
la pestaña, que es justo el caso que la cola existe para cubrir. Arreglado con
`networkMode: 'always'` en las dos mutaciones de la lista. Despues, medido:
`net::ERR_INTERNET_DISCONNECTED` -> cola escrita **en 200 ms** con la hora del movil ->
al volver, «Se ha subido 1 cambio que hiciste sin cobertura». **Ninguna prueba de codigo
podia verlo: es una politica interna de la libreria.**

**2. La frase de «¿esto esta caro?» no estaba donde se llega buscando.** Punto 3 del
encargo, y estaba solo en la ficha del producto. El navegador enseno lo que ve una persona:
buscar "leche", abrir el resultado, y encontrarse «ALTERNATIVA QUE GANA CONTIGO / Dia /
1,05 €/l» con un «74 %» al lado -- numeros, ninguno con sujeto. Ahora la pantalla del grupo
pinta **la misma frase** (`logica/frase.ts`, la misma funcion y la misma regla: si el grupo
no es de fiar, no hay frase) y **antes** que los numeros.

**3. Y un fallo de arranque: la API no arrancaba con dos listas de casa.** Aplicando las
migraciones de verdad en un PostgreSQL limpio, `migra()` reventaba:

    psycopg.errors.UniqueViolation: could not create unique index "lista_de_casa_unica"
    DETAIL: Key (es_de_casa)=(t) is duplicated.

`almacen.migra()` aplica **todos** los `.sql` **en cada arranque**, y `001_esquema.sql`
creaba un indice unico sobre `es_de_casa` a secas ("una sola lista de casa en todo el
sistema") que `003_mas_de_dos.sql` borra para que cada persona tenga la suya. Como el que
crea va antes por numero, **el que borra perdia siempre**: el segundo arranque lo resucitaba.
Y dos listas de casa es el estado normal de esta aplicacion. Arreglado quitando la creacion
de `001` (el `DROP` de `003` sigue, para las bases que lo tengan), con `tests/test_migraciones.py`
vigilando esa clase de pelea -- **un fichero viejo que se reaplica no puede contradecir a
uno nuevo que lo corrige** -- y con el caso concreto comprobado en `prueba_e2e.py`: dos
personas, cada una con su lista de casa, y borrarlas.

**La puerta mecanica de (a).** El recorrido entero, con sus tiempos, en un navegador:

    ok  la cabecera dice de que dia son los precios        ok  el pasillo se queda STICKY
    ok  el buscador se ve y se toca sin buscar el boton    ok  tachar sin cobertura dice que espera
    ok  sin escribir nada hay algo que leer                ok  y NO lo pinta como un error
    ok  la cuenta entra (fija, no nueva: hay tope)         ok  al volver se sube solo, y lo dice
    ok  el resultado abre la ficha                         ok  los avisos existen y se abren
    ok  LA FRASE, antes que la tabla                       ok  sin excepciones de JavaScript
    ok  la ficha deja pedir el aviso (la campana)
    ok  anadir a la lista, y el boton dice «En la cesta»

    abrir la aplicacion 2,4 s | a la ficha con la frase 0,9 s | a la lista 0,8 s
    tachar sin cobertura 1,2 s | a los avisos 0,7 s

Y desde entonces la puerta ha ido creciendo con **lo que faltaba por mirar**: el escaner con
un codigo de verdad y el enlace de invitacion abierto por otra persona (los dos, unas
secciones mas arriba), todo lo que se pulsa medido **ya pintado** (§3.3) y el contraste del
texto pintado en los dos temas (§1), con su trampa para saber que la medida mira. Hoy son
**mas de sesenta comprobaciones** en la misma pasada, y las tres ultimas veces seguidas ha
dicho `TODO BIEN`.

**Esto NO cierra (a)**: la condicion se juzga *contra la madre del dueno*, y eso lo dice
`docs/PRUEBA-15-SEGUNDOS.md` con alguien que no haya escrito estas pantallas. Lo que hace
es quitar de delante todo lo que haria imposible cumplirla, y avisar en el acto si vuelve.
La receta para correrlo esta en `docs/OPERACION.md`.

### Los cambios sin cobertura: tachar funciona sin red, y se sube solo

La ultima pieza del punto 2, y la que el encargo describe con mas detalle (§3.5) para la
pantalla que *"merece mas cuidado que el resto junto"*:

    - que tachar funcione igual sin red, sin ruedecita ni error;
    - una linea discreta cuando hay cambios sin subir: «3 cambios se subiran al volver
      la cobertura»;
    - y que al volver, se suba solo y se diga en una frase.
    - **Que no**: un aviso rojo de error. Estar sin cobertura en un supermercado no es
      un fallo de la aplicacion.

La mecanica de la API ya estaba desde el primer dia -- **el identificador de linea lo
genera el movil**, cada cambio viaja con **su hora** (`momento`) y existe
`POST /listas/{id}/sincronizar` --; **lo que no existia era guardarlos**. Y sin guardarlos,
"tachar sin red" era un error que habia que leer y reintentar. Lo que se hizo antes (que ese
error no fuera rojo) arreglaba el color, no el problema.

**`estado/cola.ts`**: la cola vive en el **aparato** (`localStorage`, clave con version),
no en memoria -- si se cierra la pestaña en el pasillo, los cambios siguen ahi --, con la
hora **del movil** puesta al tocar, un cambio por linea (gana el ultimo, pero sin perder
campos distintos del mismo PATCH) y `try/catch` en todo: si el navegador no deja escribir,
se dice (`null`) en vez de tragarse el fallo.

En la lista (`Cesta.tsx`):

  - un cambio que falla **por red** se guarda en la cola en vez de pintar nada: ya no es un
    error, es un cambio que espera (el rojo se queda para lo que **la API contesta que no**:
    un 403 de una lista de solo mirar, un 500);
  - **la linea se pinta con lo que espera aplicado encima** (`conPendientes`), asi que
    tachar sin red se ve en el mismo toque -- "que funcione igual" no es que se guarde, es
    que se vea --, y el total de abajo sigue siendo el del servidor: por eso esta la linea
    de "N cambios sin subir", para que nadie compare un total que todavia no cuenta lo que
    acaba de tocar;
  - la linea discreta, y la frase **«Se han subido 3 cambios que hiciste sin cobertura»**
    cuando vuelve;
  - **se sube solo** al volver la cobertura (`online`) y al abrir la lista, y **la cola se
    vacia solo cuando el servidor dice que los aplico**: si se vaciara al mandarlos, un
    fallo en el camino perderia cambios hechos de pie en la tienda.

**Verificado de punta a punta, no solo en el navegador**: `plataforma/prueba_e2e.py` manda
un cambio con `momento = 2026-09-23T18:04:00` a `/sincronizar` y comprueba que la linea
acaba tachada **con esa hora** (`tachado_en=2026-09-23 18:04:00+00:00`) y no con la de
llegada, que es el invariante del encargo. Probado tambien en
`tests/test_cola_sin_cobertura.py` (6 pruebas) y en `tests/test_sin_cobertura.py`, que ahora
fija que **sin red no se pinta ningun error**.

### Un fallo de esquema que impedia darse de baja: `tachado_coherente`

Lo encontro la verificacion de punta a punta en su primera pasada **con la cola puesta**, y
es de produccion: `DELETE FROM usuario` falla si esa persona habia tachado algo en una lista
que sobrevive (compartida, o de casa).

    lista_linea.tachado_por  uuid REFERENCES usuario(id) ON DELETE SET NULL  (001:95)
    tachado_coherente        CHECK ((tachado_por IS NULL) = (tachado_en IS NULL))  (001:100)

Las dos cosas juntas no pueden ser: al dar de baja a alguien, PostgreSQL pone
`tachado_por = NULL` y deja `tachado_en` -- que es lo correcto, la linea se tacho y eso paso
--, y la fila incumple el CHECK: **el DELETE falla entero**. Es el mismo caso que arreglo
`005_borrarse_del_todo.sql` con `anadido_por` (de `RESTRICT` a `SET NULL`); aqui el
`SET NULL` ya estaba, pero el CHECK lo dejaba sin efecto. En produccion es un **500 al darse
de baja**.

`sql/007_tachado_sin_quien.sql` deja el invariante que de verdad importa -- **no puede haber
"quien" sin "cuando"** -- y permite lo que si es legitimo: que haya "cuando" sin "quien",
porque quien lo tacho ya no esta.

### La verificacion de punta a punta, y el fallo que encontro

Las pruebas de `tests/` sustituyen PostgreSQL a proposito -- una prueba que dependa de la
base del dia mide el calendario, no el codigo --, y eso deja un hueco que **no se ve hasta
que alguien arranca el contenedor: el SQL y las migraciones no los ejecuta nadie**. El 23
de septiembre de 2026 ese hueco dejo pasar un fallo, y lo encontro esta verificacion:

    GET /api/bajadas?solo_mios=true   **sin sesion**
      antes:  {"solo_mios": true,  "resultados": [60 filas del catalogo entero]}
      ahora:  {"solo_mios": false, "resultados": [60 filas del catalogo entero]}

La respuesta decia que habia filtrado por "lo mio" porque el cliente lo habia pedido, y no
habia filtrado nada: sin sesion no hay "lo mio" que filtrar. La pantalla habria ensenado
**sesenta bajadas del catalogo entero bajo el titulo "Lo tuyo que ha bajado"**. Las pruebas
unitarias miraban los grupos que llegaban al SQL -- y eso pasaba igual de bien con el campo
mintiendo --, asi que no lo vieron. Ahora el campo **dice si se filtro, no si se pidio**, en
la API y en la pantalla (el titulo y el vacio se eligen por `d.solo_mios`), y la prueba
unitaria comprueba el campo.

**Y queda un instrumento para no volver a depender de que alguien mire:**
`plataforma/prueba_e2e.py`. Ejecuta contra un PostgreSQL **desechable** (contenedor en el
5434, que no es el de casa: el de Cesta no publica su 5432) todo lo que las pruebas
sustituyen:

    docker run --rm -d --name cesta-prueba-db -e POSTGRES_PASSWORD=prueba \
        -e POSTGRES_USER=cesta -e POSTGRES_DB=cesta -p 127.0.0.1:5434:5432 postgres:16-alpine
    uv run python -m plataforma.prueba_e2e
    docker rm -f cesta-prueba-db

    las seis migraciones       se aplican una a una sobre una base vacia
    /api/listas/{id}           el pasillo en cada linea, con el orden del recorrido
    /api/habituales            la cuadricula: origenes=['tuyo', 'basico']
    /api/alertas               la alerta con el nombre y el precio del producto
    el vigilante               una pasada: {'miradas': 1, 'saltan': 1, 'apuntadas': 1}
    /api/buscar?q=lece…        corregido='leche entera'
    /api/bajadas?solo_mios     con sesion -> true y 2 filas; sin sesion -> false y 60

Salida de la ultima pasada: **TODO BIEN**. Es lo que hay que correr **antes de desplegar**
una imagen nueva, y esta escrito donde se busca (`docs/OPERACION.md`).

### El pack: medido, y **no se usa como guarda** (pero si para decirlo)

Es la dimension que `docs/BACKLOG.md` llamaba "la de mas valor" despues de la barra: **642
grupos mezclan un pack con sueltas** (un pack de 6 botellas de 1,5 l con una botella
suelta). Nadie se contradice -- todas son agua de 1,5 l -- y el precio por litro se puede
comparar perfectamente; el problema es otro: *"donde compro agua" acaba recomendando nueve
litros frente a uno y medio*, sin decirlo.

**Se midio antes de tocar nada, y el resultado cambia la decision.** Lo primero que parece
razonable es una guarda como la de los ejes: "dos packs declarados distintos no van al
mismo grupo". Medido sobre el gold del 23 de septiembre de 2026:

    pares ciertos (mismo EAN, dos cadenas)                     1.809
    con `unidades_pack` contradicho entre cadenas                120   (en 85 codigos)
    con los DOS declarados y > 1 y distintos                       0
    grupos con dos packs > 1 y distintos                          12
    de esos 12, cuantos son de verdad un error                     0

Las dos ultimas lineas son las que deciden. **`1` no es una declaracion: es el silencio**
-- el valor que sale cuando la cadena no publica el campo y no se puede deducir del nombre
--, y la prueba son esos 120 pares: la misma Coca-Cola de dos botellas lleva `1` en una
cadena y `2` en otra, **con el mismo codigo de barras**. Una guarda por el pack separaria
esos pares, que son el mismo producto.

Y los **12 grupos** que una guarda estrecha (solo `> 1`) separaria tampoco son un error:
son el mismo producto en formato de 2 y de 4 (lonchas de embutido de Mercadona y de
Carrefour, «Salami extra» y «Salami extra 2x120 g»), o una errata de lectura
(`85x4 g` leido como 85 unidades). Separarlos **quitaria comparaciones legitimas**, que es
el error caro en esta aplicacion -- el mismo argumento que dejo al medoide fuera.

**Lo que se hace en su lugar, que es lo que resuelve el problema de verdad: decirlo.**
`GET /api/grupo` ya manda `unidades_pack` **solo cuando es mayor que 1** -- el silencio no
viaja, igual que en los ejes -- y la ficha lo ensena al lado del precio («· pack de 6»,
`paginas/Grupo.tsx`). Asi "donde comprar esto" se entiende: el precio por litro es del
pack, y se ve.

Y queda **medido y con trinquete** para que nadie lo rehaga a ciegas:
`projects.cesta.ejes` imprime los codigos con el pack contradicho (85) y
`tests/test_atributos.py` le pone techo. **Si ese numero baja mucho**, es que las cadenas
empiezan a publicar el campo de verdad, y entonces se puede volver a mirar si el pack sirve
para separar.

### El buscador encuentra con faltas de ortografia

Lo pide el §8 del encargo: *"que encuentre con faltas de ortografia y sin tildes (ya se
normaliza en el dato)"*. Las tildes y las mayusculas si se normalizaban; **una letra
cambiada devolvia cero resultados**. Medido contra la API viva el 23 de septiembre de 2026:

    leche entera   -> 3 resultados        lece entera   -> 0
    azucar         -> 3                   leche entea   -> 0
    detergente     -> 3                   detergnete    -> 0
                                          asucar        -> 0

**Como funciona, y por que asi.** `catalogo.corregir` mira **palabra a palabra** contra el
diccionario del catalogo -- las palabras que existen de verdad, 21.482, montadas una vez
por conexion en 0,06 s -- y cambia solo la que no existe por la mas parecida. Dos reglas, y
las dos salen de un fallo medido:

  - **El mismo tamano (±1 letra).** El parecido de Jaro-Winkler premia los prefijos, asi
    que sin esto `asucar` se "corrige" a **`asua`** (0,922) en vez de a `azucar` (0,900).
    Cambiar una palabra por otra que no tiene nada que ver y ensenar esos resultados es
    peor que no corregir.
  - **A igualdad de parecido, la palabra que mas aparece.** No es un desempate decorativo:
    `natral` empata con `natrual` (que existe **una** vez, porque alguien la escribio mal
    en su ficha) y con `natural` (que aparece miles). El parecido se redondea a dos
    decimales para agrupar a los que empatan de verdad, y ahi manda la frecuencia: es lo
    que distingue una palabra de la errata de una tienda.

**Y es el ultimo recurso**: primero se busca lo escrito, y la correccion solo entra cuando
no hay nada. Eso hace dos cosas -- no se paga en las busquedas que ya funcionan, y no puede
"corregir" una palabra que si tenia resultados.

**La respuesta dice lo que se ha entendido** (`corregido`), y **solo si ha servido**: si la
busqueda corregida tampoco encuentra nada, no se anuncia ninguna correccion. Anunciar una
correccion que no arregla nada seria culpar a quien escribe de un fallo que es nuestro.

Medido despues, sobre el gold de hoy y llamando a la ruta tal cual:

    lece entera    40 resultados   corregido='leche entera'    primero «Leche entera»
    leche entea    40 resultados   corregido='leche entera'
    detergnete     40 resultados   corregido='detergente'
    asucar         40 resultados   corregido='azucar'
    yogur natral   40 resultados   corregido='yogur natural'
    azucar         40 resultados   corregido=None              (ya estaba bien)
    leche entera   40 resultados   corregido=None
    xyzzy           0 resultados   corregido=None              (no se inventa nada)

Coste: 60-94 ms por busqueda, igual que antes; el diccionario se monta al abrir la conexion
(0,06 s) y no en cada consulta. Probado en `tests/test_busqueda_faltas.py` (9 pruebas, gold
de mentira y PostgreSQL fuera), incluidos los dos casos que sostienen las dos reglas
(`asucar` -> `azucar` y `natral` -> `natural`).

### La campana, la pantalla de avisos y el punto en el icono

La mitad de fuera del punto 6. Dentro ya estaba el vigilante (la alerta salta cuando
cambia gold, sin que nadie abra nada); esto es lo que se ve cuando salta, y el encargo lo
pedia literal: *"un punto en el icono, y al abrirlo **la frase entera** --«el aceite que
sigues esta a 3,89 €/l en Alcampo, el mas barato en 90 dias»--, no un numero rojo sin
contexto."*

**Tres piezas, y cada una resuelve una parte de la frase:**

    la campana     en la ficha del producto: «Avisarme si baja». Pide el aviso **util**
                   (`minimo_90d`) sin preguntar ningun numero, porque es el unico tipo
                   que no exige saber cuanto deberia costar algo -- y casi nadie lo sabe
                   hasta que ve la curva. Sin sesion no se pinta.
    la pantalla    `/avisos`: lo que ha bajado **con su frase**, lo que salto y ya no
                   esta a ese precio (con la frase **guardada** y su fecha), y lo que
                   esta esperando. Mas «Ya los he visto».
    el punto       en el icono de Avisos de la barra de abajo: cuantos han saltado y
                   nadie ha visto.

**La frase sale del servidor, siempre.** `por_que` para las que se cumplen hoy y
`salto_texto` para las que saltaron; la pantalla no monta ninguna. Recalcularla en el
navegador daria una segunda version de la misma verdad, y **la guardada no se puede
recalcular**: se midio contra el gold de ese dia, y gold es otro cada manana. Un aviso que
cambia de texto al dia siguiente no es un aviso, es un rumor.

**El punto cuenta lo que ha saltado, no lo que hay.** Una alerta que existe y no se ha
cumplido es una promesa, no una noticia. Y se apaga **a mano** (`POST /alertas/vistas`):
abrir la pantalla en el autobus no puede dar por leido lo que no se ha leido. El punto va
con `aria-hidden` **y** un `sr-only` con el numero: un punto no dice cuanto.

**Y una decision que hubo que tomar y escribir: la barra de abajo pasa a cinco
destinos.** Cuatro eran "los cuatro de estar un rato en la tienda" y habia una prueba que
lo fijaba. Avisos no es un sitio donde estar: es **lo unico que la aplicacion hace por ti
mientras no la miras**, y es la respuesta a *"¿ha bajado algo de lo mio?"*. Ponerlo dentro
de otra pantalla habria sido esconderlo en una esquina, que es justo lo que este encargo
quita -- y un punto necesita un icono donde estar. Queda escrito en `Nav.tsx`,
`docs/USABILIDAD.md` y la prueba, que ahora fija los cinco **y su razon**.

Para que la pantalla pueda decir de que producto habla, `GET /api/alertas` **anade la
tarjeta del grupo** (`catalogo.tarjetas`). Y si la tarjeta no llega, la pantalla **no
afirma nada**: dice "Un producto que sigues" y enlaza a la ficha. Pueden ser dos cosas --
que el grupo ya no este en el catalogo, o que **la API que corre sea mas vieja que esta
pantalla** -- y "ya no esta en el catalogo" seria mentira en la segunda, encima sobre un
producto que si existe. La ficha si sabe la verdad y lo dice.

Probado en `tests/test_alertas_pantalla.py` (6 pruebas: dos de la API con gold de mentira
y PostgreSQL sustituido, cuatro de la pantalla leyendo el codigo) y en
`tests/test_vigilante.py`, que fija la mitad de dentro.

### Los detalles que hacen que parezca terminada (§8), uno a uno

El encargo tiene una seccion que no es de diseño sino de acabado, y dice *"ninguno es
grande; juntos son la diferencia entre «un proyecto» y «una aplicacion»"*. Estado de cada
uno, medido sobre el codigo de hoy:

    los estados vacios, todos con una frase      HECHO (componente `Vacio`; el
                                                 «Nada con «».» de la interfaz vieja
                                                 esta arreglado desde el principio)
    los estados de carga, sin saltos             HECHO el 23 sep: `Cargando` reserva
                                                 sitio y hay esqueletos con la forma de
                                                 lo que viene (filas y cuadricula),
                                                 usados donde el contenido empuja
    los errores, «no llego a casa» + reintentar  HECHO (`Fallo` + `textoDeError`), y
                                                 **sin cobertura no es rojo** desde el
                                                 23 sep (`esSinRed`, un solo sitio)
    el buscador: recuerda lo ultimo              HECHO el 23 sep
                                                 (`estado/busquedasRecientes.ts`, 8
                                                 chips, sin repetir, en el aparato)
    el buscador: no exige pulsar una lupa        HECHO (busca al teclear, con 250 ms)
    el buscador: encuentra con faltas            HECHO el 23 sep. Medido antes:
                                                 `lece entera`, `leche entea`,
                                                 `detergnete` y `asucar` daban **0**
                                                 resultados. Ahora dan 40, y la
                                                 respuesta dice lo que ha entendido
                                                 (`corregido`). Ver abajo.
    los numeros, con su unidad al lado           HECHO (`eurosUnidad` pinta «0,96 €/kg»:
                                                 el numero suelto no existe en la
                                                 pantalla)
    el titulo de cada pantalla en la pestaña     HECHO el 23 sep (`componentes/Titulo.tsx`
                                                 + `App.tituloDe`; la ficha y el grupo
                                                 ponen **el nombre del producto**)
    volver atras siempre, y los enlaces que      HECHO (`/favoritos` y `/ajustes` con
    faltaban                                     enlace desde la cesta)

Las dos que quedaban estan hechas y la seccion esta cerrada. La de los saltos, con el caso
que la justifica: en la lista de la compra, `Cargando` era **una linea de texto**; cuando
llegaba la lista, esa linea se convertia en nueve filas y **todo lo de abajo bajaba de
golpe** -- en la pantalla que se usa de pie y con una mano, con el pulgar ya camino de un
boton. Eso no es una espera: es pulsar lo que no era.

Ahora `Cargando` reserva sitio (`min-h`), y hay dos esqueletos **con la forma de lo que va
a venir**: `Esqueleto` (filas, con el mismo `gap-2` que la lista de verdad) y
`EsqueletoRejilla` (tres columnas, para el mosaico). Se usan donde el contenido de verdad
empuja -- los resultados del buscador, las lineas de la lista y la cuadricula --, y los dos
llevan `role="status"` y un texto para lectores de pantalla: **un bloque gris no dice nada
a quien no ve**. Un esqueleto con la forma equivocada es peor que una linea de texto:
reserva el sitio que no es y encima promete algo que no viene. Probado en
`tests/test_esqueletos.py` (4 pruebas).

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

### Laya: el mismo sitio que Jev, sin lista de espera — y medido, no llega

**Por qué.** El dueño pasó un enlace a `convaiinnovations/laya4` con «parece que hace
lo mismo que jev». Hace lo mismo —hasta expone el mismo `POST /v1/systemone`—, y eso
tumba uno de los dos bloqueos que tenía parado el asunto de Jev: la lista de espera.
El otro, ser un tercero en un proyecto que vive en casa, también: Laya son **pesos
abiertos Apache 2.0 que corren en CPU**.

**El nombre pedido no existe.** `laya4` responde 401, pero **ese 401 no prueba nada**:
un nombre inventado a propósito bajo la misma cuenta da el mismo 401 y la misma página
(52.307 y 52.331 bytes), y `?search=laya4` devuelve `[]` mientras los tres de verdad
salen en la misma búsqueda. La familia publicada es `laya` (ModernBERT-large, 421 M),
`laya-multilingual` (mmBERT-base, 322 M, castellano entre 100+ idiomas) y
`laya-typed-decisions`. Si existe un `laya4` privado, **no lo sé**.

**Se instaló y se midió, que es lo que hacía falta para decidir.**

    2,2 GB de pesos · Router(preload=True) 402 s · 2,16 s por petición en CPU
    el enrutador manda el castellano al checkpoint inglés (dice "Latin script,
    language not identified... using default (english)"): hay que forzarlo

**Y el experimento que `docs/JEV-IMPLANTACION.md` daba por bloqueado, hecho.** Es el
diseño de `docs/JEV.md` §4.2 tal cual —una petición por producto, las 12 `Choice`, la
opción «no lo dice»— y su barra del §4.4:

    banco: 215 nombres, 316 declaraciones de las listas a mano, los 12 ejes
    acuerdo 231 (73,1 %)   la barra pide 97 %
    se abstiene 48 · declara otro valor 37
    declara un valor donde la lista calla: 1.230 de 2.264 (54 %)

Los fallos no son ruido, son dos patrones: **11 veces `sin grasa`** donde el nombre
dice entera o semidesnatada, y **6 veces `natural`** donde el nombre dice
descafeinado. Y el 54 % de declaraciones sin prueba es el número que más pesa, porque
con la regla de la casa —el que calla no bloquea— esas declaraciones **cortarían
comparaciones legítimas** si entraran como guarda.

**Lo que de verdad se ha ganado: 27 de los 85 desacuerdos son fallos NUESTROS.**
Auditados uno a uno, en cinco ejes, y no es un hallazgo sobre Laya sino sobre
`core/atributos.py`: `leche` dispara `bebida vegetal` en cualquier cosa con arroz,
avena, soja o almendra (8 casos: «Tostas de pan con avena», «Arroz blanco
precocido»); `cafe` dispara `soluble` con «instantáneo» (5: «Apresto instantáneo para
planchado», «Sopinstant Crema de pollo»); `aceite` dispara `orujo` en **licores** de
crema de orujo y `virgen` en la marca «Virgen del Brezo» (9); `azucar` dispara dentro
de la negación —«bajo en azúcares», «0 % azúcar»— (4); e `integral` dispara en «vino
blanco» (1). **No se arregla aquí a propósito**: `core/atributos.py` mueve los ejes
contradictorios de todo el catálogo y la barra pide 0, así que eso es un trabajo con
su propia medida.

Y una precaución que se midió en vez de suponerla: 12 de los 27 enunciados llevan
dentro el patrón de la lista, así que el experimento podría estar midiendo un espejo.
No lo está: donde copia saca **68,1 %** y donde no copia **76,8 %** (no se distingue
la diferencia, pero no hay indicio de inflado).

**Lo que queda, de más barato a más caro.** (1) Arreglar las listas sobre-disparadas y
volver a correr el mismo banco, que es el mismo comando. (2) Las 19 opciones de
pasillo (`docs/JEV.md` §5), con las 881 claves ya mapeadas de banco: ~30 minutos de
CPU, y sin medirlo **no lo sé**. (3) Afinar con nuestras etiquetas, que es donde su
tarjeta dice que está la puntería — y eso necesita una GPU que no está en casa, así
que es una decisión del dueño, no un paso técnico.

**Lo que NO cambia.** El 64 % de lo que se escapa sigue siendo aritmética de envases
(`docs/JEV.md` §2); el juez de pares sigue siendo el 20 % detrás del canal de
vectores; las ofertas siguen siendo 20 textos; y **nada de esto entra en la tarea de
las 06:00**: `laya` no es dependencia del proyecto (se importa dentro de la función
que mide, y `tests/test_laya_ejes.py` lo fija).

Lo medido, con la receta reproducible, está en **`docs/LAYA.md`**; el instrumento es
`projects/cesta/laya_ejes.py` (corre sin modelo con `--sin-modelo`); y los listados
enteros de desacuerdos e invenciones, en `data/laya_ejes.json`.

### El panel: las tres pantallas que faltaban, y lo que apareció al pintarlas

Era el punto 8 de los que quedaban (líneas 133-137): `GET /api/indice` (`app.js:796-920`),
`GET /api/posicion` (`app.js:925-996`) y `GET /api/ofertas-dudosas`
(`app.js:1110-1156`), más **el filtro del panel por cadenas cercanas** — `Panel.tsx:488`
llamaba `useBajadas(dias, subidas, [])` con la lista vacía y ninguna pestaña leía
`cadenas_cerca`. Con esto **el panel nuevo tiene todo lo que tenía el viejo**, salvo las
dos pestañas en que se decidió no copiarlo.

**Las tres pestañas**, en `plataforma/web/app/src/paginas/Panel.tsx` y el gráfico nuevo en
`componentes/GraficoIndice.tsx`:

- **Índice**: la frase primero («Alcampo es quien más ha bajado (−1,4 %) y Aldi quien más
  ha subido (+0,1 %) en 18 capturas»), después la gráfica de las cinco series con el 100
  de referencia, y **la tabla con capturas, productos y recortados**, que no es un extra:
  cinco colores no se distinguen y el dato no puede depender de verlos bien.
- **Posición**: cada sección con sus cadenas alrededor del cero (barra a la izquierda =
  por debajo de las demás), ordenadas por cuánto se separan. Donde están empatadas, elegir
  tienda no cambia el ticket y esa sección no abre la pantalla.
- **Ofertas dudosas**: ver abajo, porque lo que apareció aquí vale más que la pantalla.
- **El filtro**: una fila de cadenas que **arranca en las que tienes puestas** en Ajustes
  y **dice de dónde sale** («Mirando solo las cadenas que tienes cerca, las de Ajustes»),
  porque quien ve tres cadenas y no cinco tiene que poder saber si faltan datos o si es su
  ajuste. Se aplica a las cuatro pestañas donde significa algo, y en `bajadas` sustituye
  al `[]` que había a mano.

**Lo que apareció al pintarlo, y es el hallazgo del día.** La pestaña de ofertas dudosas
encabezaba así, el 24 de septiembre de 2026, la primera vez que alguien la miró:

    Ampollas en stick anti-fricción Compeed 8 ml.
    anuncia oferta y hoy cuesta mas que su precio de siempre
    1.306,25 €/l  hoy · su precio de siempre 10,45 €/l

Eso no es una oferta dudosa: es **una cantidad mal leída** (un día el envase se leyó como
una unidad y otro como sus 8 ml). Se vio **porque la pantalla empezó a pintar la unidad**,
que hasta hoy no se pintaba. Y no era un caso: ordenada por `posicion_90d`, las diez
primeras eran de esa familia. Tres arreglos, los tres medidos sobre el mismo gold:

1. **La ventana de `core/derive.py` era del producto, no de su unidad.** `precio_base_cent`,
   `min/max_90d` y `posicion_90d` comparaban EUR/ud con EUR/l en **2.239 productos con más
   de una unidad en su historial**. Partiendo por `unidad_canon`: las acusadas con hoy > 3×
   su base pasan de **337 a 17**, los rangos de 90 días absurdos de **3.175 a 1.694** y los
   «más barato de sus 90 días» con la unidad cambiada de **150 a 101**. Un producto que
   cambia de unidad empieza de cero: hasta que no haya base, dice «no lo sé».
2. **El control de la cantidad ya existía en el mismo fichero y no estaba puesto aquí.**
   `bajadas()` compara la cantidad deducida (`precio_cent / precio_unidad_cent`) con un 2 %
   de tolerancia desde el 18 de septiembre; el verificador de ofertas no lo hacía. Ahora sí.
3. **Y el 63 % de la lista no se podía juzgar de ninguna manera.** De las **5.488** ofertas
   anunciadas cuyo precio no baja de su precio de siempre: **3.658** dependen de cuántas
   unidades compres (`3x2` 2.195, `2ª unidad -50 %` 848, `Todo a 1 €` 653, lote, pack) y
   **288** no anuncian un descuento de precio («En pack, más fácil», «Stock Fuera (Unidades
   Limitadas)», «Novedad Alcampo»). **Un 3x2 no baja el precio de una unidad, baja el de la
   tercera**: acusarlas era un error de la pantalla, no una mentira de la cadena. Se juzgan
   **1.538**, y lo que se deja fuera **se cuenta y se dice** (`sin_poder_juzgar`, con sus
   tres motivos).

Eso último cierra dos de los tres puntos de «lo que falta» de `docs/MOVIMIENTOS.md` §4
—distinguir el texto que no es una oferta, y la pantalla en la app—; el tercero
(`solo_online`) sigue pendiente.

**Y la puerta del navegador encontró lo de siempre**: 28 enlaces de nombre de producto por
debajo de 44 px en la pestaña nueva (entre 145 × 19 y 248 × 39), el mismo fallo que ya
apareció en la ficha del producto. Arreglado con `min-h-[44px]`, y las tres rutas nuevas
entran en la lista de pantallas que se miden de pie.

**Cómo se reprodujo todo esto, y una advertencia.** El arreglo de `core/derive.py` cambia
columnas de gold, así que **los derivados se rehicieron sobre el mismo bronze**: se leyó
`gold/precio_diario.parquet` (872.650 filas, 19 días) y se volvieron a escribir
`precio_derivado`, `resumen` y `promos_por_cadena` con `pipeline._derivados`, sin tocar el
bronze ni volver a scrapear. La cadena de las 06:00 hará lo mismo mañana con el código
nuevo. Si alguien compara contra una copia vieja de `precio_derivado.parquet`, los números
no cuadrarán y no es un fallo: es el arreglo.

### La interfaz nueva, servida: el 8080 ya no enseña la vieja

Era lo único que quedaba de la puesta en producción, y se hizo el 24 de septiembre de 2026
por la tarde. Medido antes y después, con el mismo comando:

    antes     :8080/  el index.html viejo (6.858 bytes, del 22 de sep) y /app.js a mano
    despues   :8080/  el paquete de Vite (/assets/index-DkYmH6vZ.js, 892 bytes de index)

**La línea de `docker-compose.yml` llevaba escrita desde antes y no bastaba.** El
contenedor se creó cuando montaba `./web`, y Docker Compose lee los volúmenes al crearlo:
cambiar el fichero no cambia lo que sirve un contenedor que ya está arriba. Hay que
recrearlo (`docker compose up -d web`). Es la clase de fallo que no da ningún error —
Caddy sirve un `index.html` que existe y sale la interfaz vieja —, y por eso `tests/
test_interfaz.py` compara los dos lados leyendo los ficheros.

**El orden importa, y el primero fue la API.** El front nuevo lee
`/api/ofertas-dudosas` → `sin_poder_juzgar`, que la imagen que corría no devolvía (su
respuesta tenía solo `fecha_datos` y `resultados`): servir el front antes de reconstruir la
API habría roto esa pestaña. Así que primero la imagen, después el montaje.

**Y ahí apareció el fallo del día, que solo se ve desplegando.** Con la API reconstruida,
`/api/ofertas-dudosas` contestó **500** en el contenedor:

    File "/app/plataforma/api/movimientos.py", line 178, in _ventana_base
    ModuleNotFoundError: No module named 'polars'
    GET /api/ofertas-dudosas 500 Internal Server Error

El verificador necesitaba la ventana de `core/derive.py` (30 días) y la traía con un import
**dentro de la función**, que es justo lo que recomienda el mensaje de
`test_la_api_no_arrastra_polars`. Esa prueba pasó — mira solo los imports de arriba —, y la
puerta del navegador también, porque corría contra el uvicorn del PC, **donde polars sí
está**. En el contenedor no. Arreglado en el sitio correcto: `VENTANA_BASE` y `VENTANA_PERC`
se mudaron a `core/comparacion.py`, que la API ya importa; `core/derive.py` las reexporta
para que nadie tenga que cambiar una llamada; y `tests/test_imagen_api.py` gana una prueba
que mira **todos** los imports, estén donde estén, más una que comprueba que las dos copias
de la ventana siguen diciendo el mismo número. De 848 a 850 pruebas.

**La comprobación que faltaba, ahora es una herramienta.** `plataforma/prueba_produccion.py`
mira **lo que se sirve**: el paquete compilado, las cabeceras de Caddy con el CSP (que en
desarrollo no existen), la base de casa, y el recorrido de una cuenta de verdad que se crea
y **se borra al final**. Salida de la pasada, con la interfaz nueva ya en el 8080:

    TODO BIEN   (monta, el CSP no bloquea nada, sin excepciones de JavaScript,
                 la ficha contesta con su frase, las tres pestañas del panel,
                 la primera vez con 6 productos reales que tocar, al tachar las
                 dos secciones y la barra diciendo 1, el buscador, la baja)

Los únicos mensajes de consola son **401**, que es como la aplicación pregunta si hay
sesión: no son fallos, y están dichos en la salida para que nadie los cuente como tales.

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
