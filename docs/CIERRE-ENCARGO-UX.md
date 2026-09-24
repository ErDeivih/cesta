# Cierre del encargo de UX (23 de septiembre de 2026)

El encargo esta en `docs/ENCARGO-UX-23SEP.md` (328 lineas, 11 secciones). Este documento
es el **indice de cierre**: que pedia cada seccion, que hay hecho, **con que se comprueba**
y que queda. Es lo que hay que leer para decidir si el encargo esta cumplido; el detalle de
cada cosa esta en `docs/BACKLOG.md` (§0), que es el registro del dia a dia.

---

## La barra, condicion por condicion

    (a) las cuatro preguntas en < 15 s con el movil   **SIN MEDIR** -- necesita una persona
                                                      con un movil. Guion: PRUEBA-15-SEGUNDOS.md
                                                      Lo que la haria imposible esta ya
                                                      descartado y medido: **las cuatro
                                                      respuestas caben en la banda util de
                                                      un 390 x 844** (109..787 px), en el
                                                      navegador y en cada pasada
    (b) la primera vez con datos reales               CUMPLE
    (c) la lista: dos secciones, pasillo pegajoso,
        sin rojo sin cobertura, y sin cobertura
        los cambios se guardan y se suben solos       CUMPLE
    (d) la frase antes que la tabla, y sin frase
        si el grupo no es de fiar                     CUMPLE, y comprobado en el navegador
                                                      en los dos sentidos: con frase en la
                                                      ficha y en el grupo, y SIN frase en un
                                                      grupo de una sola cadena
    (e) pruebas verdes y `verificar_docs` verde       CUMPLE (829 pasan, ruff limpio, docs ok)
    (f) CERO grupos con eje contradictorio            0   CUMPLE
        menos de 30 grupos de 11+                     0   CUMPLE
        `--medir >= 57 %`                             65 % CUMPLE

**(a) es la unica que no puede cerrar quien escribe el codigo**, y lo dice el propio
encargo: se juzga *contra la madre del dueno*, que no va a leer ayuda ni a explorar menus.
El guion -- como se mide, por donde se contesta hoy cada pregunta, que se apunta y donde se
escriben los numeros -- esta en `docs/PRUEBA-15-SEGUNDOS.md`.

---

## Seccion por seccion

    §0  el cambio de marco            Cesta contesta preguntas. Las cuatro tienen pantalla:
                                      que me falta (Cesta), esto esta caro (ficha, con la
                                      frase), voy tachando (Cesta, dos secciones), ha
                                      bajado algo de lo mio (**Panel -> Bajadas -> «Solo lo
                                      mio»**, que contesta sin haber pedido nada antes; y
                                      `/avisos`, que contesta lo que pediste con la
                                      campana).
    §1  lo que no hay que tocar       AUDITADO: las seis cosas siguen en pie (abajo).
    §2  la primera vez                HECHO: `LoQueSeCompra` ensena cuatro productos que
                                      compra todo el mundo con su diferencia de hoy, y NO
                                      hay visita guiada. Sin historial sale esa tarjeta; con
                                      historial, el mosaico. **Y la cesta vacia deja de ser
                                      un cartel**: sus dos ramas vacias (sin ninguna lista y
                                      con la lista sin lineas) pintan la cuadricula de un
                                      toque, con seis productos reales y su titulo de donde
                                      salen (`Mosaico`, `vacia`).
    §3.1 por coger / en el carro      HECHO: dos secciones con su cuenta.
    §3.2 el pasillo pegajoso          HECHO: `porPasillo` + `--alto-cabecera` medido con
                                      ResizeObserver.
    §3.3 la zona del pulgar           HECHO: 44 px minimo en todo lo que se pulsa, y el
                                      deshacer y los contadores pegados a la linea.
                                      Medido ya pintado en **ocho pantallas** (entraron la
                                      ficha del producto y el escaner, que no se median: en
                                      la ficha habia cuatro objetivos de 19 px), y ninguna
                                      pantalla se desliza de lado (390 de 390).
    §3.4 deshacer, siempre            HECHO: «Deshacer» al quitar una linea, reanadiendo con
                                      **el mismo id**; tachar se deshace volviendo a pulsar.
    §3.5 sin cobertura                HECHO: los cambios se guardan en el movil con la hora
                                      del movil, se pintan al instante, y **se suben solos**
                                      al volver la cobertura, con su frase. Sin rojo.
    §4  esto esta caro                HECHO los cuatro apartados, en el orden que pide:
                                      la frase **antes** de la tabla y sin inventarse cuando
                                      el grupo no es de fiar (`logica/frase.ts`); donde esta
                                      mas barato y **cuanto se ahorra en euros** («Mas barato
                                      en / Dia · 0,98 €/l · te ahorras 0,27 €/l»); **la curva
                                      con su frase debajo** (`logica/curva.ts`, «es el precio
                                      mas bajo de los 17 dias que tenemos»); y la tabla al
                                      final. Y una regla que salio al medirlo: el ahorro
                                      **no cruza unidades** (ver abajo).
    §5  el mosaico                    HECHO: `Mosaico.tsx` (tres columnas, un toque) y
                                      `/api/habituales` rellenando por escalones con `origen`
                                      en cada tarjeta.
    §6  los avisos                    HECHO de punta a punta y en los tres sitios que pide:
                                      el **vigilante** mira cuando cambia gold (no cuando
                                      entras), la **cadena diaria** pide la pasada en su paso
                                      (`projects/cesta/avisos.py`, entre `emparejar` y el
                                      resumen) y el **resumen diario dice cuantas saltaron**.
                                      En la pantalla: campana en la ficha, `/avisos` con la
                                      frase entera y punto en el icono. Abrir la pantalla
                                      cuesta 13 ms (medido; ver `docs/OPERACION.md`).
    §7  la honestidad                 APLICADA y con prueba donde toca: fecha del dato en la
                                      cabecera, «no lo se» cuando no hay dato, la frase no se
                                      inventa, y el pack se **dice** en vez de cortarlo.
    §8  los detalles                  HECHO entero, las diez filas (tabla abajo).
    §9-§11 contexto y respuestas      Leidos; de ahi salio el reparto del trabajo (el front
                                      lo toca un agente a la vez; quien mide, mide en el
                                      navegador).

## §1 auditado: las seis cosas que no habia que tocar siguen en pie

    1  contraste y limites, con las formulas dentro   tests/test_contraste.py, verde
    2  privacidad: nada de terceros, con prueba      tests/test_sin_terceros.py, verde
    3  la fecha del dato en la cabecera               componentes/Cabecera.tsx:70
    4  la explicacion del emparejamiento              paginas/Producto.tsx:397
    5  cifras tabulares en las columnas de precio     `cifra` (tabular-nums), estilos.css:49
    6  tema por prefers-color-scheme, sin interruptor  estilos.css:23, y no hay interruptor

## §8 auditado: las diez filas

    estados vacios, todos con una frase        HECHO      errores + reintentar      HECHO, en
                                                                                     cuatro pantallas
                                                                                     y ya pintado
    sin cobertura no es rojo                   HECHO      buscar al teclear            HECHO
    ultimas busquedas                          HECHO      numeros con su unidad        HECHO
    titulo de la pestana                       HECHO      volver atras / enlaces       HECHO
    carga sin saltos de maquetacion            HECHO      faltas de ortografia         HECHO

## La regla que salio al medir el §4: **el ahorro no cruza unidades**

El apartado 2 del §4 (donde esta mas barato y cuanto se ahorra) se pinto por primera vez en
un navegador diciendo **«te ahorras 6.872,01 EUR/kg»** en la ficha de un azafran de 0,4 g, y
la pantalla del grupo decia **«+229.833,1 % frente al mas barato»**: las dos comparaban un
precio por kilo con otro medido en unidades.

La regla llevaba escrita en el proyecto desde el primer dia (`core/comparacion.py`,
`resumen.ahorro()`, `api/alertas.py`) y **la interfaz se la saltaba en tres sitios**. Los
tres arreglados, y medido antes y despues sobre el gold de hoy:

    grupos que mezclan unidades                        125 de 39.592
    grupos comparables (mas de una cadena)        8.771  ->  7.918
      diferencias imposibles (> 2.900 %)             54  ->  0
    mediana de la diferencia                      16,5 %  ->  16,0 %

Y la puerta del navegador gana la medida que lo caza sola: **ningun porcentaje pintado**
( ni en la ficha ni en la pantalla del grupo) puede pasar del tope de *"esto ya no es una
oferta"*, con su trampa para demostrar que la medida mira.

---

## Lo que queda, y de quien es la decision

    (a) la medicion de los quince segundos    **de una persona** con un movil. No la puede
                                              hacer quien ha escrito estas pantallas.
    el montaje de la interfaz nueva           **del dueno** (`docker-compose.yml`): cambiar
                                              `./web:/srv:ro` por `./web/dist:/srv:ro`. Es
                                              lo unico que queda de la puesta en
                                              produccion. Auditado el 24 sep, la paridad
                                              que falta son **tres cosas**: el interruptor
                                              de repartir entre dos tiendas, las tres
                                              pantallas del panel y el contador de la barra
                                              de abajo (`docs/BACKLOG.md`, §0).

Ya no quedan tres decisiones, queda una. Las otras dos se hicieron el 24 de septiembre de
2026, medidas antes y despues:

    la imagen de la API      RECONSTRUIDA. `/api/habituales` pasó de 404 a existir, y
                             `q=lece entera` de no encontrar nada a encontrar la leche
                             (la correccion de faltas). Las migraciones 006 y 007 se
                             aplicaron solas al arrancar; antes se comprobo que no habia
                             ninguna fila que las hiciera fallar (0), y despues que la
                             interfaz vieja -- la que se sirve hoy -- sigue entrando y
                             buscando. Detalle y numeros: `docs/BACKLOG.md` (§0).
    la base para la cadena   PUBLICADA en `127.0.0.1:5432`, y solo ahi (ni wifi ni
                             Tailscale). El paso de los avisos pasó de «no lo se» en 6,5 s
                             a «0 saltaron hoy» en 1,1 s, con la clave leida de
                             `plataforma/.env` para no tocar `ejecutar.bat`.

Ninguna de las cuatro es trabajo de codigo pendiente: son una medicion y tres decisiones.

## Como se comprueba todo esto sin creerse nada

**Todo lo de abajo se midio junto, en la misma tarde y sobre el mismo bronze** (el del 23 de
septiembre de 2026), no cada numero de un dia distinto:

    uv run pytest -q                                 829 pasan (2 fallan, ajenas)
    uv run ruff check .                              limpio
    uv run python -m projects.cesta.verificar_docs   los numeros de los documentos
    uv run python -m projects.cesta.ejes             39.592 grupos, 0 con eje contradictorio,
                                                0 de 11+, 642 que mezclan pack, 85 codigos
                                                con el pack contradicho, 41 con la cadena
                                                repetida y 0 de esas sin EAN
    uv run python -m projects.cesta.emparejar --medir 65 % (1.174 de 1.813 pares de verdad,
                                                en 359 s), y en esa misma pasada 40.110
                                                grupos con 0 ejes contradictorios
    uv run python -m plataforma.prueba_e2e           de punta a punta contra PostgreSQL: el
                                                SQL de verdad, la alerta que salta, el paso de
                                                la cadena (`avisos: 1 saltaron hoy`) y lo que
                                                tarda abrir los avisos: 47 ms en frio, 16 ms
                                                en caliente (y el andamio de la prueba, 425 ms,
                                                que no es la aplicacion)
    uv run python -m plataforma.prueba_navegador     LA INTERFAZ en un navegador: las cuatro
                                                preguntas, la cola sin cobertura, los
                                                avisos, el escaner, el enlace de invitacion
                                                abierto por una segunda persona, la curva con
                                                su frase, el ahorro en euros, **las cuatro
                                                respuestas dentro de la primera pantalla**,
                                                TODO lo que se pulsa medido, el contraste en
                                                los dos temas y ningun porcentaje imposible
                                                pintado.
                                                TODO BIEN, con los tiempos de cada paso:
                                                abrir 4,8 s | a la ficha 0,6 s | a la lista
                                                0,8 s | tachar sin red 1,2 s | a los avisos
                                                0,7 s | del panel a lo mio que ha bajado 2,0 s
                                                | escanear 1,0 s

Los dos numeros de grupos (39.592 y 40.110) no se contradicen: `ejes` cuenta los grupos del
gold que escribio la ultima pasada del emparejador, y `--medir` los reconstruye en su propia
pasada para medir el recall. Son dos pasadas distintas del mismo dia, y las dos dan cero en
las condiciones de la barra.

Las dos ultimas son las que no se pueden sustituir por una prueba de codigo: la primera
ejecuta el SQL de verdad (y encontro que la API no arrancaba con dos listas de casa), y la
segunda abre la aplicacion en un movil de verdad y recorre las cuatro preguntas (y encontro
que React Query pausaba los cambios sin cobertura, y que la frase de «¿esto esta caro?» no
estaba en la pantalla a la que se llega buscando). Las recetas, en `docs/OPERACION.md`.

**Y las dos han mentido alguna vez, que es lo que hay que saber de ellas.** La de punta a
punta midio primero "abrir los avisos: 469 ms" por `TestClient`, y esos 469 ms eran httpx en
el mismo proceso (**409 ms los gasta un endpoint que no hace nada**): ahora imprime el
andamio y la aplicacion por separado, 47 ms en frio y 9-16 ms en caliente (medido en cuatro
pasadas). Y la regla de los
documentos aprobo durante una pasada un `docs/OPERACION.md` que seguia con la raya larga
partida en tres caracteres, porque solo miraba una de las dos familias del doble codificado.
Las dos estan corregidas y las dos tienen su prueba de que miran.

Las **dos que fallan** son `tests/test_auditar_secciones.py`, y no son de este encargo: salen
de `core/datos/secciones.yml`, que otro agente tiene modificado sin terminar. Estan dichas
aqui para que nadie las confunda con un fallo de la interfaz.

## La tarea diaria de las 06:00

El encargo tiene una condicion que no se puede romper: **`ejecutar.bat` a las 06:00**
(`rehacer_maestro` -> `reprocesar` -> `pipeline` -> `emparejar` -> `verificar_docs`). No se
ha tocado el `.bat`, y de sus pasos **solo cambia uno**: `emparejar`, que ahora pasa los
nombres a `agrupar_enlaces` (la segunda red de los ejes) e imprime las invariantes. El paso
de los avisos (`projects/cesta/avisos.py`, §6) **va dentro de `run.py`**, que es a quien el
`.bat` ya llama, asi que la forma de la tarea no cambia y tampoco hay que tocar el
Programador de tareas.

    emparejar        ejecutado dos veces hoy con el codigo nuevo: 438 s y 451 s, gold escrito
    ejes             sobre ese gold: 0 contradictorios, 0 de 11+, 0 sin EAN
    verificar_docs   verde sobre ese gold
    avisos           dentro de `run.py`: 6,5 s diciendo "no lo se" (la base no se alcanza) y
                     **codigo de salida 0**, medido dos veces; con base delante, `avisos.py`
                     hace la pasada y el resumen dice `1 saltaron hoy`
    los otros pasos  no importan nada de lo que se ha tocado: `pipeline` usa `core.alcohol,
                     config, derive, promos, secciones, sellos + normalize/storage`;
                     `reprocesar` y `rehacer_maestro`, solo `config`/`schemas`/`storage`

Lo unico nuevo que corre **al arrancar** (no en la tarea) son las migraciones 006 y 007, que
las aplica la API sola (`almacen.migra()` corre todos los `.sql` por orden y son
idempotentes).
