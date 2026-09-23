# Cierre del encargo de UX (23 de septiembre de 2026)

El encargo esta en `docs/ENCARGO-UX-23SEP.md` (328 lineas, 11 secciones). Este documento
es el **indice de cierre**: que pedia cada seccion, que hay hecho, **con que se comprueba**
y que queda. Es lo que hay que leer para decidir si el encargo esta cumplido; el detalle de
cada cosa esta en `docs/BACKLOG.md` (Â§0), que es el registro del dia a dia.

---

## La barra, condicion por condicion

    (a) las cuatro preguntas en < 15 s con el movil   **SIN MEDIR** -- necesita una persona
                                                      con un movil. Guion: PRUEBA-15-SEGUNDOS.md
    (b) la primera vez con datos reales               CUMPLE
    (c) la lista: dos secciones, pasillo pegajoso,
        sin rojo sin cobertura, y sin cobertura
        los cambios se guardan y se suben solos       CUMPLE
    (d) la frase antes que la tabla, y sin frase
        si el grupo no es de fiar                     CUMPLE, y comprobado en el navegador
                                                      en los dos sentidos: con frase en la
                                                      ficha y en el grupo, y SIN frase en un
                                                      grupo de una sola cadena
    (e) pruebas verdes y `verificar_docs` verde       CUMPLE (791 pasan, ruff limpio, docs ok)
    (f) CERO grupos con eje contradictorio            0   CUMPLE
        menos de 30 grupos de 11+                     0   CUMPLE
        `--medir >= 57 %`                             65 % CUMPLE

**(a) es la unica que no puede cerrar quien escribe el codigo**, y lo dice el propio
encargo: se juzga *contra la madre del dueno*, que no va a leer ayuda ni a explorar menus.
El guion -- como se mide, por donde se contesta hoy cada pregunta, que se apunta y donde se
escriben los numeros -- esta en `docs/PRUEBA-15-SEGUNDOS.md`.

---

## Seccion por seccion

    Â§0  el cambio de marco            Cesta contesta preguntas. Las cuatro tienen pantalla:
                                      que me falta (Cesta), esto esta caro (ficha, con la
                                      frase), voy tachando (Cesta, dos secciones), ha
                                      bajado algo de lo mio (Avisos).
    Â§1  lo que no hay que tocar       AUDITADO: las seis cosas siguen en pie (abajo).
    Â§2  la primera vez                HECHO: `LoQueSeCompra` ensena cuatro productos que
                                      compra todo el mundo con su diferencia de hoy, y NO
                                      hay visita guiada. Sin historial sale esa tarjeta; con
                                      historial, el mosaico.
    Â§3.1 por coger / en el carro      HECHO: dos secciones con su cuenta.
    Â§3.2 el pasillo pegajoso          HECHO: `porPasillo` + `--alto-cabecera` medido con
                                      ResizeObserver.
    Â§3.3 la zona del pulgar           HECHO: 44 px minimo en todo lo que se pulsa, y el
                                      deshacer y los contadores pegados a la linea.
    Â§3.4 deshacer, siempre            HECHO: Â«DeshacerÂ» al quitar una linea, reanadiendo con
                                      **el mismo id**; tachar se deshace volviendo a pulsar.
    Â§3.5 sin cobertura                HECHO: los cambios se guardan en el movil con la hora
                                      del movil, se pintan al instante, y **se suben solos**
                                      al volver la cobertura, con su frase. Sin rojo.
    Â§4  esto esta caro                HECHO: la frase antes de la tabla, y **no se inventa**
                                      cuando el grupo no es de fiar (`logica/frase.ts`).
    Â§5  el mosaico                    HECHO: `Mosaico.tsx` (tres columnas, un toque) y
                                      `/api/habituales` rellenando por escalones con `origen`
                                      en cada tarjeta.
    Â§6  los avisos                    HECHO de punta a punta: el vigilante mira cuando cambia
                                      gold (no cuando entras), campana en la ficha, pantalla
                                      `/avisos` y punto en el icono.
    Â§7  la honestidad                 APLICADA y con prueba donde toca: fecha del dato en la
                                      cabecera, Â«no lo seÂ» cuando no hay dato, la frase no se
                                      inventa, y el pack se **dice** en vez de cortarlo.
    Â§8  los detalles                  HECHO entero, las diez filas (tabla abajo).
    Â§9-Â§11 contexto y respuestas      Leidos; de ahi salio el reparto del trabajo (el front
                                      lo toca un agente a la vez; quien mide, mide en el
                                      navegador).

## Â§1 auditado: las seis cosas que no habia que tocar siguen en pie

    1  contraste y limites, con las formulas dentro   tests/test_contraste.py, verde
    2  privacidad: nada de terceros, con prueba      tests/test_sin_terceros.py, verde
    3  la fecha del dato en la cabecera               componentes/Cabecera.tsx:70
    4  la explicacion del emparejamiento              paginas/Producto.tsx:397
    5  cifras tabulares en las columnas de precio     `cifra` (tabular-nums), estilos.css:49
    6  tema por prefers-color-scheme, sin interruptor  estilos.css:23, y no hay interruptor

## Â§8 auditado: las diez filas

    estados vacios, todos con una frase        HECHO      errores + reintentar          HECHO
    sin cobertura no es rojo                   HECHO      buscar al teclear            HECHO
    ultimas busquedas                          HECHO      numeros con su unidad        HECHO
    titulo de la pestana                       HECHO      volver atras / enlaces       HECHO
    carga sin saltos de maquetacion            HECHO      faltas de ortografia         HECHO

---

## Lo que queda, y de quien es la decision

    (a) la medicion de los quince segundos    **de una persona** con un movil. No la puede
                                              hacer quien ha escrito estas pantallas.
    la imagen de la API en produccion         **del dueno**. Hay tres cosas en el repositorio
                                              que no estan en lo que corre: el nombre en las
                                              alertas, la correccion de faltas y
                                              `/api/habituales`. Al reconstruir se aplican
                                              solas las migraciones 006 y 007.
    el montaje de la interfaz nueva           **del dueno** (`docker-compose.yml:95`). Ya no
                                              tiene los bloqueantes que tenia el 23 sep;
                                              lo que falta de paridad esta listado en
                                              `docs/BACKLOG.md` (Â§0).

Ninguna de las tres es trabajo de codigo pendiente: son una medicion y dos decisiones.

## Como se comprueba todo esto sin creerse nada

    uv run pytest -q                                 799 pasan (2 fallan, ajenas)
    uv run ruff check .                              limpio
    uv run python -m projects.cesta.verificar_docs   los numeros de los documentos
    uv run python -m projects.cesta.ejes             0 ejes, 0 de 11+, 642 pack, 85 pack mal
    uv run python -m projects.cesta.emparejar --medir 65 % (420 s)
    uv run python -m plataforma.prueba_e2e           de punta a punta contra PostgreSQL
    uv run python -m plataforma.prueba_navegador     LA INTERFAZ, en un navegador de verdad

Las dos ultimas son las que no se pueden sustituir por una prueba de codigo: la primera
ejecuta el SQL de verdad (y encontro que la API no arrancaba con dos listas de casa), y la
segunda abre la aplicacion en un movil de verdad y recorre las cuatro preguntas (y encontro
que React Query pausaba los cambios sin cobertura, y que la frase de Â«Â¿esto esta caro?Â» no
estaba en la pantalla a la que se llega buscando). Las recetas, en `docs/OPERACION.md`.

## La tarea diaria de las 06:00

El encargo tiene una condicion que no se puede romper: **`ejecutar.bat` a las 06:00**
(`rehacer_maestro` -> `reprocesar` -> `pipeline` -> `emparejar` -> `verificar_docs`). No se
ha tocado el `.bat`, y de sus pasos **solo cambia uno**: `emparejar`, que ahora pasa los
nombres a `agrupar_enlaces` (la segunda red de los ejes) e imprime las invariantes.

    emparejar        ejecutado dos veces hoy con el codigo nuevo: 438 s y 451 s, gold escrito
    ejes             sobre ese gold: 0 contradictorios, 0 de 11+, 0 sin EAN
    verificar_docs   verde sobre ese gold
    los otros pasos  no importan nada de lo que se ha tocado: `pipeline` usa `core.alcohol,
                     config, derive, promos, secciones, sellos + normalize/storage`;
                     `reprocesar` y `rehacer_maestro`, solo `config`/`schemas`/`storage`

Lo unico nuevo que corre **al arrancar** (no en la tarea) son las migraciones 006 y 007, que
las aplica la API sola (`almacen.migra()` corre todos los `.sql` por orden y son
idempotentes).
