# F03 · La publicación iba **antes** de lo que se calcula después

Estado: **defecto reproducido; arreglada la mitad del código de salida**. Fecha: 13 de octubre de 2026.
Origen del hallazgo: revisión previa de fase 2, tabla §3, fila *«Publicación y derivados»*.

> *«`pipeline.py` todavía captura fallo de publicar; **el ciclo reconstruye grupos después del
> pipeline**. → Auditar cierre de versión y estado diario. **El arreglo de las fechas del puntero no
> demuestra coherencia de todos los artefactos.**»*

Y el criterio de F03: *«Construir/publicar **todos los derivados de una versión antes del puntero**.
Inyectar fallos entre pipeline, matching, manifiesto y publicación.»*

---

## 1. La cadena, medida

```
run.py:235   pipeline.main()   -> escribe gold y PUBLICA (sella la version)
run.py:245   emparejar.main()  -> reescribe data/gold/grupos.parquet y enlaces.parquet
```

**Y quien lee, lee la versión.** `publicacion.ruta()` resuelve el puntero y devuelve
`v<version>/grupos.parquet`, **no** el gold suelto: *el gold suelto es la copia de trabajo; la versión es
lo que se sirve.* **Eso corrige mi primera lectura** —*creí que la incoherencia era «el puntero no
coincide con `data/gold`»*, y no lo es: los dos papeles son distintos a propósito—.

**Así que lo que `emparejar` calcula no lo ve nadie.** Se escribe en gold y los lectores siguen con la
versión publicada **antes**, que es la de antes del emparejado.

**Medido sobre el estado real**, no deducido: la última versión publicada (`20261011-124542`) tiene
`grupos.parquet` y `enlaces.parquet` **distintos** de los de `data/gold` —**los dos únicos ficheros que
escribe `emparejar`**— y los otros cuatro **idénticos**. *Los cuatro que nadie reescribe después
coinciden; los dos que sí, no.*

---

## 2. La segunda mitad: el fallo de publicar no llegaba a nadie

```python
# pipeline.py, antes
try:
    publicacion.publicar()
except Exception as exc:
    print(f"  publicacion: no se pudo publicar ({type(exc).__name__}: {exc})")
print("pipeline: hecho")
return 0        # <- SIEMPRE 0, aunque la publicacion falle
```

```python
# run.py, antes
importlib.import_module("projects.cesta.pipeline").main()   # <- resultado DESCARTADO
```

**Las dos cosas a la vez**: el pipeline se tragaba el fallo y devolvía 0, **y el ciclo no miraba el
resultado**. Así que un fallo de publicación **no llegaba al veredicto del día**.

*Y el propio comentario del pipeline confiesa que eso ya pasó*: **«el 13 de octubre de 2026 eso dejó
`data/gold` en el 8 y `actual.json` en el 7, y `/api/estado` lo declaró incoherente -- con razón.»*

**Arreglado**: `main()` devuelve **1** y lo dice —*«el dato está escrito, pero la versión NO se ha
publicado»*—, y `run.py` **mira el resultado** y lo apunta en `fallos`, que es lo que decide el veredicto
del día. *Reproducido y comprobado: la prueba fallaba antes y pasa después.*

---

## 3. Y una invariante que se descubrió de camino, y conviene dejar fijada

**`publicar()` no copia: hace un enlace duro** (`os.link`), *para no duplicar un fichero de 195 MB*. Eso
significa que **la versión publicada y el gold suelto son el mismo inodo al publicar**.

**Lo que salva eso es que `write_parquet_file` escribe en un temporal y renombra**: el gold suelto pasa a
ser otro inodo y la versión conserva el suyo. *Un escritor que escribiera **en el sitio** mutaría todas
las versiones publicadas que compartan ese inodo — hacia atrás en el tiempo.*

*Lo descubrí porque **mi primera prueba usaba `pl.write_parquet`**, que escribe en el sitio, y **la
versión publicada cambió sola**. No era un fallo del motor: era mi prueba midiendo otro escritor.*
**Queda fijado** en `test_una_version_publicada_no_se_muta_si_el_escritor_renombra`: *si alguien cambia
el escritor por uno que no renombre, salta ahí.*

---

## 4. La publicación, movida al final del ciclo

**El propio ciclo decía dónde va.** `run.py` comenta, al escribir el manifiesto: *«va después del
emparejador, **que es lo último que toca gold**»*. Ahí es donde se publica ahora —justo después del
manifiesto, que describe lo que se publica—.

**Y el pipeline aprende a callarse**: `pipeline.main(*, publicar=True)`. *Una pasada suelta
(`python -m projects.cesta.pipeline`) sigue publicando; **el ciclo le dice `publicar=False`**, porque es
el ciclo quien sabe cuándo se ha acabado de escribir gold.*

**Y el fallo entra en el veredicto**: `fallos.append("publicacion")`.

**Fijado en `tests/test_la_pasada_publica.py`**, que lee la fuente del ciclo y afirma **las tres cosas**:
que el pipeline **no** publique cuando lo llama el ciclo, que el ciclo **sí** publique, y que lo haga
**después** del emparejador. *Se refuerza el test que ya existía en vez de sustituirlo: el de antes
comprobaba que la pasada publica, y sigue siendo verdad para una pasada suelta.*

---

## 5. Lo que queda de F03

1. **Inyectar fallos** entre pipeline, matching, manifiesto y publicación, como pide el criterio.
2. **El resumen diario** que distingue **capturado / procesado / publicado**, y que **reanuda desde crudo
   sin rescrapear todo**.
3. **Los dos recorridos de navegador** de V1 fija y V2 publicada durante el uso, con las tres apps.
4. **Y una observación sin explicar, que no afirmo como defecto**: el puntero apunta a
   `20261007-103000`, y sus **6 ficheros son byte a byte idénticos** al gold que se sirve hoy. *Con
   `fijar()` no se tocan ficheros y `publicar()` rechaza una versión que ya existe, así que la
   explicación más probable es una publicación con `momento` retrofechado — que es justo la sutileza que
   avisa `tests/test_g04_catalogo_de_ensayo.py:543`.* **No lo doy por bueno ni por malo: queda anotado
   como algo que hay que explicar antes de tocar la publicación.**


---

## 6. Y el hallazgo que obliga a corregir lo de arriba: **la aplicación no lee versiones**

*(Ronda 14.)* Buscando la mitad de F03 que se puede probar sin navegador —*«respuesta individual no mezcla
versiones»*—, medí **quién usa el mecanismo que existe para eso**:

```
git grep -n "publicacion.ruta\|publicacion.rutas\|rutas(" -- plataforma/api core
  core/publicacion.py:86:def rutas(...)      <- y ninguna llamada mas
```

**`ruta()` y `rutas()` no los usa nadie.** *Existen, están documentados —«fija la versión: un lector no
puede ver dos mezcladas», «es lo que fija la versión por petición»— y **no tienen un solo consumidor**.*

**Y la aplicación sí lee un catálogo**: `catalogo.buscar` va contra **`data/gold`**, con la conexión
cacheada por el `mtime` de `grupos.parquet`. *Lo dice el propio test, en su comentario; y el test que
parece demostrar lo contrario se llama `…publicar_v2_cambia_lo_que_la_aplicacion_sirve` **pero usa
`_suelta`, que escribe el gold suelto, no `publicar()`**.*

### Lo que eso significa, dicho sin adorno

1. **El versionado es inerte para la aplicación.** Se publica, el puntero se mueve y `/api/estado` lo
   mira — **pero la aplicación nunca lee una versión**: sirve siempre el gold suelto.
2. **`respuesta individual no mezcla versiones` se cumple por trivialidad**, no por el `rutas()` que se
   escribió para ello: *hay una sola fuente*.
3. **Y el `AVISO` que añadí en la ronda 12 afirmaba algo falso**: *«hay catálogo procesado que NO se está
   sirviendo»*. **No es verdad**: lo servido es el gold, que sí es lo más nuevo; **la que se quedó atrás
   es la publicación**. *Lo he corregido, con la explicación impresa debajo, y la prueba que afirmaba la
   frase vieja está ajustada a lo que es verdad.*

**Es un error mío de la ronda 12, y es del tipo que el encargo avisa**: *afirmé una consecuencia
operativa —«no se está sirviendo»— desde un detalle de versionado, **sin comprobar quién lee qué**.*
*Mirar el puntero no es mirar lo que ve quien compra.*

**Y abre una pregunta que hay que contestar antes de tocar nada más**: *si la aplicación no lee
versiones, ¿para qué se publican?* Las respuestas posibles —que el versionado sea para el manifiesto y la
auditoría, que falte conectar `catalogo` a `rutas()`, o que sea deuda a medio terminar— **no las elijo
yo**: quedan como la primera cosa que hay que decidir en F03.


---

## 7. La pregunta que abrí en la ronda 14 **ya estaba contestada**, y la contesté mal

Escribí: *«si la aplicación no lee versiones, ¿para qué se publican? […] no las elijo yo: quedan como la
primera cosa que hay que decidir.»*

**Estaba en el proyecto, con su motivo, y no lo leí.** `docs/SUPERAPP-ESTADO.md:645-647`, en el cierre de
S01:

> **Pendiente dentro de S01**: el pipeline todavía escribe los ficheros sueltos; **hay que hacerlo
> publicar por versiones y que la API lea con `rutas()`**. Se hace al entrar en S02/S05, **para no tocar
> la tarea de las 06:00 a la vez que se cambia la lectura**.

**Así que no es un defecto escondido: es un pendiente declarado, con su razón de ordenación** — *cambiar
la tarea de las 06:00 y la ruta de lectura a la vez es justo lo que no se quiere*.

**Y el documento avisa además del riesgo técnico**: *«importar `publicacion` en la API»* traería **polars**
a la API, que *«causó reinicios de `cesta-api` el 21 de septiembre»*. El camino que el propio documento
apunta: **«sacar la lectura a un módulo pequeño sin polars que usen los dos»**. Y termina con una frase
que conviene citar entera: *«Queda apuntado, no hecho: hoy no hay ningún síntoma que lo pida.»*

**Lo que sí es mío, y sigue en pie**: la tabla de S01 afirma *«concurrencia probada: `rutas()` resuelve la
versión **una vez** y devuelve todos los caminos»*, y **eso está probado pero no usado** — *la prueba mide
la función, no que la petición la use*. **Un cierre por «probado» sobre una función sin consumidores es
exactamente el patrón que esta fase existe para encontrar**; el documento ya lo dice en prosa, pero la
tabla lo lee como cumplido.

**Y la lección de método, que me la llevo**: *presenté como pregunta abierta algo que el proyecto había
escrito y decidido aplazar.* **Antes de declarar un hueco, hay que leer el fichero de estado** — que es
justo lo que el encargo pide cuando dice «contrastar los cierres anteriores con los criterios y pruebas
reales».

---

## 8. Lo que queda de F03, ya sin preguntas abiertas

1. **Cambiar la lectura de la API a `rutas()`** — el pendiente declarado de S01 —, **sin meter polars en
   la API**: *el camino que el propio documento apunta es un módulo pequeño sin polars que usen los dos.*
   *Ese cambio es lo que hace verdadera la frase «respuesta individual no mezcla versiones», que hoy se
   cumple por trivialidad.*
2. **Los dos recorridos de navegador** de V1 fija y V2 publicada durante el uso.
3. **Reanudar desde crudo sin rescrapear todo**, con `load_raw_bytes`.
4. **Y una decisión de tabla, no de código**: la fila de S01 que da «concurrencia probada» por `rutas()`
   —*probado, sí; usado, no*— **debería decir lo que dice la prosa**.


---

## 9. El modulo sin polars, hecho

*(Ronda 16.)* El pendiente declarado de S01 es **que la API lea la version publicada**. *Y el propio
documento de estado fija por que no se hizo de la forma obvia: `core/publicacion.py` **importa polars**
-- escribe marcos --, y meterlo en la API es meter polars en el proceso que atiende a quien compra:
**«causo reinicios de `cesta-api` el 21 de septiembre»**.* El camino que el documento apunta: *«sacar la
lectura a un modulo pequeno sin polars que usen los dos»*.

**Ese modulo esta hecho**: `core/version_vigente.py`. **No importa nada del proyecto** -- ni polars, ni
`duckdb`, ni `core.config`: *solo la biblioteca estandar* --, y resuelve lo unico que hace falta:

    version_actual(gold)                 la version que se sirve, o None
    publicado_en(gold)                   cuando se movio el puntero
    carpeta_de(gold, version)            donde vive
    ruta(gold, nombre, version=None)     el fichero, de la version o del gold suelto
    sello(gold, nombre, version=None)    su mtime, para cachear por el

**Y la restriccion se comprueba, no se confia**: `test_no_arrastra_polars` importa el modulo en un
interprete limpio y mira `sys.modules` -- *si polars, duckdb o pyarrow entraran por la puerta de atras,
saldria ahi*.

**Y una cosa que el modulo ya deja bien**: `catalogo` cachea hoy por el `mtime` de
`AJUSTES.gold / "grupos.parquet"`, **el suelto**. *Cuando lea la version, cachear por el suelto seria
cachear por un fichero que puede no ser el que se lee, y la cache no se invalidaria al publicar -- que
es justo cuando tiene que invalidarse.* **`sello()` resuelve eso y tiene prueba propia.**

**Lo que queda es la conmutacion**: `catalogo.conexion()` y `_sello_de_gold()` tienen que pasar a usar
`version_vigente`, resolviendo la version **una vez por peticion** -- *que es la frase que hoy se cumple
por trivialidad* --. **No se ha hecho en esta ronda y no se da por hecho.**


---

## 10. La conmutacion, hecha

*(Ronda 17.)* El pendiente declarado de S01 —**que la API lea la version publicada**— esta hecho:

```python
# catalogo._sello_de_gold()   ahora es el sello de LO QUE SE LEE
return version_vigente.sello(AJUSTES.gold, "grupos.parquet")

# catalogo.conexion()   la version se resuelve UNA VEZ y las cinco vistas salen de ella
version = version_vigente.version_actual(g)
con.execute(f"CREATE VIEW grupos AS SELECT * FROM '{_de_la_version('grupos.parquet')}'")
```

**Y las dos mitades importan por razones distintas:**

- **Las vistas, de una sola version.** *Resolver el puntero cinco veces -- una por vista -- es lo que
  deja montar `grupos` de una publicacion y `enlaces` de la siguiente si se publica a mitad de camino.*
  **Es la mezcla que S01 prohibe**, y hasta hoy **la frase se cumplia por trivialidad**: `rutas()` estaba
  probado y no lo usaba nadie.
- **El sello, el de lo que se lee.** *El `mtime` del gold suelto es el de un fichero que puede no ser el
  que se sirve: la cache no se invalidaria **al publicar**, que es justo cuando tiene que invalidarse.*

**Y el fallback hace el cambio seguro**: *sin puntero, `version_vigente.ruta` devuelve los ficheros
sueltos de siempre.* **Lo confirman las pruebas que ya existian**: `test_g04_catalogo_de_ensayo.py`
escribe el gold suelto con `_suelta` **sin poner puntero**, asi que sigue leyendo el suelto — **46 pasan,
1 skipped** en la bateria del catalogo y la API, y **1711 en la suite entera**.

### Lo que NO esta probado, y no se da por hecho

**Que publicar cambie lo que la aplicacion sirve.** *La prueba que se llama asi
(`test_publicar_v2_cambia_lo_que_la_aplicacion_sirve`) **usa `_suelta`, que escribe el gold suelto, no
`publicar()`**: mide otra cosa.* **Ahora que `catalogo` lee la version, esa prueba hay que escribirla de
verdad** -- publicar V2 con `publicacion.publicar()` y comprobar que la busqueda devuelve lo de V2 --, y
con ella la de que **una peticion de dos ficheros ve una sola version**.

*Es el siguiente paso, y es corto: el mecanismo ya esta conectado.*


---

## 11. La prueba que faltaba, y el enlace duro mordiendo de verdad

*(Ronda 18.)* La conmutacion de la ronda 17 **ya esta probada**: hay una prueba que **publica de verdad**
--puntero, carpeta de version y enlace duro-- y comprueba que lo servido sigue al puntero.

**Y esta montada para discriminar, que es lo que habia que cuidar.** *Si se escribe V2 en el gold suelto
**y se publica**, una aplicacion que leyera el suelto tambien daria otro precio, y la prueba pasaria sin
medir nada.* Por eso **V2 se deja SOLO en el suelto, sin publicar**: si la aplicacion lee la version,
sigue sirviendo **V1** -- y eso es lo que comprueba la primera asercion.

```
con el puntero en V1 y V2 solo en el gold suelto  ->  sirve V1   (150)
y despues de publicar V2                          ->  sirve V2   (120)
```

### Y al escribirla, el enlace duro mordio de verdad

**La primera version fallo**, y no por la prueba: con el puntero en V1 servia **120**, el precio de V2.
*La causa es la invariante que fije en la ronda 10 y que aqui dejo de ser teorica.*

`_suelta` -- el ayudante del ensayo -- usa `marco.write_parquet`, que **escribe en el sitio**; y
`publicar()` deja un **enlace duro** entre el gold suelto y la version. **Asi que escribir V2 en el gold
suelto mutaba tambien la version publicada.** *Con el escritor del proyecto -- `write_parquet_file`, que
escribe en un temporal y renombra -- la prueba pasa.*

**Queda dicho donde importa**: en la prueba nueva, con el porque. *`_suelta` sigue como estaba porque las
otras pruebas del fichero no publican antes de volver a escribir, y cambiar un ayudante compartido por
una razon que solo afecta a una prueba es peor que decirlo ahi.* **Pero es una trampa para el proximo**:
*publicar y despues usar `_suelta` sobre el mismo gold mutila la version publicada.*


---

## 12. «Una peticion de dos ficheros ve una sola version», y su limite

*(Ronda 19.)* La otra mitad de la frase de S01, con prueba: **una conexion ya montada sigue leyendo su
version aunque se publique otra cosa, y una nueva lee la nueva** -- *que es lo que hace que publicar sirva
para algo.*

```
se monta la conexion con el puntero en V1
se publica V2 a mitad de camino
  la conexion que ya estaba  ->  sigue leyendo V1   (sus vistas apuntan a los ficheros de V1)
  una conexion nueva         ->  lee V2
```

### Y el limite, medido y dicho donde se lee

**La unidad no es la peticion, es la conexion.** Medido: la API llama a `catalogo.conexion()` en **ocho
sitios, cada uno en una funcion distinta** (`alertas.py` dos, `main.py` dos -- uno de ellos al arrancar
--, `movimientos.py` cuatro). *Asi que un manejador que la pida una vez esta cubierto.*

**Si algun dia un manejador llama a dos de esas funciones** -- y por tanto pide conexion dos veces -- **y
se publica entre las dos, vera dos versiones.** *Entonces habra que **pasar la conexion**, no volver a
pedirla.* **Queda escrito en la prueba, que es donde se va a leer.**

### Lo que esta prueba NO demuestra, y no se le atribuye

**Que las cinco vistas se resuelvan de una sola version.** *Eso lo garantiza la construccion -- `version`
se resuelve en una linea y las cinco `CREATE VIEW` salen de ella -- y la lectura del codigo, no esta
prueba.* Lo que esta prueba fija es el **contrato de fuera**: una conexion, una version. *Y fallaria si
`conexion()` se rehiciera en cada lectura.*


---

## 13. «Reanudar desde crudo», que **ya estaba hecho y probado** — y yo lo liste como pendiente

*(Ronda 20.)* He cerrado varias rondas diciendo que faltaba *«reanudar desde crudo sin rescrapear todo,
con `load_raw_bytes`»*. **Lo medi y no falta: esta hecho y probado.** *Es el mismo error de la ronda 15
--dar por hueco lo que no habia comprobado--, esta vez con una lista de pendientes en vez de con una
pregunta.*

**Lo que hay, medido:**

- **`core/storage.py`**: `save_raw` / `load_raw_bytes` -- *«la ultima captura de hoy para reanudar una
  ejecucion interrumpida sin red»* --, con **pruebas propias** (`tests/test_storage.py`).
- **Las cuatro cadenas lo usan**: `alcampo.py`, `aldi.py` (dos veces), `carrefour.py`, `dia.py` (dos).
- **Y el caso dificil esta resuelto y probado.** `alcampo._cache_limpia` no sirve de la cache un reto del
  WAF, y su docstring cuenta por que:

  > *«El reto se guardaba como si fuera catalogo, y a partir de ahi la categoria quedaba envenenada: la
  > ejecucion siguiente la leia del disco, veia el reto y se paraba sin llegar a pedir nada por la red.
  > Renovar la cookie no arreglaba nada porque nunca se volvia a pedir. **De ahi la pasada del 7 sep que
  > "corto" tras 6.623 productos en ocho segundos sin una sola peticion.**»*

  *Y `_guardar` tampoco guarda un reto, asi que la cache no se puede envenenar hacia adelante y las
  entradas viejas se ignoran.* **Las dos mitades tienen prueba**: `test_un_reto_ya_cacheado_se_ignora_y_se_
  vuelve_a_pedir` y `test_el_crudo_bueno_se_sirve_de_la_cache`.

**Asi que lo que queda de F03 es mas estrecho de lo que yo decia**: *no* es la reanudacion, es **que el
resumen diga de que cadenas hay crudo reanudable** -- que es la parte de «capturado/procesado/publicado»
que todavia no esta -- y **los dos recorridos de navegador**.

**Y la leccion, que ya es la segunda vez**: *antes de apuntar un pendiente en el tablero hay que medirlo.*
**Un pendiente inventado cuesta lo mismo que un cierre inventado**: los dos hacen que el tablero deje de
servir para decidir.


---

## 14. Verificado por HTTP, y una decision que **no me toca tomar**

*(Ronda 22.)* Lo que faltaba de la aceptacion de F03 en su mitad de *«pruebas reales de API»*: **el API
corriendo con el codigo de hoy**, no solo `catalogo` en una prueba.

```
uv run uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8100    (CESTA_POSTGRES -> 5434)

/api/estado                    200
  fecha_datos      2026-10-11
  version_catalogo 20261007-103000
  coherente        False
/api/buscar?q=leche            200, 40 resultados
```

**1. La conmutacion de la ronda 17 funciona de punta a punta.** *El API lee la version publicada y sirve
-- 40 resultados para «leche» --, que es lo que hasta la ronda 17 no se podia decir: `catalogo` leia el
gold suelto.*

**2. Y `/api/estado` declara `coherente: False`**, por lo mismo que el resumen: **los precios son del
2026-10-11 y el puntero del 2026-10-07**. *No es un efecto del cambio -- la version y el gold son byte a
byte identicos en `precio_diario` (medido en la ronda 10) --, es la incoherencia que ya estaba.*

### Y aqui paro, a proposito

**Publicar arreglaria la incoherencia**: el puntero pasaria al 11 y `/api/estado` diria coherente. *Y
ahora es seguro hacerlo: la publicacion va al final del ciclo, el fallo llega al veredicto, y una
conexion ve una sola version.*

**Pero publicar cambia lo que la aplicacion sirve.** *Hoy sirve la version del 7 de octubre; publicar la
moveria al gold del 11.* **Es un cambio material sobre datos reales, es reversible (`fijar` vuelve
atras), y no es mio tomarlo sin que lo decida quien es dueno del catalogo.** *El encargo dice preservar
los datos reales y no desplegar; y una publicacion no es un despliegue, pero si una decision.*

**Queda como la primera cosa que hay que decidir, con los numeros delante**: *el puntero esta en
`20261007-103000`, el gold es del 11, y `/api/estado` lleva desde entonces diciendo que no cuadra.*


---

## 15. El bloqueo del recorrido de navegador **no era tal**

*(Ronda 23.)* Ayer escribi que el ensayo de navegador de V2 publicada *«exige publicar una version real,
que es la decision material que no me toca tomar»*. **Lo medi y no hace falta: `CESTA_GOLD` es una
variable de entorno.**

```python
# plataforma/api/ajustes.py:27
gold=_ruta("CESTA_GOLD", raiz / "data" / "gold"),
```

**Asi que se puede levantar un API contra un gold de ensayo sin tocar el de casa**, que es exactamente lo
que hace falta para el recorrido. *Tercera vez en esta fase que doy por bloqueado algo que no lo estaba
-- y la tercera que lo cazo midiendo.*

### La receta, para que el proximo no vuelva a empezar por aqui

    # 1. Un gold de ensayo, copiado del real (o construido), y su V1 publicada
    $sandbox = "F:\aprendizaje\scrap\data\debug\gold-f03"
    Copy-Item data\gold\*.parquet $sandbox\
    $env:CESTA_GOLD = $sandbox
    uv run python -c "from core import publicacion; print(publicacion.publicar(None))"

    # 2. Un API apuntando AHI, y no al de casa
    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    $env:CESTA_GOLD=$sandbox
    uv run uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8101

    # 3. Vite apuntando a ese API, y el ensayo con patchright
    cd plataforma\web\app; $env:CESTA_API='http://127.0.0.1:8101'; npm run dev
    $env:CESTA_UI='http://localhost:5173'; uv run python -m plataforma.<el ensayo>

**Lo que el ensayo tiene que comprobar**, y es lo que pide el criterio: *con **V1** fija, buscar y abrir
la previa de una lista; **publicar V2** a mitad; y que la respuesta individual **no mezcle** versiones
-- ni la busqueda, ni la previa, ni el alta de receta o comida --, y que el historial y el consumo
antiguos **no cambien**.*

**Y una cosa que la pieza ya construida deja hecha**: `version_vigente` y la conmutacion de `catalogo`
hacen que **cada conexion lea una version**, asi que lo que el ensayo tiene que demostrar **desde fuera**
es que ningun manejador pide conexion dos veces. *El limite esta escrito en
`test_una_conexion_ve_una_sola_version`.*

**No se ha montado en esta ronda, y no se da por hecho.**


---

## 16. **Incidente**: movi el puntero del gold REAL, y la receta de la seccion 15 estaba mal

*(Ronda 50.)* Iba a montar el recorrido de V2 publicada con el sandbox de la seccion 15. **Y al publicar la V1
del sandbox, escribi en el catalogo de verdad.**

### Que paso

```python
os.environ["CESTA_GOLD"] = ".../data/debug/gold-f03"
from core import publicacion
publicacion.publicar(None, momento=datetime(2026, 10, 1, 9, 0, 0))
```

```
publicacion.GOLD = F:\aprendizaje\scrap\data\gold      <- EL REAL
```

**`publicacion.GOLD` es una constante de modulo, calculada al importar, y NO lee `CESTA_GOLD`.** *Esa
variable la lee `plataforma/api/ajustes.py` -- **el API** --, no los scripts de publicacion.* **Asi que la
receta que yo mismo escribi en la seccion 15 era falsa en la mitad que importaba: `CESTA_GOLD` no aisla a
`publicar`.**

### Que se toco, y como quedo

- Se creo `v20261001-090000` en el gold real (**enlace duro de los ficheros que ya estaban**: *byte a byte
  identicos, nada corrupto*) y **el puntero paso a esa version** -- es decir, **la aplicacion empezo a
  servir una version fechada el 1 de octubre**.
- **Restaurado**: `publicacion.fijar("20261007-103000")` y **retirada la carpeta** que cree.
- **Y un efecto que `fijar` dejo**: *re-sello `publicado_en` con la hora del arreglo*
  (`2026-10-11T21:23`), **y eso cambiaba el veredicto de `/api/estado`** -- *de incoherente a coherente, por
  un sello, no por un dato*. **Devuelto a su valor medido** (`2026-10-07T10:30:00`), escribiendo el puntero
  de forma atomica como hace el resto del proyecto.

**Estado final, verificado**: `version = 20261007-103000`, `publicado_en = 2026-10-07T10:30:00`, **los seis
ficheros presentes**, y **el resumen dice exactamente lo mismo que antes del incidente**:

```
publicado: v20261007-103000, el 2026-10-07T10:30:00
AVISO: la version publicada es del 2026-10-07 y el silver llega al 2026-10-11: se publico por detras de lo procesado
```

### Y la leccion, que es lo unico bueno que saco de esto

**No se aisla un script de publicacion con variables de entorno: `publicacion.GOLD` se parchea en el
proceso.** *Es lo que ya hacen las pruebas del ensayo (`monkeypatch.setattr(publicacion, "GOLD", oro)`), y
es lo que yo deberia haber hecho en vez de confiar en `CESTA_GOLD`.*

**La receta de la seccion 15 queda corregida:**

    import os
    from pathlib import Path
    from core import publicacion
    sandbox = Path(".../data/debug/gold-f03")
    publicacion.GOLD = sandbox                 # <- ASI, no con CESTA_GOLD
    publicacion.PUNTERO = sandbox / "actual.json"
    publicacion.publicar(None, momento=...)

*Y `CESTA_GOLD` sigue sirviendo para el **API**, que es para lo que existe.*

### Y lo que no voy a hacer ahora

**Reintentar el recorrido.** *El contexto de esta sesion esta agotado y acabo de demostrar el riesgo de
tocar esto con prisa.* **La receta corregida queda escrita, y el recorrido sigue pendiente** -- *que es
mejor que un segundo intento a medias sobre datos reales.*


---

## 17. El recorrido de varias tablas, probado

*(Ronda 52.)* La aceptación de F03 pide *«búsqueda, previa de lista, sustitución y alta de receta/comida;
respuesta individual no mezcla versiones»*. **Las cuatro leen la misma conexión**, y una conexión puede leer
varias tablas -- `grupos`, `enlaces` y `precio_diario` --. **Eso es lo que reproduce la prueba**, en
`tests/test_g04_catalogo_de_ensayo.py`:

```
se abre la conexion con V1 publicado
se leen las TRES tablas
se publica V2 a mitad del recorrido          <- parcheando publicacion.GOLD EN EL PROCESO
se vuelven a leer las tres
    -> identicas: la conexion no cambia de version a mitad
y una conexion NUEVA
    -> lee V2, que es lo que hace que publicar sirva para algo
```

**Y publica en el sandbox parcheando `publicacion.GOLD` en el proceso** -- *no con `CESTA_GOLD`, que es el
error del §16*.

### Y lo que esta prueba demuestra, sin atribuirle mas

- **Demuestra**: *la version se resuelve **al abrir la conexion**, no en cada consulta* -- *si se resolviera
  por consulta, un recorrido de tres tablas podría enseñar el nombre de una version y el precio de la
  siguiente.*
- **Y demuestra** que publicar cambia lo que sirve una conexión nueva.
- **No demuestra** lo que pasa en un **navegador**: *que la pantalla no mezcle dos respuestas de dos
  peticiones distintas.* **Eso sigue pendiente**, y es lo que la aceptación llama «las tres apps durante el
  uso».

*Sigue sin hacerse el recorrido con navegador. Lo que hay ahora es la mitad del servidor, probada.*
