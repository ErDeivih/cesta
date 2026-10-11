# F07 -- Compra rapida, familiar y clara (P1)

**Criterio, de `docs/SUPERAPP-FASE2-EMPEZAR-AQUI.md:121`:**

> Investigar C01-C05 con Bring!/AnyList/Listonic. Mejorar solo lo que falte: lista por pasillos y orden por
> pasillo...
> Dos usuarios concurrentes del mismo hogar **no pisan cantidades ni tachados**; conflictos claros, sin
> empujar[se]...
> **Aceptacion:** tarea movil con una mano, recorrido de cuenta vacia, recarga y **dos sesiones**; medir pasos

*Y el encargo pone esto **despues** de los cierres*, asi que se empieza por lo que se puede comprobar.

---

## 1. Lo que hay que comprobar primero: **la concurrencia**, y ya tiene mecanismo

*Antes de «mejorar solo lo que falte» hay que saber **que falta**, y la parte verificable del criterio es la
concurrencia:* **dos usuarios del mismo hogar no pisan cantidades ni tachados.**

**Y el mecanismo existe**, en `plataforma/api/main.py`:

```
870  @app.post("/api/listas/{lista_id}/sincronizar")
871  def sincronizar(lista_id: str, cambios: list[dict], usuario: dict = Depends(usuario_actual)):
872      """Lo que se hizo sin cobertura, todo de golpe.
874      Cada cambio lleva su hora del movil. Como anadir y tachar son idempotentes,
875      subir dos veces lo mismo no rompe nada: es justo lo que pasa cuando la red
876      va y viene en el pasillo del supermercado.
877      """
```

**Asi que esta disenado para el caso real**: *cambios hechos **sin cobertura** en el pasillo, subidos **de
golpe** al recuperarla, **cada uno con su hora del movil**, y con **anadir y tachar idempotentes** -- *subir
dos veces lo mismo no rompe nada.*

### Y lo que queda por comprobar, con precision

**El endpoint resuelve el caso de UN usuario que pierde la red.** *Lo que el criterio pide ademas es **DOS
usuarios a la vez***, y ahi hay una pregunta abierta y concreta:

> **¿`momento` se usa para resolver conflictos, o solo viaja?**

*El parametro esta ahi (`c.get("momento")`, linea 888) y se pasa a `almacen.cambia_linea`. **Si `cambia_linea`
lo usa para decidir quien gana, la afirmacion del criterio es cierta; si lo ignora y escribe el ultimo que
llega, entonces dos usuarios si se pisan** -- *y la ultima linea escrita gana por orden de llegada, no por hora
del movil.*

**Es una pregunta de una funcion**, y *es lo primero que hay que mirar en F07: **leer `almacen.cambia_linea` y
ver si `momento` decide algo.***

### Y lo demas del criterio, para no perderlo

| lo que pide | estado |
|---|---|
| **dos sesiones, sin pisarse** | **mecanismo existe**; *falta comprobar si `momento` resuelve* |
| **lista por pasillos y orden por pasillo** | *por medir* -- *¿hay `categoria` en las lineas de la lista?* |
| C01-C05 con Bring!/AnyList/Listonic | **estudio de competencia**: *`docs/SUPERAPP-COMPETENCIA-Y-REA.md`* |
| **tarea movil con una mano** | *por medir* |
| **recorrido de cuenta vacia** | *por medir* |
| **medir pasos** | *por hacer, y es un numero* |

**Y el orden correcto es el que ya funciona en esta fase**: *primero **medir que falta** -- `momento`, los
pasillos, y los pasos --, y despues mejorar.* **No al reves.**


---

## 2. **El tachado esta protegido por diseno; la cantidad no** -- y el codigo dice que es a proposito

*(Ronda 87.)* Leida `almacen.cambia_linea` (`plataforma/api/almacen.py:406`), que era la pregunta de una
funcion:

```python
411  """Idempotente a proposito: tachar algo ya tachado no hace nada y no es un
412  error. Si los dos tachais a la vez, gana quien lo hizo antes y el otro ve lo
413  que queria ver.
415  `momento` es la hora del MOVIL, no la de llegada: tachar sin cobertura a las
416  18:04 y subirlo a las 18:20 cuenta como las 18:04, que si no el orden de los
417  hechos se lo inventa el servidor.
418  """
419  cuando = momento or datetime.now(timezone.utc)
...
421  if tachado is True:
422      trozos.append("en_carrito = true")
423      # COALESCE: si ya estaba tachado, se respeta el primero.
424      trozos.append("tachado_en = LEAST(COALESCE(tachado_en, %s), %s)")
426      trozos.append("tachado_por = COALESCE(tachado_por, %s)")
428  elif tachado is False:
429      trozos += ["tachado_en = NULL", "tachado_por = NULL", "en_carrito = false"]
430  if cantidad is not None:
431      trozos.append("cantidad = %s")      # gana el ultimo, a proposito
```

### Y la respuesta es distinta para cada campo

| campo | regla | y el motivo, escrito |
|---|---|---|
| **`tachado`** | **`LEAST` + `COALESCE`: gana el PRIMERO** | *«gana quien lo hizo antes y el otro ve lo que queria ver»* |
| **`tachado_por`** | **`COALESCE`: se queda el primero** | *para poder decir quien fue* |
| **`cantidad`** | **gana el ULTIMO** | *«a proposito», dice el comentario* |
| **`nota`** | *ausente = no tocar; `null` = quitarla* | *con el defecto del 30-sep documentado al lado* |

### Y eso choca con el criterio, que dice «no pisan cantidades ni tachados»

**El tachado cumple la afirmacion, y ademas bien**: *`LEAST` sobre la hora **del movil** -- no la de llegada --
hace que **el primero gane aunque llegue segundo***, y que el otro **vea lo que queria ver** en vez de un error.
*Es exactamente lo que pide el criterio, y resuelve el caso dificil: dos personas tachando el mismo brick desde
dos moviles sin cobertura.*

**La cantidad, no.** *«Gana el ultimo»* significa que **si dos personas cambian la cantidad a la vez, la
segunda pisa a la primera** -- *y **`momento` no se usa para la cantidad**: el `if cantidad is not None` no
mira `cuando` para nada.*

### Y aqui hay que decidir si es un defecto, y no antes de mirarlo

**Hay dos lecturas y no son la misma:**

1. **Es un defecto**: *el criterio dice «no pisan cantidades», y **esta claro que se pisan*** -- *la segunda
   escritura gana, y quien puso «3» se encuentra «2» sin saber por que.*
2. **Es una decision**: *«gana el ultimo» en una cantidad es defendible* -- *si mi pareja cambia de 2 a 6
   porque ha visto mas sitios, mi 3 viejo no deberia ganar por ser mas antiguo.*

**Y lo que decide entre las dos no es la opinion: es que pasa de verdad.** *Asi que lo siguiente es **probar
dos sesiones cambiando la misma cantidad**, con horas de movil distintas y en los dos ordenes de llegada, y ver
quien gana* -- *que es lo que el criterio pide medir y todavia no se ha medido.*

**Y hay un tercer caso que no he mirado**: *`tachado is False` **borra la hora sin mirar `cuando`*** -- *asi que
destachar **siempre gana** sobre tachar, sin importar el orden.* *Puede ser correcto -- destachar es una accion
deliberada --, pero **es una asimetria que conviene tener escrita**.*


---

## 3. **Medido con dos sesiones de verdad**: el tachado cumple, y la cantidad es un defecto

*(Ronda 89.)* `tests/test_fase2_f07_dos_sesiones.py` -- *cinco pruebas contra el Postgres de verdad, con su
propio usuario y su propia lista.* **El resultado:**

```
4 passed, 1 xfailed
```

| lo que se midio | resultado |
|---|---|
| **el tachado gana el PRIMERO aunque llegue segundo** | **pasa** -- *`LEAST`+`COALESCE` sobre la hora del movil* |
| **tachar dos veces no es un error** | **pasa** -- *idempotente, que es lo que pasa en el pasillo* |
| **destachar gana siempre, sin mirar la hora** | **pasa** -- *la asimetria de §2, ahora medida* |
| **la cantidad nueva gana si llega despues** | **pasa** |
| **la cantidad VIEJA no gana por llegar despues** | **FALLA** -- *y por eso queda fijada* |

### El defecto, con la medicion delante

```
AssertionError: gana la que llego ultima (3), no la mas nueva (5):
                la cantidad NO mira `momento`. Medido: 3
```

**Dos personas cambian la cantidad de la misma linea sin cobertura.** *Una a las 17:50 pone 3; la otra a las
18:30 pone 5.* **Y la de las 17:50 llega al servidor despues** -- *que es lo normal si se recupera la cobertura
mas tarde.* **El resultado es 3.**

**Y eso es exactamente lo que el comentario del tachado dice que no hay que permitir:**

> *«`momento` es la hora del MOVIL, no la de llegada: tachar sin cobertura a las 18:04 y subirlo a las 18:20
> cuenta como las 18:04, **que si no el orden de los hechos se lo inventa el servidor**.»*

**El tachado lo cumple. La cantidad no: `cantidad = %s` escribe sin mirar `cuando`.** *Asi que el servidor
**si** se inventa el orden de los hechos -- pero solo para la cantidad.*

### Y queda fijado, no arreglado, a proposito

```python
@pytest.mark.xfail(strict=True, reason=(
    "DEFECTO MEDIDO: `almacen.cambia_linea` escribe `cantidad = %s` sin mirar `momento`, asi que gana la "
    "ultima que LLEGA y no la mas nueva. ... Arreglo: comparar `momento` contra la hora del ultimo cambio de "
    "cantidad, como hace el tachado con LEAST+COALESCE."))
```

**No se arregla en la misma ronda en que se mide**, y por la razon de siempre: *el arreglo **necesita una
columna** -- la hora del ultimo cambio de cantidad, que hoy no existe -- y **decidir si gana la mas nueva o la
ultima es una decision del dueno**, no del que escribe la migracion.* *«Mi pareja cambio de 2 a 6 porque vio
mas sitios» es un argumento legitimo para que gane la ultima llegada.*

**Lo que si queda hecho es lo que hacia falta**: *la afirmacion del criterio **ya no es una suposicion** --
**esta medida, y en rojo**, con el defecto nombrado y el arreglo descrito.* *Y el dia que se arregle, la prueba
**fallara por pasar** y alguien lo sabra.*
