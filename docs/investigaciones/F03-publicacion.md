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
