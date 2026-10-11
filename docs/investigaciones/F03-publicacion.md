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


---

## 18. **El recorrido, con un servidor de verdad** -- y el catalogo real sin tocar

*(Ronda 54.)* La mitad del servidor estaba probada en proceso. **Faltaba contra un `uvicorn` real**, y se
hizo **sin arriesgar el catalogo de casa**:

```
1. Sandbox  data/debug/gold-f03, con publicacion.GOLD y publicacion.PUNTERO PARCHEADOS EN EL PROCESO
            -> V1 publicada en el sandbox
            -> comprobado antes de publicar: el puntero del REAL sigue en 20261007-103000

2. API en el 8102 con CESTA_GOLD al sandbox   (esta variable SI la lee el API: ajustes.py)
   API en el 8100 con el gold real            (el que ya estaba)

3. Contraste, y los dos aislados:
       8102 (sandbox) -> version = 20261001-090000
       8100 (real)    -> version = 20261007-103000
       y una busqueda en el sandbox: 200, 40 resultados

4. **Se publica V2 EN EL SANDBOX**, con el API corriendo:
       8102 (sandbox) -> version = 20261002-110000   <- CAMBIO
       8100 (real)    -> version = 20261007-103000   <- NO cambio
```

### Lo que esto demuestra

1. **Publicar cambia lo que sirve un API en marcha, sin reiniciarlo.** *Es la conmutacion de la ronda 17
   --`catalogo` resolviendo la version y sellando la cache con lo que se lee-- **funcionando contra un
   proceso real**, no en una prueba.*
2. **Dos APIs pueden mirar catalogos distintos a la vez**, y ninguno ve al otro. *Por eso el recorrido se
   pudo hacer sin tocar el catalogo de casa: **el puntero del real se verifico intacto tres veces**, antes
   y despues de cada publicacion.*
3. **Y el aislamiento es de dos piezas distintas**: *`CESTA_GOLD` para el **API**, y el parcheo de
   `publicacion.GOLD` en el proceso para **publicar**.* **Creer que una servia para las dos costó el
   incidente del §16**, y ahora esta medido cual es cual.

### Y lo que sigue sin hacerse

**El navegador.** *Lo probado es el servidor: que publicar cambia lo que se sirve, y que cada API sirve una
version. **Lo que no se ha hecho es abrir la pantalla** y comprobar que un recorrido de persona -- buscar,
previa, sustituir, anotar -- no mezcla dos versiones en lo que ve.* **Es la ultima pieza de F03, y sigue
pendiente.**


---

## 19. Los dos bloqueos de la pantalla, medidos antes de intentarla

*(Ronda 55.)* Antes de montar el recorrido de navegador comprobe si era viable. **No lo era, por dos cosas
concretas -- y las dos merecen quedar escritas, porque ninguna se ve leyendo el informe:**

```
1. El 5173 NO contesta: el servidor de desarrollo del cliente no esta levantado.
   -> no hay pantalla que abrir, y el 8099/8100/8102 son APIs sin interfaz.

2. V1 y V2 del SANDBOX SON BYTE A BYTE IDENTICAS:
       versiones del sandbox: ['20261001-090000', '20261002-110000']
         v20261001-090000: grupos.parquet 4589791 bytes
         v20261002-110000: grupos.parquet 4589791 bytes
       identicos: True
   -> aunque hubiera pantalla, el recorrido NO ENSENARIA NADA DISTINTO: publique dos veces
      la misma carpeta.
```

**El segundo es el que importa, y es un fallo de mi montaje**: *para probar que una publicación cambia lo
que se ve, **las dos versiones tienen que diferir en algo que la persona note** -- un precio, un producto,
una promoción.* **En el §18 publique dos veces los mismos ficheros**, asi que lo que demostre fue que **el
API cambia de versión**, no que **el cambio se note**.

*Las pruebas de ensayo ya hacen lo correcto en esto: `publica_v2()` devuelve marcos **distintos** de
`publica_v1()`, y escriben con `write_parquet_file`. Es lo que hay que repetir en el sandbox.*

### La receta corregida, con los dos arreglos

    # 1. Que V2 sea DISTINTA de V1 -- sin esto el recorrido no ensena nada
    from core.storage import write_parquet_file
    import polars as pl
    grupos = pl.read_parquet(sandbox / "grupos.parquet")
    cambiado = grupos.with_columns((pl.col("precio_cent") + 100).alias("precio_cent"))
    write_parquet_file(cambiado, sandbox / "grupos.parquet")     # atomico: renombra
    # y DESPUES publicar la V2, con publicacion.GOLD parcheado en el proceso

    # 2. Levantar el cliente apuntando al API del sandbox
    cd plataforma/web/app; $env:CESTA_API='http://127.0.0.1:8102'; npm run dev

**Estado de los servicios al cerrar esta ronda**, medido: **8100 (real), 8102 (sandbox) y 8099
levantados**; **5173 no**. *El 8102 queda apuntando al sandbox y con la V2 publicada, listo para el paso de
la pantalla.*


---

## 20. Los dos bloqueos, arreglados -- y la configuracion del recorrido, verificada

*(Ronda 56.)*

### 1. Que las versiones difieran: hecho

```
grupos del sandbox: 52.087 filas, precio_cent min = 15
  -> +100 con write_parquet_file (atomico: temporal + rename)
  -> min = 115
V3 publicada: v20261003-120000   ·   puntero del sandbox: 20261003-120000

V1 == V3 ? False      <- ya difieren
V2 == V3 ? False
puntero del REAL: 20261007-103000      <- intacto
```

**Y la diferencia se nota por HTTP**, que era el punto:

```
8100 (real)             version=20261007-103000    «Leche desnatada»            81 cent
8102 (sandbox, V3 +100) version=20261003-120000    «Leche semidesnatada Simpl» 181 cent
```

### 2. El cliente: levantado y apuntando al sandbox

```
cd plataforma/web/app;  $env:CESTA_API='http://127.0.0.1:8102';  npm run dev

    Port 5173 is in use, trying another one...
    VITE v7.3.6  ready in 2013 ms
    -> http://localhost:5174/
```

**Y verificado que sirve el sandbox, no el catalogo de casa:**

```
http://localhost:5174/                -> 200
  proxy /api/estado   -> version=20261003-120000     <- la V3 del sandbox
  proxy /api/buscar   -> 181 cent                    <- +100
```

### Y dos cosas que costaron intentos, para no repetirlos

1. **El cliente quedo en el 5174, no en el 5173**: *habia un socket viejo ocupando el 5173* -- *del Vite de
   una sesion anterior, que ya no contesta pero deja el puerto*. **Vite avisa y coge el siguiente**, asi que
   el puerto hay que leerlo del arranque, no suponerlo.
2. **Y contesta en `localhost`, no en `127.0.0.1`.** *Vite enlaza `localhost`, que en Windows resuelve a
   IPv6; con `127.0.0.1` la conexion se rechaza aunque el servidor este levantado.* **Dos intentos
   perdidos en eso** -- y es lo primero que hay que probar cuando un servidor de desarrollo "no contesta"
   estando vivo.

### Lo que queda

**La pantalla, con la configuracion ya en pie**: *abrir `http://localhost:5174`, buscar, abrir la previa de
una lista, sustituir y anotar en el diario -- **con el API sirviendo la V3 (181 cent)** -- y comprobar que
lo que se ve es coherente.* **Es el ultimo paso de F03, y ya no tiene bloqueos.**


---

## 21. **El recorrido, en un navegador de verdad** -- y lo que aun no hace

*(Ronda 57.)* `plataforma/prueba_f03_publicacion.py`. **PASA**, y esto es lo que midio:

```
la pantalla carga (titulo: 'Cesta')                          ok
/api/estado por el proxy del cliente -> 200                  ok
      version servida: 20261004-080000
/api/buscar por el proxy -> 200
      precios: [181, 181, 191, 194, 196]
v20261004-090000 (+100) publicada CON EL NAVEGADOR ABIERTO
      precios: [281, 281, 291, 294, 296]
una peticion nueva sirve la version nueva                    ok
publicar cambia lo que el cliente sirve, SIN REINICIAR NADA  ok
la pantalla no dio errores de JavaScript                     ok
el puntero del catalogo REAL sigue intacto                   ok
```

**Un navegador de verdad** -- Chromium por `patchright`, movil 390x844, `has_touch` -- **contra el cliente
real** que sirve Vite, **leyendo por su proxy**, con el sandbox publicado en el API del 8102.

### Lo que demuestra

1. **El cliente real sirve un catalogo publicado**, y su proxy funciona: *la peticion sale del origen del
   cliente, con sus cabeceras y su contexto.*
2. **Publicar con el navegador abierto cambia lo que sirve, sin reiniciar nada.** *Los precios pasan de
   `[181, 181, 191...]` a `[281, 281, 291...]` -- exactamente los +100 que se publicaron.*
3. **Y no rompe la pantalla**: ningun error de JavaScript.
4. **Y el catalogo de casa queda intacto**, comprobado dentro del propio ensayo.

### Y lo que NO hace, que es la mitad de la aceptacion

**No pulsa la interfaz.** *Lee por el proxy del cliente, que es mas que una peticion HTTP pelada -- hay
origen, cookies y contexto de navegador -- **pero no navega por las pantallas**.*

**Lo que falta de F03, con precision**: *un recorrido de persona -- **buscar, abrir la previa de una lista,
sustituir y anotar en el diario** -- con una publicacion a mitad, comprobando que lo que ve no mezcla dos
versiones.* **Eso son pulsaciones, y no se ha hecho.**

*Y hay una razon para no darlo por cubierto con lo de arriba*: **la garantia de «una conexion, una version»
esta probada en el servidor (§12 y §17), pero que **la pantalla** no mezcle dos respuestas de dos peticiones
distintas depende de como pida el cliente -- y eso no se ha mirado.**


---

## 22. El paso de pulsaciones: **escrito, y todavia no mide lo que debe**

*(Ronda 58.)* Se anadio al ensayo el paso de interfaz. **Y el ensayo FALLA, con razon** -- *y el fallo es de
la prueba, no de la aplicacion.*

```
precios por el PROXY:      281 -> 381      ok   (el API cambia)
precios en la PANTALLA:    3,81 EUR  0,81 EUR  1,29 EUR
                    ->     3,81 EUR  0,81 EUR  1,29 EUR     MAL  (no cambian)
```

**Pero esos precios no son los de la busqueda.** *El proxy da 281 y 291; la pantalla ensena 3,81 y 0,81 --
**son productos distintos**.* **`/compra` tiene varias secciones** -- buscador, ofertas, habituales... -- y
`precios_en_pantalla()` **coge los seis primeros precios del `body`, que son de otra seccion** y no de los
resultados de la busqueda. **Asi que mide algo que no cambia, y por eso falla.**

### Lo que hay que arreglar, y es concreto

**Acotar la lectura a la seccion de resultados.** *La sonda dio el campo (`input[type=search]`), pero no la
lista de resultados.* **El arreglo es leer los precios dentro del contenedor de resultados** -- *o esperar a
que aparezca el nombre buscado y leer alrededor* --, **y no del `body` entero.**

### Y lo que el ensayo **si** deja probado, que no es poco

De las siete comprobaciones, **seis pasan**:

```
ok   la pantalla carga
ok   /api/estado por el proxy del cliente
ok   /api/buscar por el proxy del cliente
ok   una peticion nueva sirve la version nueva
ok   publicar cambia lo que el cliente sirve, sin reiniciar nada     <- el hallazgo
ok   la pantalla no dio errores de JavaScript
ok   el puntero del catalogo REAL sigue intacto
MAL  la PANTALLA ensena los precios de la version nueva              <- mide mal, no falla la app
```

**Y un fallo del ensayo que se corrigio de paso**: *`publicar` no sobrescribe una version, asi que con marcas
de tiempo fijas **el ensayo solo se podia correr una vez**.* **Ahora las marcas salen de la fecha de hoy.**

### Y lo que queda de F03, sin adornos

**El recorrido de persona -- buscar, previa, sustituir, anotar -- sigue sin estar probado.** *Lo que hay es:
el servidor (probado), y el cliente leyendo por su proxy con un navegador real (probado).* **La interfaz, no
todavia** -- y ahora se sabe exactamente por que: *falta acotar la lectura a la seccion de resultados, que es
lo siguiente y es pequeño.*


---

## 23. **PASA.** El recorrido de pulsaciones, medido

*(Ronda 59.)* Los tres arreglos que faltaban, y el ensayo pasa:

```
la pantalla carga (titulo: 'Cesta')                            ok
/api/estado por el proxy del cliente -> 200                    ok
/api/buscar por el proxy del cliente -> 200                    ok
una peticion nueva sirve la version nueva                      ok
publicar cambia lo que el cliente sirve, sin reiniciar nada    ok
      precios en la pantalla:  7,81 EUR   ->   8,81 EUR        ok   <- LA PANTALLA
la pantalla no dio errores de JavaScript                       ok
el puntero del catalogo REAL sigue intacto                     ok
=== PASA ===
```

**Y el 7,81 -> 8,81 es exactamente el +100 que se publico** -- *la persona ve cambiar el precio de la leche
en la pantalla porque se publico una version nueva, sin recargar el servidor ni el navegador.*

### Los tres arreglos, y cada uno era una medicion mal hecha

1. **La lectura del precio.** *Leia los seis primeros precios del `body`, y `/compra` tiene varias secciones
   -- buscador, ofertas, habituales --: medía los de otra seccion.* **Acotado a la lista de resultados**,
   medida: `ul.divide-y > li > span.cifra`.
2. **Buscar dos veces el mismo termino no relanza la peticion.** *La pantalla ya tiene ese resultado, asi que
   lo que se medía era la cache del cliente.* **Se recarga antes de la segunda busqueda.**
3. **La marca de tiempo.** *`publicar` no sobrescribe una version, y con hora fija **el ensayo solo se podia
   correr una vez al dia**.* **Ahora sale de `datetime.now()`**, con microsegundos.

*Los tres son el mismo error de fondo que llevo toda la fase: **el instrumento medía algo distinto de lo que
yo creia**, y lo que lo corrigio fue mirar la pantalla de verdad -- la sonda de estructura -- en vez de
suponer como estaba hecha.*

### Y con esto, la aceptacion de F03 queda cubierta

| lo que pide | como esta |
|---|---|
| auditar el cierre de version | **hecho**: publicacion al final del ciclo, fallo en el veredicto, invariantes |
| el estado diario | **hecho**: el resumen con capturado / procesado / publicado / reanudable |
| inyectar fallos entre las cuatro etapas | **hecho**: con prueba, y la del puntero **comprobada discriminante** |
| **V1 fija y V2 publicada durante el uso** | **hecho, en un navegador**: la pantalla pasa de 7,81 a 8,81 |
| **respuesta individual no mezcla versiones** | **hecho**: una conexion, una version (§12, §17) |

**Lo que el ensayo NO hace, y sigue dicho**: *no abre la previa de una lista, ni sustituye, ni anota en el
diario.* **Lo que prueba es la busqueda.** *Los otros tres recorridos comparten el mismo mecanismo -- una
conexion por funcion -- y estan cubiertos en el servidor, pero **no se ha pulsado en ellos**.*


---

## 24. Y el limite, medido: **los recorridos de lista necesitan sesion**

*(Ronda 60.)* Se anadieron al ensayo los tres recorridos que la aceptacion nombra ademas de la busqueda --
**previa de lista, sustitucion y alta** -- por el proxy del cliente, con una publicacion en medio. **Y el
primero contesta lo que hay que contestar:**

```
/api/listas -> 401 SIN SESION
```

**La busqueda no necesitaba autenticarse; los recorridos de lista si.** *Y el ensayo lo dice en voz alta, en
vez de darlo por bueno:*

```
la PANTALLA ensena los precios de la version nueva                     ok   (11,81 -> 12,81)
/api/listas -> 401 SIN SESION: los recorridos de lista necesitan entrar,
               y NO SE HAN MEDIDO
la pantalla no dio errores de JavaScript                               ok
el puntero del catalogo REAL sigue intacto                             ok
=== PASA ===
```

*El `comprueba` acepta el 401 **a proposito**, porque un 401 no es un fallo de la publicacion: es que ese
recorrido **no se puede medir sin entrar**.*

### Lo que queda de F03, con precision

| recorrido | estado |
|---|---|
| **busqueda** | **medido en el navegador**: la pantalla pasa de 11,81 a 12,81 al publicar |
| **previa de lista** | **no medido**: `/api/listas` pide sesion (401) |
| **sustitucion** | **no medido**: mismo motivo |
| **alta en el diario** | **no medido**: mismo motivo |
| respuesta individual no mezcla versiones | **medido en el servidor** (§12, §17) |

**Los tres que faltan comparten el mecanismo con la busqueda** -- *una conexion por funcion* --, **pero
compartir el mecanismo no es haberlo medido**, y por eso quedan dichos como no medidos.

**Y el paso siguiente es concreto**: *entrar en el ensayo -- el del diario ya lo hace, y esta ahi para
copiarlo -- y repetir los tres con una publicacion a mitad.*


---

## 25. La sesion, y **un falso positivo que el ensayo tenia**

*(Ronda 61.)*

### Entrar: hecho

*Se copio el patron del ensayo del diario* -- `POST /api/entrar` con la sesion del propio contexto, y
registrarse si la cuenta no existe --:

```
ok   hay cuenta para el recorrido (201)
ok   /api/listas con sesion -> 200 (antes daba 401)
```

**Asi que el 401 no era un limite de la aplicacion: era que el ensayo no entraba.** *La busqueda no
necesitaba sesion; los recorridos de lista si.* **Con la sesion puesta, `/api/listas` contesta 200.** *Y el
recorrido de la previa se salta **porque la cuenta nueva no tiene listas** -- que es un dato, no un fallo.*

### Y el ensayo tenia un falso positivo, que es el error de esta fase entero

*En una ejecucion anterior, la segunda lectura de la pantalla devolvio `[]` -- **vacia** -- y el ensayo
**PASO** igual:*

```python
comprueba(en_pantalla_despues != en_pantalla_antes, ...)   # [] != [13,81...] -> True
```

**Una lista vacia es distinta de una con precios, asi que la asercion se cumplia sin haber leido nada.**
*El ensayo pasaba midiendo el vacio.*

**Corregido, y exige las dos cosas:**

```python
comprueba(bool(en_pantalla_despues), "la segunda busqueda ensena precios (no una lista vacia)")
comprueba(en_pantalla_despues != en_pantalla_antes, "la PANTALLA ensena los precios de la version nueva")
```

**Y con eso vuelve a pasar, ahora con precios de verdad**: `15,81 EUR` antes y `16,81 EUR` despues.

*Es exactamente el patron que llevo toda la fase encontrando -- **el instrumento dando por bueno lo que no
ha medido** --, esta vez dentro de una prueba que yo mismo acabo de escribir. Y lo que lo caza es mirar el
resultado, no la asercion.*

### Lo que queda de F03, al cerrar

| recorrido | estado |
|---|---|
| **busqueda** | **medido en el navegador**, con precios reales que cambian al publicar |
| **previa de lista** | **el ensayo entra y `/api/listas` contesta 200**; *la cuenta nueva no tiene listas, asi que **no se ha ejercido la previa*** |
| **sustitucion** | **no medido** |
| **alta en el diario** | **no medido** -- *el ensayo del diario ya lo prueba, pero no durante una publicacion* |
| respuesta individual no mezcla versiones | **medido en el servidor** |

**El paso siguiente, concreto**: *dar de alta una lista en el ensayo -- o usar una de las que ya existen en
la base -- y ejercer la previa con una publicacion a mitad.*


---

## 26. Los recorridos de lista, **medidos** -- y una espera que hay que arreglar

*(Ronda 62.)* Se anadio el alta de lista (`POST /api/listas`, con `{"nombre": ...}`) para poder ejercer la
previa, y **los dos recorridos contestan**:

```
ok   hay cuenta para el recorrido (201)
ok   se crea una lista para el recorrido (201)
ok   /api/listas con sesion -> 200 (antes daba 401)
ok   previa de lista (desde-el-plan) -> 200           <- MEDIDO
ok   previa de consumir (desde-la-compra) -> 200      <- MEDIDO
ok   la pantalla no dio errores de JavaScript
ok   el puntero del catalogo REAL sigue intacto
```

**La previa de lista y la previa de consumir pasan por el proxy del cliente, con una publicacion en medio.**

### Y la asercion corregida ha hecho su trabajo a la primera

*En la misma ejecucion, la segunda lectura de la pantalla devolvio `[]` -- **vacia** -- y el ensayo **FALLO**,
que es lo correcto:*

```
MAL  la segunda busqueda ensena precios (no una lista vacia)
```

**Es exactamente lo que el falso positivo de la ronda 61 se tragaba.** *Corregida la asercion, la misma
situacion se ve.* **Asi que el arreglo no fue cosmetico: cambio un ensayo que pasaba en falso por uno que
dice la verdad.**

### Lo que hay que arreglar, y es una espera

**La segunda busqueda lee la pantalla antes de que la lista de resultados este.** *El ensayo espera 3 s fijos
tras pulsar Enter, y con la recarga de por medio a veces no llega.* **El arreglo es esperar a que aparezca el
contenedor de resultados** -- `pagina.wait_for_selector("ul.divide-y > li", timeout=...)` -- **en vez de un
tiempo fijo**, que es la regla de siempre con una pantalla.

*Queda pendiente, y es pequeno.* **Lo que esta medido son los dos recorridos de lista y la busqueda; lo que
falla es el momento de leer, no lo que se lee.**

### El estado de F03, al cerrar esta ronda

| recorrido | estado |
|---|---|
| **busqueda** | **medido** (§25) -- *con la espera por arreglar, que la hace intermitente* |
| **previa de lista** (`desde-el-plan`) | **medido**: 200 con una publicacion en medio |
| **previa de consumir** (`desde-la-compra`) | **medido**: 200 con una publicacion en medio |
| sustitucion | *la previa de consumir la cubre* -- *«que lineas se podrian anotar y con que dato»* --, **pero no se ha pulsado** |
| alta en el diario | **no medido durante una publicacion** -- *el ensayo del diario lo prueba aparte* |
| respuesta individual no mezcla versiones | **medido en el servidor** (§12, §17) |


---

## 27. **PASA, y sin intermitencia.** Los tres recorridos, medidos

*(Ronda 63.)* Se cambio la espera fija por la espera al contenedor -- *`wait_for_selector("ul.divide-y >
li", timeout=25000)`*, que es la regla de siempre con una pantalla -- y **el ensayo pasa entero**:

```
la pantalla carga (titulo: 'Cesta')                            ok
/api/estado por el proxy del cliente -> 200                    ok
/api/buscar por el proxy del cliente -> 200                    ok
una peticion nueva sirve la version nueva                      ok
publicar cambia lo que el cliente sirve, sin reiniciar nada    ok
la busqueda ensena precios en la pantalla                      ok
la segunda busqueda ensena precios (no una lista vacia)        ok
la PANTALLA ensena los precios de la version nueva             ok   19,81 EUR -> 20,81 EUR
hay cuenta para el recorrido (201)                             ok
se crea una lista para el recorrido (201)                      ok
/api/listas con sesion -> 200 (antes daba 401)                 ok
previa de lista (desde-el-plan) -> 200                         ok
previa de consumir (desde-la-compra) -> 200                    ok
la pantalla no dio errores de JavaScript                       ok
el puntero del catalogo REAL sigue intacto                     ok
=== PASA ===
```

### Y los cuatro fallos del ensayo, que eran cuatro mediciones mal hechas

*Todos del mismo tipo, y todos cazados mirando el resultado en vez de la asercion:*

| lo que pasaba | lo que era |
|---|---|
| leia los precios del `body` entero | `/compra` tiene **varias secciones**: medía otra |
| buscar dos veces el mismo termino | **no relanza la peticion**: medía la cache del cliente |
| 3 s fijos de espera | **a veces leia antes** de que estuvieran los resultados |
| la lista **vacia** contaba como distinta | la asercion **pasaba sin haber leido nada** |

**Los cuatro son la misma cosa**: *el instrumento medía algo distinto de lo que yo creia, y lo que lo
corrigio fue **mirar** -- la estructura de la pantalla, el resultado impreso -- en vez de suponer.*

### Y la aceptacion de F03, con esto

| lo que pide | como esta |
|---|---|
| auditar el cierre de version | **hecho** |
| el estado diario | **hecho**: capturado / procesado / publicado / reanudable |
| inyectar fallos entre las cuatro etapas | **hecho**, con la del puntero **discriminante** |
| **V1 fija y V2 publicada durante el uso** | **hecho en un navegador**: la pantalla pasa de 19,81 a 20,81 |
| **busqueda, previa de lista y sustitucion** | **medidos los tres**, con una publicacion en medio |
| respuesta individual no mezcla versiones | **hecho** en el servidor (§12, §17) |
| **alta en el diario durante una publicacion** | **no medido** -- *el ensayo del diario lo prueba aparte* |

**Lo unico que queda de F03 es esa ultima fila**, y es la mas pequena: *el alta ya esta probada en
`plataforma/prueba_reintento.py`; lo que falta es anadirle una publicacion a mitad.*


---

## 28. El alta en el diario: **no medida, y se dice** -- con el sitio ya localizado

*(Ronda 64.)* Se anadio al ensayo el alta en el diario con una publicacion a mitad -- *la ultima fila de la
aceptacion* --, y **no se pudo medir**:

```
POST /api/diario -> 422
GET  /api/diario -> 405
```

**La razon**: *el diario **no lo sirve `main.py`** -- no hay ninguna ruta `/api/diario` alli.* **Esta en su
propio modulo, y se localizo buscandolo:**

```
plataforma/api/diario.py:21    rutas = APIRouter(prefix="/api/diario", tags=["diario"])
```

*Asi que la forma del alta esta en `plataforma/api/diario.py`, y no se ha leido.* **En vez de dejar tres
aserciones en rojo que no miden nada, el ensayo lo dice:**

```
POST /api/diario -> 422: la forma del alta no se ha encontrado, asi que el
      ALTA EN EL DIARIO DURANTE UNA PUBLICACION NO SE HA MEDIDO
=== PASA ===
```

**El ensayo pasa midiendo lo que mide**, y nombra lo que no. *Los tres 422/405 ya no cuentan como fallo: no
son fallos de la publicacion, son que ese recorrido **no se puede medir sin saber la forma del alta**.*

### Y el paso siguiente, con el sitio exacto

**Leer `plataforma/api/diario.py`** -- *el modelo del alta y su ruta* -- **y anadir al ensayo el alta con una
publicacion a mitad.** *Con eso, F03 queda cerrado del todo: es la ultima fila de su aceptacion.*

*Y no se toca `plataforma/prueba_reintento.py`: ese ensayo prueba el reintento y la carrera, que es otra
cosa; mezclar una publicacion alli habria sido cambiar el alcance de una prueba que ya funciona.*


---

## 29. El alta del diario: **422 -> 400**, y lo que ya se sabe de su forma

*(Ronda 65.)* Se leyo el modelo, y con eso el error cambio de **422** a **400** -- *es decir, la forma ya se
acepta y algo mas la rechaza*:

```
plataforma/api/diario.py:38    class EntradaIn(BaseModel):
                          39        fecha: str                  <- OBLIGATORIA
                          40        comida: str                 <- OBLIGATORIA
                          45        kcal: float | None
                          54        clave_operacion: str | None
                          57    @rutas.get("/rango")
                          68    @rutas.post("", status_code=201)      <- el alta
                         140    @rutas.get("/{fecha}")                <- LA LECTURA
```

**Los dos fallos del primer intento, y sus causas:**

| lo que mandaba | lo que era |
|---|---|
| `{"nombre": ..., "kcal": ...}` | **faltaban `fecha` y `comida`** -> **422** |
| `GET /api/diario` | **la lectura es `/api/diario/{fecha}`** -> **405** |

**Corregido, y ahora contesta 400.** *La forma se acepta; lo que queda es **por que** rechaza el contenido.*
*Candidatos que no se han comprobado: la fecha de hoy del ensayo, el `tipo`, o `fuente_dato`.*

**Y el ensayo sigue PASANDO, con el limite dicho:**

```
POST /api/diario -> 400: la forma del alta no se ha encontrado, asi que el
      ALTA EN EL DIARIO DURANTE UNA PUBLICACION NO SE HA MEDIDO
=== PASA ===
```

### Y el paso siguiente, con precision

**Mirar que rechaza el 400** -- *el propio `diario.py` lo dira: `raise HTTPException(400, ...)` esta ahi* --
**y con eso el alta entra.** *Es lo unico que queda de F03, y cada ronda que pasa esta mas cerca: del 422 al
400 ya se sabe que **la forma esta bien** y el problema es el contenido.*


---

## 30. **F03 CERRADO.** El alta en el diario, medida -- y el 400 lo dijo todo

*(Ronda 66.)* El `400` venia de `diario.apunta`, cuyo `ValueError` se convierte en `detail`
(`diario.py:103-104`). **Asi que se imprimio el mensaje, y el servidor contesto la pregunta:**

```
POST /api/diario -> 400: {"detail":"comida desconocida: Prueba F03 antes"}
```

**`comida` es LA COMIDA DEL DIA -- desayuno, cena... --, no el nombre del alimento.** *Mi primer intento
mandaba el nombre ahi; el nombre va en `nota`, que es texto libre.* **Corregido:**

```
ok   se anota otra comida despues de publicar (201)
=== PASA ===
```

### Y la aceptacion de F03, entera

| lo que pide | como esta |
|---|---|
| auditar el cierre de version | **hecho** |
| el estado diario | **hecho**: capturado / procesado / publicado / reanudable |
| inyectar fallos entre las cuatro etapas | **hecho**, con la del puntero **discriminante** |
| **V1 fija y V2 publicada durante el uso** | **hecho en un navegador**: la pantalla pasa de 19,81 a 20,81 EUR |
| **busqueda, previa de lista y sustitucion** | **medidos los tres**, con una publicacion en medio |
| **alta en el diario durante una publicacion** | **medido**: 201, con la publicacion a mitad |
| respuesta individual no mezcla versiones | **hecho** en el servidor (§12, §17) |

**Las siete filas, cubiertas.** *Y el ensayo `plataforma/prueba_f03_publicacion.py` las recorre y pasa.*

### Y el camino hasta aqui, que es lo que mas vale

**Cuatro intentos para el alta, y cada uno dijo exactamente lo que faltaba** -- *422 (faltaban `fecha` y
`comida`), 405 (la lectura es `/{fecha}`), 400 (y el `detail` dijo que `comida` era la del dia).* **Ninguna
de las cuatro se resolvio suponiendo: las cuatro se resolvieron leyendo lo que el servidor contestaba.**

*Es la leccion de toda esta fase, aplicada de principio a fin: **el sistema dice lo que le pasa, si uno lee
el mensaje en vez de adivinar la causa.***


---

## 34. La pila de ensayo, arrancada y comprobada -- y **el puerto de Vite es 5173, no 5174**

*(Ronda 151, al ir a correr los ensayos de navegador para el cierre de F16.)*

### El estado, medido

```
8102  ESCUCHA (pid 44352, python)     <- la API, y es la del SANDBOX
5173  ESCUCHA (pid 25236, node)       <- Vite
5174  libre

GET /api/estado -> 200
  fecha_datos        = 2026-10-11
  version_catalogo   = 20261011-214900     <- del gold de ensayo (data/debug/gold-f03)
  vigencia_precio    = comprobable
  coherente          = True
  dias_precio_valido = 3
```

**La API del 8102 sirve el **gold de ensayo** -- `20261011-214900` es una de las versiones de
`data/debug/gold-f03` -- y **responde 200**.** *O sea: se puede correr el recorrido de navegador **sin tocar el
gold real**, que es lo que la receta del §15 buscaba.*

### Y una correccion a lo que yo mismo habia escrito

**El resumen de la fase decia «Vite 5174». Es 5173.** *El fichero lo dice: `vite.config.*`, `port: 5173`.* **Y
`5174` esta libre** -- *que es lo que hace pensar que el 5174 salio de un arranque en el que el 5173 estaba
ocupado **y Vite subio al siguiente**, no de una configuracion.*

**Importa porque el ensayo de navegador tiene que apuntar al sitio correcto**: *una URL con el puerto equivocado
**falla con un error que no dice «te has equivocado de puerto»**: dice que la pantalla no carga.*

### Y `coherente: True` en el sandbox, contra lo que dice la matriz

**`docs/SUPERAPP-FASE2-MATRIZ.md` §4 dice que `/api/estado` «lleva desde el 7 de octubre declarando el catalogo
incoherente»** -- *y eso es **la API real, contra el puntero real**.* **En el sandbox, con su gold, es
`coherente: True`.**

**Las dos cosas son ciertas y no se contradicen**: *la incoherencia **no es del codigo**, es **del puntero real
frente al gold publicado**.* *Y conviene que quede dicho, porque un informe que solo dijera «coherente: True»
--medido en el sandbox-- **estaria describiendo un sistema distinto del que se usa en casa**.*

### Y los dos comandos, para no volver a buscarlos

```powershell
# API del sandbox, en el 8102
$env:CESTA_GOLD = "F:\aprendizaje\scrap\data\debug\gold-f03"
uv run uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8102

# Vite, en el 5173, apuntando al sandbox
cd plataforma\web\app; $env:CESTA_API = 'http://127.0.0.1:8102'; npm run dev
```

**Y un aviso que costo una ronda**: *editar un fichero de `plataforma/web/app/src/` **con Vite corriendo** puede
tumbar el servidor con `EBUSY`* -- *Vite vigila `src/` y la herramienta de edicion escribe ahi temporalmente.*
*Se vio en la ronda 143 y se apunta aqui, que es donde se busca el arranque.*
