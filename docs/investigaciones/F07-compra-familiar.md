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


---

## 4. Pasillos: **la funcion no esta, y el dato si** -- a un `LEFT JOIN` de distancia

*(Ronda 90.)* El criterio pide *«lista por pasillos y **orden por pasillo**»*. Leida la consulta que sirve la
lista a la pantalla, `almacen.lineas_de` (`plataforma/api/almacen.py:342`):

```sql
SELECT li.id, li.grupo_id, li.producto_id, li.nombre_visto, li.cantidad,
       li.nota, li.tachado_en, li.anadido_en, li.en_carrito, li.cadena_elegida,
       qa.nombre AS anadido_por, qt.nombre AS tachado_por
  FROM lista_linea li
  LEFT JOIN usuario qa ON qa.id = li.anadido_por
  LEFT JOIN usuario qt ON qt.id = li.tachado_por
 WHERE li.lista_id = %s AND li.borrado_en IS NULL
 ORDER BY li.en_carrito, li.anadido_en
```

### Lo que hay, y lo que no

| pieza | estado |
|---|---|
| **el pasillo en la respuesta** | **no esta** -- *no hay `categoria` en el `SELECT`* |
| **el orden** | **`en_carrito, anadido_en`**: *lo tachado al final, y dentro, por orden de alta* -- **no por pasillo** |
| **`grupo_id` en la linea** | **si esta** |
| **`categoria` en `grupos`** | **si esta** (medida en la ronda 82: *62 columnas, y `categoria` trae cosas como `la-despensa/lacteos`*) |

**Asi que el pasillo **no hay que inventarlo ni pedirlo a nadie**: *es un `LEFT JOIN grupos ON grupos.grupo_id
= li.grupo_id`, y una columna mas en la respuesta.* **La funcion no esta escrita; el dato esta.**

### Y el orden que hay es defendible, y no es el que falta

**`ORDER BY li.en_carrito, li.anadido_en`** hace lo correcto para una lista de la compra: *lo ya cogido **al
final** -- para que no estorbe mientras se recorre -- y dentro de cada grupo, por orden de alta.* **Es el orden
de una lista corriente, no el de un supermercado.**

**Y el de pasillo es otra cosa**: *agrupar por `categoria` para **recorrer la tienda en un solo sentido** y no
volver atras.* *Que es exactamente lo que pide C01-C05 de las referencias.*

### Y una advertencia que hay que decir antes de construirlo

**El pasillo de `grupos` es el de la cadena que lo capturo, y cada cadena tiene el suyo.** *`la-despensa/lacteos`
de Carrefour **no es el mismo pasillo** que el de Alcampo, y el orden fisico de las tiendas tampoco es el
mismo.* **Asi que «ordenado por pasillo» solo significa algo si se dice **en que tienda** -- y la linea ya tiene
`cadena_elegida` para eso.**

**Es la decision que hay que tomar antes de escribir el `ORDER BY`**: *¿se ordena por el pasillo de la tienda
elegida en la linea, por el de la cadena del producto, o por una lista de pasillos propia de casa?* **Las tres
son defendibles y dan listas distintas** -- *y elegir una sin decirlo es como se construye un orden que no sirve
para recorrer nada.*

### Y F07 queda asi, con lo suyo medido

| lo que pide su criterio | estado |
|---|---|
| **dos sesiones, sin pisarse** | **medido** (§3): *el tachado cumple; **la cantidad es un defecto**, fijado* |
| **lista por pasillos** | **el dato esta** (`grupo_id` + `categoria`), **la funcion no**; *y hay que decidir de que tienda* |
| C01-C05 con Bring!/AnyList/Listonic | **estudio de competencia**, sin empezar |
| **tarea movil con una mano** | *por medir* |
| **recorrido de cuenta vacia** | *por medir* |
| **medir pasos** | *por hacer* |


---

## 5. «Medir pasos»: **los del servidor son cuatro** -- y los de la pantalla no los he contado

*(Ronda 91.)* El criterio acaba con *«medir pasos»*, que es un numero y por eso hay que darlo. **Y hay que decir
de que son los pasos**, porque no es lo mismo:

### Los pasos del SERVIDOR, que si estan contados

Contadas las rutas que hacen falta para el **recorrido de cuenta vacia** -- *lo que pide el criterio* --, en
`plataforma/api/main.py`:

| paso | ruta | linea |
|---|---|---|
| 1 | **`POST /api/registrarse`** (o `/api/entrar` si ya hay cuenta) | 100 (o 82) |
| 2 | **`POST /api/listas`** -- *la lista de casa* | 518 |
| 3 | **`GET /api/buscar`** -- *encontrar el producto* | 390 |
| 4 | **`POST /api/listas/{lista_id}/lineas`** -- *anadirlo* | 698 |

**Cuatro peticiones.** *Y el paso 2 no se puede saltar:* **la lista de casa es el eje** -- *alimenta el contador
del menu, el puente de la compra y las alertas* --, y **una linea necesita una lista donde vivir.**

### Y lo que NO he contado: los toques en la pantalla

**«Pasos» en el criterio es, con toda probabilidad, toques con el pulgar, no peticiones.** *Y esos no los he
contado* -- *hacen falta la pantalla y alguien usandola.* **Decir «cuatro» y dejarlo ahi seria confundir una
cosa con la otra**, que es la clase de error que llevo toda la fase encontrando.

**Lo que se puede afirmar sin la pantalla**: *la app necesita **cuatro viajes al servidor** para que una cuenta
nueva tenga su primer producto en la lista.* **Cuantos toques hacen falta para provocarlos es otra medida, y
estA pendiente.**

### Y una pieza que aparece al mirarlo, y conviene guardar

**El alta de la lista de casa tenía un defecto, y ya está arreglado** (`main.py:518`):

```
# **Una lista de casa por persona, y la base lo impone** (`lista_de_casa_por_dueno`). La regla es la
# correcta -- la lista de casa es el eje de la aplicacion --, pero **la respuesta era mentira**: crear
# la segunda salia como **500 «Internal Server Error»**, que manda a mirar los registros de la API por
# algo que el usuario puede entender y resolver. Medido el 11 de octubre de 2026 contra la API viva:
# `UniqueViolation: ... "lista_de_casa_por_dueno"`.
# Es la misma clase de defecto que el 422 de las lineas: **la restriccion hacia su trabajo y el
# mensaje culpaba al servidor**.
try:
    return almacen.crea_lista(usuario["id"], datos.nombre, datos.es_de_casa)
except psycopg.errors.UniqueViolation as choque:
    raise HTTPException(409, "Ya tienes una lista de casa, y solo puede haber una. ...")
```

**Un 500 que ahora es un 409 con una frase que se entiende.** *Y el comentario dice la leccion mejor que yo:
**«la restricción hacía su trabajo y el mensaje culpaba al servidor»**.* **Es la misma clase de defecto que el
422 de las líneas** -- *los dos ya cerrados* --, **y el mismo que encontré en F00 con `alerta`: un dato correcto
con un mensaje que manda a mirar donde no es.**

### Y F07, con sus seis filas

| lo que pide su criterio | estado |
|---|---|
| **dos sesiones, sin pisarse** | **medido**: *el tachado cumple; **la cantidad es un defecto**, fijado* |
| **lista por pasillos y orden por pasillo** | **el dato está** (`grupo_id`+`categoria`), **la función no**; *falta decidir de qué tienda* |
| **recorrido de cuenta vacía** | **4 pasos de servidor** (medido); **los toques de pantalla, pendientes** |
| **medir pasos** | **medido a medias, y se dice cuál mitad** |
| **tarea móvil con una mano** | *por medir -- necesita la pantalla* |
| **recarga** | *cubierta por el ensayo de F03 (la pantalla se recarga y sirve la versión nueva)* |
| C01-C05 con Bring!/AnyList/Listonic | **estudio de competencia**, sin empezar |


---

## 6. La pantalla del recorrido: **`Cesta.tsx`, 1.779 lineas** -- y los toques siguen sin medirse de verdad

*(Ronda 92.)* El recorrido de cuenta vacía vive en **`plataforma/web/app/src/paginas/Cesta.tsx`** -- *1.779
lineas* --, y contados sus elementos interactivos:

| linea | elemento | para qué |
|---|---|---|
| 233 | `onClick={() => setCreando(!creando)}` | *abrir el alta de lista* |
| 584 | `placeholder="La del sábado"` | *el nombre de la lista* |
| 587 | `<Boton ... onClick={() => crear.mutate()}>` | *crear* |
| 537 | `onClick={() => setEscribiendo(true)}` | *empezar a escribir un producto* |
| 450 / 459 | `cambiar(linea.id, { cantidad: … ± 1 })` | *subir y bajar la cantidad* |
| 468 | `cambiar(linea.id, { borrado: true })` | *quitar la línea* |
| 567 / 569 | `setAbierto(true)` | *el selector de lista* |

### Y por que esto **no** es la respuesta

**El criterio pide «medir pasos», y contar los botones de un fichero no es medir pasos.** *Lo que hace falta
es **hacer el recorrido y contar los toques**: abrir la app vacía, crear la lista, buscar el producto,
anadirlo.* **El orden y los campos que aparecen dependen del estado** -- *si ya hay lista no se crea, si no hay
sesión se entra primero* --, **y eso no se lee: se usa.**

**Asi que lo unico que puedo afirmar con esto es que los elementos existen y donde estan.** *El numero sigue
pendiente, y ahora se sabe exactamente donde medirlo: **`Cesta.tsx`, con un navegador y una cuenta vacía**.*

### Y la mitad que sí está, para no perderla

**Los pasos del servidor, del §5: cuatro peticiones.** *`registrarse` → `POST /listas` → `buscar` →
`POST /lineas`.* **Y el ensayo de F03 (`plataforma/prueba_f03_publicacion.py`) ya monta lo que hace falta**:
*un navegador, una cuenta con sesión, una lista creada, y la pantalla de `/compra` con su buscador.*
**Anadirle un contador de toques es trabajo pequeno y con el andamio hecho.**
