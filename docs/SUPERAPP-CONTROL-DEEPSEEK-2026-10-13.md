# Control vivo del nuevo encargo

Objetivo: [GOAL ACTUAL](SUPERAPP-GOAL-ACTUAL.md).
Contrato: [plan B00–B16](SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md).
No usar cifras heredadas para cambiar estas celdas.

## Punto de continuación

Preparación de GPT, 13/10/2026, HEAD inspeccionado `dddc74e`.
Tarea diaria Running al observar; puntero `20261012-162023`, precios del 11,
seis huellas correctas. Ruff verificado; 1.999/74 son resultados del traspaso.
No se ha detenido ni duplicado ingesta, cambiado el catálogo o restaurado una base.
Diagnóstico B04 ejecutado sin bases reales: requerida 300 g, previa 100/100,
una unidad insertada con nota 100 g; segunda contribución descartada. Script:
`uv run python -m scripts.auditar_puente_plan_20261013`.
El estado Running es una foto, no una instrucción de asumirlo al retomar.

Siguiente: B00 guardas e inventario actual → B04 regresiones de los dos puentes
→ B03 adaptador diario Lidl. Los demás paquetes continúan sin esperar a la captura.

| Paquete | Estado de este encargo | Próxima evidencia |
| --- | --- | --- |
| B00 | **cerrado** | Docker levantado, cuatro puertas verdes y la guarda del DSN con siete ensayos |
| B01 | al día | Las seis fuentes con dato de hoy; la tarea corriendo |
| B02 | **leido, no empezado** | La resistencia YA ESTA en los dos; falta sacarla a donde se lea, mas fixtures |
| B03 | **cerrado** | Aceptacion por HTTP (bed5639); queda fuera del criterio usar la zona para elegir |
| B04 | **cerrado** | Aceptación 27/27 contra la API real |
| B05 | pendiente | Caída y reintento entre SQLite/PostgreSQL |
| B06 | pendiente | Inventario por campo/fuente y presupuesto útil |
| B07 | pendiente | Recetas con contenido, versiones y cocina |
| B08 | pendiente | Plan distinto de diario; porción y snapshot |
| B09 | pendiente | Oráculo de asignaciones y artículo efectivo |
| B10 | pendiente | Compra doméstica completa y cantidades concurrentes |
| B11 | pendiente | Gráficas con medida/universo/cobertura |
| B12 | documental iniciado | Estudio de una función y prueba equivalente |
| B13 | pendiente | Recorrido completo no vacío, capturas y errores |
| B14 | pendiente | CSRF real, copias aisladas y logs crecientes |
| B15 | pendiente | Aprendizaje con ejemplos reales reproducibles |
| B16 | pendiente | Dictamen por capacidad y puertas finales |

Pendiente no significa borrar lo existente: reutilizar sus implementaciones y
pruebas; estos criterios solo se cierran cuando corresponden a este escenario.

## Entradas por paquete

### B02 · 13/10/2026 · **sin codigo todavia** · seis rondas de lectura, cinco conclusiones falsas

- **Cambio o hallazgo nuevo**: **la resistencia que B02 pide YA ESTA en los dos colectores.** *Y eso se supo
  despues de **cinco conclusiones falsas seguidas**, todas por concluir antes de leer:*

  ```
  LO QUE YA HAY (leido, con nombre y linea):
    ALCAMPO    RetoWAF (13 usos, y dice DONDE le cortaron) · AVANCE_MINIMO
               · CORTES_PARA_RENDIRSE · MAX_RENOVACIONES · `detener` (`alcampo.py:790-805`)
               · y abre un NAVEGADOR para el reto cuando hace falta
    CARREFOUR  VUELTAS_DE_RESCATE · ESPERA_ENTRE_VUELTAS * 2**(vuelta-1) -- BACKOFF EXPONENCIAL
               · VUELTAS_SIN_BLOQUEO · `_por_que_fallan` (`carrefour.py:518-537`)
    LOS DOS    no inventan catalogo cuando no pueden leer

  LO QUE FALTA DE VERDAD:
    1) SACAR A DONDE SE PUEDA LEER lo que los dos ya cuentan -- hoy se dice POR PANTALLA
       (reintentos, bloqueadas, por que fallan), no en un sitio que se lea despues.
       ** ESTO es lo que falta, y es pequeno. **
    2) FIXTURES -- `tests/fixtures/` EXISTE Y ESTA VACIA. Y el plan pide seis casos.
    3) LA DECISION DEL NAVEGADOR -- ver abajo. Es del propietario y ya se le pregunto.
    4) Y UNA CAPTURA ACOTADA REAL -- la segunda mitad de la aceptacion.
  ```

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**. *Y **nada de
  codigo** en este paquete: seis rondas de lectura.*
- **Evidencia**: `docs/investigaciones/B02-*.md` (siete documentos, **incluidas las correcciones de mis propias
  conclusiones**) · `tests/test_waf_alcampo.py` (9,3 KB).
- **Pendiente o límite exacto**: **hay una decision que es del propietario y no mia.** *El colector de Alcampo
  **abre un navegador** para pasar el reto del WAF* (`test_si_sin_ventana_no_pasa_el_reto_se_abre_la_ventana`).
  *El plan dice:* **«Si exige interaccion humana, marcar `requiere_interaccion`, conservar ultimo valido y
  continuar otras cadenas»** -- *y el codigo **resuelve el reto en vez de marcarlo**.* **Cambiar lo que funciona
  por lo que dice el plan es una decision suya, no un detalle de implementacion.** *Y hay una segunda pregunta
  detras:* **si el colector necesita una ventana, la pasada diaria necesita un escritorio** -- *y eso seria una
  capacidad LIMITADA que hay que declarar.*
- **Siguiente comando o acción**: **cuatro cosas, todas pequenas y todas medidas -- y ninguna era lo que parecia
  en la ronda 105.**

  ```
  1) LIDL -- es el UNICO de los seis que NO llama a `log_run`.
     (alcampo 4 · carrefour 4 · dia 4 · mercadona 4 · aldi 4 · LIDL 0)
     Y el molde esta leido, en alcampo.py:
       717:  t0, errores, filas, truncadas = time.monotonic(), 0, [], 0
       721/729/732:  log_run(FUENTE, 0, 1, time.monotonic() - t0)     <- cada salida de FRACASO
       950:  completa = not detener and errores == 0
       974:  guardar = completa
       1028: log_run(FUENTE, len(filas), errores, segundos, completa) <- el EXITO
     -> Y `completa` NO ES `errores == 0`: es EL JUICIO DEL COLECTOR. Para Lidl, sus datos
        estan en su `resumen` (fichas_leidas, con_precio, precios_con_vigencia_comprobada, region).

  2) CARREFOUR Y ALCAMPO -- escribir su fichero de cobertura por dia, con las 5 lineas de
     lidl.py:278-285, justo despues de `write_parquet`. `cobertura` = "catalogo_entero".

  3) LOS FIXTURES en tests/fixtures/ (existe y esta vacia): desafio · esquema cambiado · pagina
     vacia · corte a mitad · reanudar · publicacion final.

  4) LA DECISION DEL NAVEGADOR -- del propietario. Alcampo ABRE UNA VENTANA para el reto del WAF
     (test_si_sin_ventana_no_pasa_el_reto_se_abre_la_ventana), y el plan dice marcar
     `requiere_interaccion` en vez de resolverlo. Y detras hay otra: si necesita ventana,
     LA PASADA DIARIA NECESITA UN ESCRITORIO -- capacidad LIMITADA que habria que declarar.
  ```

  *Y **lo que ya existe y no hay que inventar**: `core/runlog.py` (`log_run`, `check_drift`) ·
  `core/cobertura.py` (la revision, con error si falta medio catalogo) · `cobertura_diaria.py` (162 lineas:
  `filas_por_dia`, `veredicto`, `--fecha`, `--dias`) · y 11 ensayos de colectores, uno del WAF.*

  ***Ver `docs/investigaciones/B02-y-el-veredicto-leido.md` y los veinte documentos `B02-*.md` mas -- que incluyen
  las SIETE correcciones de mis propias conclusiones.***

  **Y la leccion de las seis rondas, que vale mas que el paquete**: *105 un `grep` con mis palabras («no existe
  nada») · 106 una correccion sin abrir · 107 veinte lineas de lectura · 108 no mirar el directorio · 109 un `ls`
  · y 110 el bloque entero.* **Cada ronda leyo un poco mas y bajo un escalon.** *El arreglo era el mismo las seis
  veces: **abrir el fichero y leerlo entero**.*
  *Lo unico que se compro es que **el error no llego al codigo** -- porque la ronda 105 habria justificado
  **escribir un colector de cero al lado de dos que funcionan**.*
  **Y `ls tests/` habria contestado en la ronda 105 lo que costo cinco.**

### B00 · 13/10/2026 · commits `9a3a4bb`, `7b33a3f`, `c749405`, `fda0f5c`, `491ac0c`

- **Cambio o hallazgo nuevo**: Docker Desktop estaba parado y su servicio también. Se arrancó el
  ejecutable y el motor respondió. **`cesta-prueba-db` no existía**: `docs/OPERACION.md:13` la crea con
  `--rm`, así que el reinicio de Docker se la llevó. Se recreó y se recrearon `prueba-navegador` y
  `recibo-de-prueba` con `almacen.crea_usuario`. **Y se añadió la guarda que faltaba**:
  `comprueba_que_es_una_prueba(dsn)` rechaza el 5432 (la base de casa) y el 5433 (facylf), y también un
  DSN **sin puerto**, porque «no se sabe» no es «es de pruebas». **Y —lo que la hace servir de algo— está
  puesta donde el daño ocurre**: `prueba_e2e.py` la llama sobre su `CESTA_POSTGRES` **antes de importar
  la plataforma** (su `setdefault` respetaba un DSN heredado), y `prueba_copia.py` la llama sobre el que
  le pasa al hijo. **Dos comprobaciones: quien lanza y quien corre.**
- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2019 pasan, 0 fallan, 0 se saltan**
  (2012 + los 7 de la guarda) · `npm test` 74 pasan · `npx tsc --noEmit` 0. **Los siete de la guarda no
  se conectan a nada**: se corren con Docker parado.
- **Evidencia**: `/api/estado` versión `20261013-135533`, `coherente true`, 6 huellas ·
  `docs/investigaciones/B00-verificacion-inicial.md` §6 · `tests/test_b00_guarda_del_dsn.py` ·
  comprobado con la variable puesta a mano: `CESTA_POSTGRES='…:5432/cesta'` → `ValueError` y salida 1.
- **Pendiente o límite exacto**: **ninguno del criterio de B00.**
- **Siguiente comando**: `uv run pytest tests/test_b00_guarda_del_dsn.py -q`

### B03 · 13/10/2026 · commits `3cc4013` … `bed5639`

- **Cambio o hallazgo nuevo**: Lidl **ya estaba** en `ORDEN` y en `CADENAS_QUE_SE_CAPTURAN`; no corría
  porque `run.py` llamaba `main()` sin argumentos y su CLI los exige (`required=True`). Se añadió
  `ARGUMENTOS` en `run.py` con `["--web","--escribir"]`. La **región** sale de `config.CODIGO_POSTAL`
  acreditada por el nombre que publica la fuente (55 regiones), nunca de un CP supuesto. El **veto**
  estaba en una línea de `en_tienda` (`CADENAS` → `CADENAS_QUE_SE_CAPTURAN`) y el motivo,
  `por_que_no_se_compara`, **no lo llamaba producción**. La **región** viaja ahora bronze → silver →
  gold → vista → API (77 de 77 en Lidl), con el histórico rehecho.
- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2012 pasan, 0 fallan** · comprobado por
  HTTP: `/api/estado` con 6 cadenas y la cobertura de Lidl, y `en_tienda` con `lidl` da **401**, no 422.
- **Evidencia**: `data/cobertura/lidl-2026-10-13.json` (`ofertas_semanales_parcial`, `con_precio 77` de
  `79`, `region 28`) · `docs/investigaciones/B03-*.md` (catorce documentos).
- **Pendiente o límite exacto**: **la zona en la comparación de precios.** *Y ahora se sabe **dónde empieza**,
  que no es donde parecía*: `donde_comprar` **no lee `diario`, lee `grupos`** — *el modelo de emparejamiento,
  `data/gold/matching/`* —, y `grupos` **no tiene `region`**. Medido: al añadirla al `SELECT` salta
  `_duckdb.BinderException: Referenced column "region" not found in FROM clause`, y rompe **seis pruebas de
  tres ficheros**. *Se probó y se **revirtió**; el árbol volvió a `2019 pasan, 0 fallan`.*
- **Siguiente comando o acción**: **empezar por `matching`, no por `donde_comprar`.** *Y la decisión de fondo
  es la misma que la del grano de `diario`, una capa más arriba*: **si un producto puede tener precios de dos
  zonas emparejados en el mismo grupo, el grupo deja de ser «un producto» y pasa a ser «un producto en una
  zona»**. *La forma de añadir la columna cuando toque sí está comprobada: **al final del `SELECT`**, que no
  mueve ningún índice.* Ver `docs/investigaciones/B03-la-comparacion-lee-grupos-no-diario.md`.

  **Y el mapa, ya corregido — con una pieza que NO se toca:**

  ```
  NO SE TOCA:  core/grupos_ids.clave_de(fuente, id_fuente)
               -> es el PRODUCTO, y el producto no tiene zona.
               -> Su docstring: «la identidad estable que YA USA MEDIO PROYECTO».
               -> Y es literal: es el `producto_id`, y `estabiliza` hace JOIN sobre ella.
               -> Tocarla rompe el emparejamiento ENTERO, no la comparacion de zonas.

  SE TOCA:     la clave del GRUPO, en `estabiliza` y en el calculo del grupo.
               -> La zona es una propiedad del PRECIO, no del producto.

  Y LA OCTAVA MEDIDA, HECHA — con una corrección importante sobre lo que se creyó al medirla:

  ```
  SE TOCA (1):  projects/cesta/emparejar.py :: grupos_de(...)
                -> AQUI SE FORMA EL GRUPO. Dos zonas, dos `grupo`.

  SE TOCA (2):  core/grupos_ids.tabla_de(filas, grupo_id)
                -> guarda (clave, grupo_id) para manana, y `clave` NO lleva zona.
                -> Con dos zonas habria DOS FILAS CON LA MISMA `clave` y un EMPATE en el join
                   de `estabiliza` cada dia. Determinista -- y conviene que la clave lleve la
                   zona PARA NO TENER QUE DESEMPATAR. Es una MEJORA, no un arreglo.
                -> *** NO HAY NINGUN FALLO ESPERANDO AQUI. Se creyo que si, y era falso. ***

  NO SE TOCA:   core/grupos_ids.estabiliza(...)
                -> recibe `grupo` y le pone numero. Con la clave bien, ya funciona.
  ```

  *Y la corrección, que es lo que más vale de esta serie*: **se midió `estabiliza` con «dos zonas», se vio que
  uno de los dos grupos recibía un id nuevo, y se le puso nombre — «el defecto de las dos zonas».** *Al escribir
  la prueba se vio que **el caso normal hace exactamente lo mismo**:* **es un grupo que se PARTE, y un grupo que
  se parte reparte el número — que es lo único que se puede hacer.** *No hay defecto.*

  ***La lección: no fue una suposición sobre el código, fue una suposición sobre una medida propia.*** *Una
  medida mal interpretada es peor que ninguna, porque viene con números y parece probada. Lo que la caza es
  contrastar: **poner el caso sospechoso al lado del caso normal.*** Ver
  `docs/investigaciones/B03-la-octava-medida-estabiliza-con-dos-zonas.md` (la conclusión falsa) y
  `tests/test_b03_herencia_con_dos_zonas.py` (la que la desmintió, con las tres pruebas que quedan).

  la forma:    `region` AL FINAL del SELECT de `donde_comprar`  (probado: el error no fue de indices)
  el atajo que NO vale: anadir la columna sin tocar la identidad del grupo

  **Y LA NOVENA MEDIDA, HECHA — con esto el mapa esta entero y sin incognitas:**

  ```
  HECHO:    core/grupos_ids.tabla_de -- guarda la zona, si las filas la traen     -- 0d1a50c
  HECHO:    plataforma/api/cesta.py -- donde_comprar la pide, si esta             -- f952c80

  MEDIDO:   projects/cesta/emparejar.py :: grupos_de(...)
            -> la zona va AL LADO DE `cadenas`, en la misma invariante.
            -> «un grupo no puede tener dos productos de la misma cadena» pasa a ser
               «... de la misma cadena EN LA MISMA ZONA».
            -> NO HAY QUE DISENAR NADA: es un parametro al lado de uno que ya existe.

  MEDIDO:   core/matching.py :: agrupar_enlaces(...)
            -> tiene `cadenas: list[str] | None = None` -- ES PARA `cadenas`, NO para atributos.
            -> HAY QUE GENERALIZARLA. Y la condicion que no se puede saltar es:
               *** SIN ZONAS TIENE QUE SALIR EXACTAMENTE LO MISMO QUE ANTES ***
               (es el caso de las otras cinco fuentes, y el de todos los dias hasta hoy).

  FALTA:    (1) generalizar la invariante a (cadena, zona), SIN CAMBIAR el caso sin zona
            (2) que la clave con la que se hereda incluya la zona
            (3) y que donde_comprar HAGA algo con ella -- comparar dentro de la zona, o avisar
  ```

  ***Y LA PRUEBA DE ESE CAMBIO NO ES «con zonas funciona»: ES «SIN ZONAS, SALE LO MISMO».*** *Que es la forma
  de probar una generalizacion, y es lo que hay que escribir primero.*

  **Y ESA PRUEBA YA ESTA ESCRITA — DOS VECES.** *La zona es **el tercer parametro** que entra en
  `agrupar_enlaces`, y los dos anteriores dejaron su prueba:*

  ```
  tests/test_invariante_reparto.py -- 8 pruebas, todas pasan
    test_rechaza_la_union_que_dejaria_una_cadena_repetida      <- LA INVARIANTE
    test_sin_el_parametro_se_comporta_como_antes               <- el parametro `cadenas`
    test_sin_el_parametro_de_nombres_nada_cambia               <- el parametro `nombres`
  ```

  *Y los tres pasos, entonces, no hay que inventarlos — **hay que copiar la forma**:*

  ```
  1) agrupar_enlaces(..., regiones: list[str] | None = None)   -- igual que `cadenas` y `nombres`
  2) que la union por cadena se haga por (cadena, zona) cuando la zona viene
  3) y que con regiones=None salga EXACTAMENTE lo mismo que hoy
  4) y una prueba nueva: test_sin_el_parametro_de_zonas_nada_cambia
  ```

  *De las nueve medidas **ninguna dejo una incognita**; y **las tres que parecian diseno resultaron ser
  precedentes** — `grupos_de` ya tenia la invariante (para las cadenas), y las pruebas ya estaban escritas.*
  Ver `docs/investigaciones/B03-la-red-de-seguridad-ya-existe.md` y `...la-pieza-central-ya-tiene-la-forma.md`.

  **Y LA DECIMA MEDIDA, HECHA — y esta mueve el punto de partida del cambio:**

  ```
  core/matching.py:447 :: enlaces(filas_completas, umbral, ...)
    -> «Lo primero que hace es quedarse con esas SEIS COLUMNAS Y TIRAR EL RESTO: ver `adelgaza`.»
    -> *** POR ESO LA ZONA NO LLEGA: `adelgaza` la tira. ***
    -> El emparejamiento por pares de cadenas NO SABE DE ZONAS -- no por decision,
       porque NADIE SE LAS PASO.
  ```

  *Y el cambio son **cuatro funciones, y el orden de la lista es el orden de la cadena de datos**:*

  ```
  1) matching.py :: adelgaza(...)       -> QUE CONSERVE `region`   *** EL PRIMERO ***
     -> sin esto, los otros tres no sirven de nada.

  2) matching.py :: _asignacion_1a1(...) -> EMPAREJAR POR PAR DE (CADENA, ZONA)
     -> AQUI NACE LA INVARIANTE (el docstring: «dentro de cada bloque y de cada par de cadenas»).

  3) matching.py :: agrupar_enlaces(...) -> `regiones` al lado de `cadenas`; la guarda por (cadena, zona)
     -> con su prueba test_sin_el_parametro_de_zonas_nada_cambia (el molde ya existe dos veces).

  4) grupos_ids.py :: tabla_de(...)      YA HECHO -- 0d1a50c
     -> y `grupos_de` (emparejar.py) pasa `regiones` al lado de `cadenas`.
  ```

  ***Y AL REVES -- EMPEZANDO POR LA GUARDA, QUE ES LO QUE EL PLAN DECIA -- EL CAMBIO HABRIA PASADO LAS PRUEBAS Y
  NO HABRIA HECHO NADA***: *la zona no llega hasta alli.* Ver
  `docs/investigaciones/B03-la-decima-medida-los-enlaces-y-adelgaza.md` y `...la-invariante-nace-en-los-enlaces.md`.

  **Y LAS SIETE PIEZAS, HECHAS** — *la zona recorre ya todo el emparejador:*

  ```
  HECHO:   matching.py :: adelgaza          -> conserva `region`              -- 27756cd
  HECHO:   matching.py :: agrupar_enlaces   -> la guarda por (cadena, zona)   -- 75e625f
  HECHO:   grupos_ids.py :: tabla_de        -> la clave que se hereda         -- 0d1a50c
  HECHO:   emparejar.py :: grupos_de        -> pasa `regiones`                -- 7f0b72d
  HECHO:   api/cesta.py :: donde_comprar    -> pide la zona (si esta)         -- f952c80
  HECHO:   emparejar.py :: COLUMNAS         -> la zona ENTRA por aqui         -- f469015
  ```
  *(`emitir/ocupados` -- dea976a -- y `_bloque` -- 2ad380c -- se **revirtieron** en 0206c2a: **no hacian falta**,
  porque la invariante de la cadena ya separa las zonas.)*

  ***Y EL TRANSPORTE ESTA CERRADO, PUBLICADO Y COMPROBADO***: *`grupos.parquet` con `region`, **63 columnas,
  LIDL 79 de 79**; version `v20261013-155356`; y **38961 grupos sin ninguno con dos zonas**.*
  *Ver `docs/investigaciones/B03-relevo-en-una-pagina.md`.*

  *Y `precio_diario` conserva `1643898 filas, 38 dias` -- el historico rehecho de la ronda 46.*

  ---

  ### ***** CORRECCION IMPORTANTE: LA CONDICION DE LA ZONA NO HACIA FALTA *****

  *Este tramo se dio por cerrado en la ronda 90 con una conclusion que **resulto falsa**, y hay que leer esto
  antes de tocar nada de la zona:*

  **1. La direccion se aplico al REVES, y se revirtio.** *Se relajo la invariante de la cadena a «misma cadena y
  misma zona», con lo que **dos zonas del mismo producto dejaron de estar prohibidas y se juntaron**.*
  *Medido con una prueba de fuego:* `[0, 1, 0]` sin zonas contra `[0, 0, 0]` con zonas -- **al reves**.
  *Revertido en `0206c2a`.* Ver `docs/investigaciones/B03-EL-CAMBIO-ESTA-INVERTIDO.md`.

  **2. Y la condicion que se iba a anadir TAMPOCO hace falta.** *Se escribio la prueba del objetivo con
  `xfail(strict=True)`, esperando que fallara -- **y paso**.* *Y lo que dice ese `XPASS` es la conclusion:*

  > **LA INVARIANTE DE LA CADENA YA SEPARA LOS DOS PRECIOS DE UN MISMO PRODUCTO EN DOS ZONAS**, porque son dos
  > productos de la misma cadena -- y un grupo no puede tener dos.

  *O sea: la zona **separa sola**, y lo unico que hacia falta era **no relajar la invariante que ya estaba**.
  Ver `tests/test_b03_la_zona_separa.py` (dos pruebas, verdes) y el commit `372968b`.*

  ### *** LO QUE QUEDA DE B03, DE VERDAD, Y ES SOLO ESTO ***

  ```
  (1) que `donde_comprar` HAGA ALGO con la zona -- Y `grupos` YA LA TIENE, Y LA API YA LA SIRVE.
      decision escrita: que el precio que se elija sea de la zona del usuario,
      y decir cuando no haya con quien comparar.
      *Y hoy no cambia nada: solo Lidl declara zona, y es una sola.*
  ```

  **NO hay que tocar la guarda del emparejamiento.** *Se quedo como estaba, que es lo correcto.*

  ---

  ### *** EL TRANSPORTE DE LA ZONA: CERRADO Y PUBLICADO (rondas 82-99) ***

  ```
  silver (79 de 79)
    -> projects/cesta/emparejar.py :: COLUMNAS     -- f469015  *** EL SITIO 15, Y EL PRIMERO ***
    -> core/matching.py :: adelgaza                -- 27756cd
    -> groups_de (pasa `regiones`)                 -- 7f0b72d
    -> agrupar_enlaces (acepta `regiones`)         -- 75e625f
    -> core/grupos_ids.py :: tabla_de              -- 0d1a50c
    -> grupos.parquet, la vista `grupos` y LA API  CON region · 63 columnas · LIDL 79 de 79
    -> api/cesta.py :: donde_comprar               la pide SI ESTA -- f952c80
  ```

  *Y comprobado sobre el catalogo entero:* **38961 grupos, y NINGUNO con precios de dos zonas** -- *sin ninguna
  condicion nueva, porque **la invariante de la cadena ya los separa**.* Ver
  `tests/test_b03_la_zona_separa.py` y `docs/investigaciones/B03-relevo-en-una-pagina.md`.

  *Version publicada: `v20261013-155356`.* **Y `precio_diario` conserva `1643898 filas, 38 dias`.**

  *** Y LAS DOS LECCIONES, QUE VALEN MAS QUE EL CAMBIO ***

  *1) **Quince sitios**, cuando el plan decia cuatro funciones -- y **el que faltaba era el PRIMERO de todos**, el
  que LEE el catalogo, porque se hizo el camino **de dentro hacia fuera**.* Lo que lo habria evitado:
  **preguntar «¿por donde ENTRA este dato?» al principio, en vez de «¿donde se usa?».**

  *2) Y **una prueba que PASA puede decir mas que una que falla**: la de la ronda 93 dijo que el trabajo que se
  iba a hacer **no hacia falta** -- y hoy hay 38961 grupos que lo confirman.*

  *Y la leccion de las catorce medidas, que vale mas que el cambio*: **el plan decia cuatro funciones y son siete
  sitios en cuatro ficheros; y el que impone la regla -- `ocupados` -- no estaba en ninguno de los tres planes
  (ni `donde_comprar`, ni la guarda, ni `_asignacion_1a1`).** *Cada uno de esos planes habria producido **un
  cambio correcto, probado, y sin efecto**.* **Y la prueba que mas enseno fue UNA QUE PASO.**

  *La decisión de identidad **está tomada**: la zona entra en el grupo — y por qué, en
  `docs/investigaciones/B03-la-decision-de-identidad-tomada.md` y en `...correccion-la-zona-entra-en-el-grupo-no-en-la-clave.md`.*
  **Un cambio de `SCRAP_CP` reagrupa, no renueva identidades de producto**, y eso se ve en la cobertura del día,
  que ya lleva `region`.

### B04 · 13/10/2026 · commits `e2c3597` … `3ffa9a7`

- **Cambio o hallazgo nuevo**: **el defecto del dueño, reproducido y corregido en los DOS puentes.**
  `_del_plan` no escalaba por comensales y **descartaba la segunda receta**; `recetas.a_la_lista`
  escribía `round(ln.cantidad) or 1` (300 g → 300 unidades) y `None` de nota. **Los dos puentes quedaron
  unificados en `previa_compra.previa_de_compra`**, el id de línea pasó a ser determinista (`uuid5`) y la
  nota dice las recetas, la cantidad, los envases y el sobrante. Además: `grupo_id` y `recetas` se
  añadieron a `LineaDeCompra` (se nombraban y no se leían), la **despensa** se dice y sólo se descuenta
  si la persona lo elige, y `en_tienda` dejó de vetar Lidl.
- **Pruebas ejecutadas**: **13 pruebas de B04**, con **mutación controlada**: las tres mutaciones hacen
  fallar la prueba (`SystemExit`/assert) → **protegidas**. **Aceptación 27 de 27 contra la API real**
  (cinco recetas, dos listas, dos marcas, otra semana, versiones y reintentos). `ruff` limpio · suite
  **2012 pasan, 0 fallan**.
- **Evidencia**: `tests/test_b04_los_dos_puentes.py` · `tests/test_b04_contrato_de_del_plan.py` ·
  `data/debug/b04_mutaciones.py` · `data/debug/b04_aceptacion.py`.
- **Pendiente o límite exacto**: nada del criterio de B04. *La admisión **por línea** de Lidl (con precio
  observado) sigue pendiente, pero eso es de B03.*
- **Siguiente comando**: `uv run pytest tests/test_b04_los_dos_puentes.py tests/test_b04_contrato_de_del_plan.py -q`

## Plantilla de actualización corta

- Paquete / commit / fecha de evidencia:
- Cambio o hallazgo nuevo:
- Pruebas ejecutadas y resultado:
- Evidencia (ruta/version/hash/recibo):
- Pendiente o límite exacto:
- Siguiente comando o acción:

Mantener una entrada por paquete; no copiar conversaciones completas ni actualizar
repetidamente «sigue Running» sin nueva información accionable.
