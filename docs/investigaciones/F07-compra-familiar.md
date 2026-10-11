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

## 4. Pasillos: **estan hechos, con tres decisiones escritas** -- y me equivoque al medirlo

*(Ronda 90, **corregida en la 97**.)* El criterio pide *«lista por pasillos y **orden por pasillo**»*.

### Lo que escribi en la ronda 90, y era falso

> *«Leida la consulta que sirve la lista a la pantalla, `almacen.lineas_de` ... **el pasillo en la respuesta no
> esta** ... **La funcion no esta escrita; el dato esta**»*

**Lei UNA capa -- el `SELECT` de Postgres -- y concluí que la funcion no existia.** *Y existe, en la pantalla,
con tres decisiones escritas al lado.*

### Lo que hay de verdad

`plataforma/web/app/src/paginas/Cesta.tsx:386`:

```tsx
function porPasillo(lineas: Linea[]): [string, Linea[]][] {
  const sinPasillo = Number.MAX_SAFE_INTEGER
  const ordenadas = [...lineas].sort(
    (a, b) => (a.pasillo_orden ?? sinPasillo) - (b.pasillo_orden ?? sinPasillo),
  )
```

**Y encima, tres decisiones que estan escritas en el propio codigo (`Cesta.tsx:372-384`):**

1. **«Las lineas sin pasillo van al final y sin encabezado**, no al principio ni repartidas por donde "parezca".
   Cuando gold no trae la columna `seccion`, o el grupo no esta en el catalogo, no sabemos de que pasillo es:
   **eso no se rellena, se deja al final**.»
   > *Es la regla de la casa -- **lo que no se sabe se dice** -- aplicada a los pasillos.* **Y es la respuesta
   > exacta a la duda que yo planteaba en la ronda 90 sobre que hacer con lo que no tiene pasillo.**
2. **«Dentro de un pasillo se respeta el orden que manda la API»** (`en_carrito, anadido_en`), porque `sort` es
   estable -- *«ordenarlas aqui otra vez daria dos ordenes peleandose en cada recarga».*
3. **«Los pasillos se cortan por nombre, no por `seccion`»**, para pintar lo que se lee.

**Y usa `l.pasillo` y `l.pasillo_orden`, que la API entrega.** *No los vi porque mire donde no estaban.*

### Y el error, que es lo que hay que contar

**Es el tercero de la misma clase en esta sesion, y los tres iguales:**

| ronda | donde mire | **donde estaba** |
|---|---|---|
| 82 | el maestro, el crudo, la cola | **`kcal_100g`**, una columna que la app ensena |
| 96 | `git grep -c` y mi resumen del numero | **las cuatro lineas del front** que el comando si habia encontrado |
| **90** | **`almacen.lineas_de`** (Postgres) | **`Cesta.tsx:386`** (la pantalla) |

**Los tres son lo mismo: mirar una capa y concluir sobre el sistema.** *Y los tres se corrigen igual: **ir a ver
la capa que falta**, no razonar sobre la que ya mire.* **Es el error mas repetido de esta fase, y el mas facil de
cometer precisamente porque cada capa, leida sola, parece completa.**

### Y `C03`, corregido

| lo que pide | estado |
|---|---|
| **orden editable por lista/tienda; uso con una mano; conservacion al recargar** | **el orden por pasillo ESTA HECHO** (`porPasillo`, con las tres decisiones); *«editable» -- que el usuario lo cambie -- **eso si falta, y es otra cosa***; **una mano: 390x844 y 4 toques**; **la recarga SI**, por F03 |

**Asi que de C03 falta lo mas pequeno**: *que el orden se pueda **editar**.* **El agrupar por pasillo, que es lo
que yo daba por no hecho, esta hecho y bien.**

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


---

## 7. **El numero: cuatro toques.** Y la lista de casa ya viene creada

*(Ronda 93.)* Pasos medidos **de verdad**, con un navegador y una cuenta vacia:
`plataforma/prueba_f07_pasos.py`.

```
=== TOQUES DEL RECORRIDO DE CUENTA VACIA: 4 ===
        toque  1: abrir la app
        toque  2: escribir 'Gofres' en el buscador
        toque  3: pulsar buscar
        toque  4: anadir el producto a la lista
=== PASA ===
```

### Y tres cosas que salieron al medirlo, que no sabia

**1. `/compra` ES la pantalla de busqueda.** *El titulo es **`'Buscar · Cesta'`*** -- *asi que el recorrido
empieza buscando, y no hay que navegar a ningun sitio.* *Eso quita un toque que yo contaba.*

**2. La lista de casa ya viene creada.** *El ensayo dijo, literalmente:* **«no hay boton de crear lista: puede
que ya venga creada»** -- *y es que **viene creada**.* **Asi que el paso 2 del servidor (`POST /listas`) no
cuesta ningun toque al usuario**: *existe antes de que lo pida.*

> *Que es exactamente lo que decia el comentario de `main.py:518`, que lei en §5 y no acabe de entender hasta
> ahora: **«la lista de casa es el eje de la aplicacion: alimenta el contador del menu, el puente de la compra
> y las alertas»**.* **Si es el eje, se crea sola -- y por eso el usuario no la crea.**

**3. Los resultados traen un solo elemento pulsable**, y es el nombre del producto. *Doce resultados, y cada uno
se anade pulsandolo.* **Un toque por producto, que es lo que hay que medir para una compra entera.**

### Y los dos numeros, que son distintos y los dos hacen falta

| | cuenta | **que mide** |
|---|---|---|
| **servidor** (§5) | **4 peticiones** | *`registrarse` → `POST /listas` → `buscar` → `POST /lineas`* |
| **pulgar** (§7) | **4 toques** | *abrir · escribir · buscar · anadir* |

**Y no coinciden por casualidad**: *la lista de casa se crea **sin toque** (la crea el servidor al entrar), y
«abrir la app» no es una peticion.* **Coinciden en numero y no en contenido, que es justo la razon de contarlos
por separado** -- *decir «cuatro» a secas habria sido cierto y no habria dicho nada.*

### Y F07 queda con sus seis filas, ya casi todas con numero

| lo que pide su criterio | estado |
|---|---|
| **dos sesiones, sin pisarse** | **medido**: *el tachado cumple; **la cantidad es un defecto**, fijado con `xfail`* |
| **lista por pasillos** | **el dato esta, la funcion no**; *falta decidir de que tienda* |
| **recorrido de cuenta vacia** | **4 toques**, medidos en un navegador |
| **medir pasos** | **hecho**: 4 y 4, y son cosas distintas |
| **tarea movil con una mano** | *medido a 390x844 en el ensayo*; **falta que lo haga una mano de verdad** |
| **recarga** | **cubierta** por el ensayo de F03 |
| C01-C05 con Bring!/AnyList/Listonic | **estudio de competencia**, sin empezar |


---

## 8. C01-C05, contrastados -- y **no son una tarea aparte: son una lista de comprobacion**

*(Ronda 94.)* *Y al leerlos se ve lo que son.* **C01-C05 no son cinco funciones que haya que estudiar en
Bring! o Listonic: son cinco criterios de aceptacion, y cuatro de ellos ya estaban medidos en esta misma
investigacion -- por otro motivo.** *El estudio consistia en **contrastarlos**, no en empezarlos.*

**Los criterios, de `docs/SUPERAPP-COMPETENCIA-Y-REA.md:89-93`** -- *y el documento avisa de como leerlos:*
*«Las referencias son semillas de investigacion. La columna "aceptacion" define Cesta, **no afirma que el
competidor se comporte exactamente asi**»* ✓ **Asi que no hay que copiar a nadie: hay que cumplir el criterio.**

| ID | lo que pide | **estado, con la medida** |
|---|---|---|
| **C01** | *anadir/tachar/deshacer desde dos sesiones, sin perder cambios* | **medido** (§3): *el tachado **gana el primero** (`LEAST`+`COALESCE` sobre la hora del movil), tachar dos veces **no es error**, y **deshacer gana siempre*** |
| **C01b** | *ni exponer listas de otro hogar* | **NO MEDIDO** -- *y es la mitad que importa mas: es lo unico de C01 que es de seguridad.* **Hay `papel_en` y `_acceso` en el codigo, pero no se ha probado** |
| **C02** | *guardado sin catalogo* | **medido**: `anade_linea` acepta un nombre y `grupo_id`/`producto_id` son opcionales -- *una linea puede existir sin estar en ningun catalogo* |
| **C02b** | *vinculo posterior explicito y **precio desconocido visible*** | **NO MEDIDO** -- *y «precio desconocido **visible**» es una condicion de la pantalla, no del dato* |
| **C03** | *orden editable por lista/tienda; uso con una mano; conservacion al recargar* | **el orden NO esta** (§4: *el dato si, la funcion no*); **una mano: 390x844 y 4 toques** (§7); **la recarga SI** -- *cubierta por el ensayo de F03* |
| **C04** | *frecuentes sin confundir preferencia con necesidad; estados necesito/no necesito y carrito/comprado* | **NO MEDIDO** -- *hay `favoritos` y hay `en_carrito` separado de `tachado_en` en la tabla, pero no se ha comprobado que no se confundan* |
| **C05** | *acentos/typos/filtros utiles; **sugerir no significa declarar identidad exacta*** | **NO MEDIDO** -- *la pantalla tiene filtros (`cadena, pasillo, dieta, ofertas`), y la parte de «sugerir no es afirmar» es la misma que ya trata `AvisoIdentidad`, **pero no se ha probado en la busqueda***

### Y lo que sale al contrastarlos: **la mitad de C01-C05 esta sin medir, y no es la mitad facil**

**Cuatro de los cinco tienen su parte principal medida** -- *y por otros motivos: la concurrencia por F07, los
pasos por el criterio, la recarga por F03.* **Pero hay cuatro sub-criterios que no se han tocado, y tres de
ellos son de la clase que mas importa:**

1. **`C01b`: que no se expongan listas de otro hogar.** *Es **seguridad**, y es lo unico de la tabla que puede
   hacer dano si falla.* *El codigo tiene `papel_en` y `_acceso`; **que hagan su trabajo no se ha probado.***
2. **`C02b`: que el precio desconocido se vea.** *Una linea sin catalogo **tiene que poder decir que no sabe
   el precio**, y no ensenar un cero.* *Es el mismo patron que `nombre_visto` y que `nutricion_por`: **lo que
   no se sabe se dice.***
3. **`C04`: preferencia contra necesidad.** *«Frecuentes» y «lo que hace falta» son cosas distintas*, y la
   tabla ya las separa (`en_carrito` y `tachado_en` son columnas distintas) -- **pero separadas en la base no
   es separadas en la cabeza de quien las mira.***
4. **`C05`: que sugerir no sea afirmar.** *Es el mismo problema que `AvisoIdentidad` ya resuelve para las
   alternativas*, **y no esta dicho que la busqueda lo respete.**

### Y el orden que sale de aqui

**Lo siguiente de F07 no es estudiar a Bring!: es `C01b`, que es seguridad y es el unico que puede hacer
dano.** *Y se prueba como los demas: **dos sesiones de dos hogares distintos, y comprobar que la una no ve la
lista de la otra*** -- *que es `papel_en`, y es una prueba de una funcion.*


---

## 9. `C01b`, medido: **lo de seguridad pasa** -- y con las dos distinciones que importan

*(Ronda 95.)* `tests/test_fase2_f07_otro_hogar.py`, seis pruebas contra Postgres. **El resultado:**

```
6 passed
```

| lo que se comprobo | resultado |
|---|---|
| **el dueno tiene su lista y el de otro hogar no** (`papel_en`) | **pasa** |
| **un hogar ajeno no pasa el guardian** (`_acceso`) | **pasa** -- *403 o 404* |
| **el dueno si pasa** | **pasa** |
| **leer no es escribir** -- *`hace_falta_escribir` en los dos sentidos* | **pasa** |
| **un identificador que no es UUID da 404, no 500** | **pasa** |
| **una lista que no existe, tambien** | **pasa** |

### Y las dos distinciones que hacen que esto valga

**1. Se prueban las DOS piezas, no una.** *`papel_en` podria contestar bien **y las rutas no usarlo** -- y
entonces la lista se expondria igual.* **Por eso estan las dos: la funcion y el guardian que la usa.**

**2. Se prueba que el guardian deja pasar al dueno.** *Sin esa prueba, las otras pasarian **porque el guardian
no deja pasar a nadie*** -- que es la forma mas tonta de tener razon.* **Es el mismo error que la lista vacia
que contaba como distinta (§25 de F03): el instrumento dando por bueno lo que no ha medido.**

### Y una cosa que aparece y conviene guardar

**El guardian distingue leer de escribir** (`hace_falta_escribir`), **y ademas convierte un identificador que no
es UUID en un 404 en vez de un 500.** *Su comentario lo cuenta: se vio el 18-sep-2026 pidiendo `/api/listas/None`,
y Postgres rechazaba el texto al compararlo con una columna `uuid`, **asi que la peticion salia como 500 con su
traza en el log**.*

**Es la tercera vez en esta fase que aparece el mismo defecto**: *el 500 de la lista de casa duplicada, el 422 de
las lineas, y este 404.* **Los tres son «la restriccion hacia su trabajo y el mensaje culpaba al servidor»** --
*que es la frase que el propio codigo tiene escrita, y que es mejor que cualquier resumen mio.*

### Y C01-C05, con C01 entero

| ID | lo que pide | estado |
|---|---|---|
| **C01** | *dos sesiones sin perder cambios* | **medido** (§3): *el tachado gana el primero; **la cantidad es un defecto*** |
| **C01b** | *ni exponer listas de otro hogar* | **medido y pasa** (§9) |
| **C02 / C02b** | *sin catalogo* / *precio desconocido visible* | *lo primero medido; lo segundo no* |
| **C03** | *orden por pasillo* | *el dato esta, la funcion no* |
| **C04 / C05** | *preferencia contra necesidad* / *sugerir no es afirmar* | *sin medir* |

**De las dos mitades de C01, una tiene un defecto fijado y la otra pasa.** *Y la de seguridad -- que era la que
podia hacer dano -- **esta bien hecha**, con las dos piezas y con el caso del dueno comprobado.*


---

## 10. `C02b`: **hecho entero, dato y pantalla** -- y un error mio al medirlo

*(Ronda 96.)* El criterio (`SUPERAPP-COMPETENCIA-Y-REA.md:90`) pide, para `C02`: *«guardado sin catalogo, vinculo
posterior explicito y **precio desconocido visible**»*.

### El dato: hecho, y dicho mejor que en el criterio

`plataforma/api/almacen.py:519`:

```python
def _lo_que_se_paga(cent, parte, cantidad) -> int | None:
    """Cuanto suma una linea en la caja, o `None` si no hay precio que dar.
    ...
    **Y no se inventa un cero.** Sin precio, devuelve `None`: el cierre lo cuenta aparte (`sin_precio`),
    porque **un cero ahi afirmaria que salio gratis**.
    """
```

**Y en `cierra_compra`**: *«Una linea sin precio se guarda con `precio_cent` en NULL y se cuenta en
`sin_precio` -- tirarla borraria de la compra algo que si se compro, y **contarla como cero mentiria en el
total**.»*

### Y la pantalla: **tambien**, y con las palabras del criterio

```
plataforma/web/app/src/paginas/Cesta.tsx:749   {hecho.sin_precio > 0 && (
plataforma/web/app/src/paginas/Cesta.tsx:750     <> {hecho.sin_precio} sin precio conocido, co...
plataforma/web/app/src/paginas/Cesta.tsx:1511  {detalle.data.estimacion.sin_precio > 0 ...
plataforma/web/app/src/tipos.ts:729,927         sin_precio: number
plataforma/web/app/src/api/cesta.ts:315         sin_precio: number
plataforma/web/app/src/logica/gasto.ts:31,48    lineas_sin_precio?: number ... ?? 0
```

**La pantalla lo dice con las palabras exactas**: ***«N sin precio conocido»*** -- *y solo cuando hay alguno
(`> 0`), que es la regla de la casa.* **Y el `?? 0` de `gasto.ts` es sobre el CONTADOR, no sobre el precio** --
*que es lo correcto: contar cero lineas sin precio es un cero de verdad.*

**Asi que `C02b` esta cumplido entero, y mejor que el criterio.** *Es la cuarta comprobacion de esta
investigacion en que **el proyecto ya habia resuelto lo que yo iba a proponer**.*

### Y el error mio, que es lo que hay que contar de esta ronda

**Al medirlo escribi, en este mismo documento y en el mensaje del commit:**

> *«menciones en `plataforma/web/app/src`: **0** ... **no hay ni una mencion en el front** ... el contador viaja
> en el JSON y **no se pinta**»*

**Y era falso.** *El comando contaba **ficheros**, no menciones -- y devolvio **4**.* **Yo escribi «cero» al
lado del numero y no lo mire.** *Y el resultado fue una seccion entera, y un commit, **afirmando lo contrario
de lo que pasa**.*

**Es exactamente el error que llevo toda la fase cazando en el proyecto** -- *leer el nombre de un campo y creer
que he leido su contenido; la prosa diciendo una cosa y el numero otra* --, **y esta vez lo cometi yo, en la
misma ronda en que lo estaba describiendo.**

*Lo que lo caza es lo de siempre, y por eso esta escrito al lado del numero*: **mirar las cuatro lineas que el
comando habia encontrado, en vez de fiarme de mi resumen de lo que el comando decia.**

### Y C01-C05, con lo que hay

| ID | lo que pide | estado |
|---|---|---|
| **C01** | *dos sesiones sin perder cambios* | **medido**: *el tachado gana el primero; **la cantidad es un defecto**, fijado* |
| **C01b** | *ni exponer listas de otro hogar* | **medido y PASA** (§9) |
| **C02** | *guardado sin catalogo* | **medido**: *`anade_linea` acepta un nombre y `grupo_id` es opcional* |
| **C02b** | *precio desconocido **visible*** | **medido y PASA, entero**: el dato devuelve `None` y la pantalla dice **«N sin precio conocido»** |
| **C03** | *orden editable por lista/tienda* | *el dato esta, la funcion no* |
| **C04** | *preferencia contra necesidad* | *sin medir* |
| **C05** | *sugerir no es afirmar* | *sin medir* |


---

## 11. `C04`: **la separacion es estructural** -- dos tablas y dos columnas, no una convencion

*(Ronda 98.)* *Esta vez mire **las dos capas en el mismo comando**, que es la leccion de la ronda 97.*

**El criterio** (`SUPERAPP-COMPETENCIA-Y-REA.md:92`): *«Anadir frecuentes **sin confundir preferencia con
necesidad**; estados **necesito/no necesito** y **carrito/comprado**.»*

### Las dos capas, medidas

**Capa del dato** -- `information_schema`, en el Postgres de verdad:

```
favorito:     usuario_id, grupo_id, producto_id, anadido_en
lista_linea:  id, lista_id, grupo_id, producto_id, nombre_visto, cantidad, nota,
              anadido_por, anadido_en, tachado_por, tachado_en, borrado_en, tocado_en,
              en_carrito, cadena_elegida, autorizado, autorizado_en, ...
```

**Capa de la pantalla** -- `GET /api/habituales`, y *«el mosaico de lo habitual: "lo de siempre", para
anadir...»* (`Mosaico.tsx`), con `LoQueSeCompra.tsx` al lado.

### Y la separacion no es una convencion: **es la forma de la base**

| lo que el criterio pide | **como esta** |
|---|---|
| **preferencia** | **la tabla `favorito`**, con `usuario_id` y el producto -- *y **nada mas*** |
| **necesidad** | **la tabla `lista_linea`**, con su lista y su cantidad |
| **carrito** | **`en_carrito`**, una columna |
| **comprado** | **`tachado_en`** (y `borrado_en`), **otra columna** |

**Asi que marcar un favorito no anade nada a ninguna lista** -- *son tablas distintas y ninguna escribe en la
otra.* **Y «en el carro» y «tachado» son dos columnas separadas**, no un estado con dos nombres.

**Es la quinta comprobacion de esta investigacion en que el proyecto ya habia resuelto lo que yo iba a
proponer** -- *y esta es la mas limpia de las cinco: **la distincion esta en el esquema**, que es donde una
distincion no se puede olvidar.*

### Y lo que NO queda medido, que es lo unico que podria faltar

**El esquema separa preferencia de necesidad. Que la pantalla no las mezcle en la cabeza de quien la usa es otra
cosa** -- *y esa no se mide con un `SELECT`.* *El nombre del componente ayuda (`Mosaico`, «lo de siempre»,
frente a la lista), pero **«el nombre del componente ayuda» es exactamente el tipo de razonamiento que me ha
fallado tres veces esta sesion** (§4, §10 y la ronda 96).*

**Asi que queda dicho como lo que es**: *la separacion **estructural** esta **medida y es correcta**; la
**de la pantalla**, sin medir, y para eso hace falta mirarla con un navegador y una lista con favoritos.*

### Y C01-C05, con lo que hay de verdad

| ID | lo que pide | estado |
|---|---|---|
| **C01** | *dos sesiones sin perder cambios* | **medido**: *el tachado gana el primero; **la cantidad es un defecto**, fijado* |
| **C01b** | *ni exponer listas de otro hogar* | **medido y PASA** |
| **C02** | *guardado sin catalogo* | **medido** |
| **C02b** | *precio desconocido visible* | **medido y PASA** |
| **C03** | *orden por pasillo / una mano / recarga* | **el orden ESTA HECHO** (§4 corregido); *«editable» falta*; 4 toques; recarga por F03 |
| **C04** | *preferencia contra necesidad* | **la separacion estructural, medida y correcta** (dos tablas, dos columnas); *la pantalla, sin medir* |
| **C05** | *sugerir no es afirmar* | *sin medir* |


---

## 12. `C05`: **el aviso de identidad existe y esta bien** -- y en los resultados de busqueda **no lo he concluido**

*(Ronda 99.)* **El criterio** (`SUPERAPP-COMPETENCIA-Y-REA.md:93`): *«Acentos/typos/filtros utiles; **sugerir no
significa declarar identidad exacta**.»*

### Lo que si esta medido

**El aviso existe, y distingue bien** -- `plataforma/web/app/src/componentes/AvisoIdentidad.tsx`:

```tsx
19  export function AvisoIdentidad({ identidad, motivo }) {
20    identidad?: string | null
25    if (CONFIRMADO.has(identidad)) return null      // <- si esta confirmado, NO avisa
26    const esSeguro = identidad === 'probable'
```

**Solo avisa cuando la identidad NO esta confirmada**, *y distingue «probable» del resto* -- *que es la
distincion que el criterio pide, y en el sitio correcto: **el aviso, no el dato.***

**Y se usa** -- `RepartoEnTiendas.tsx:390`: `<AvisoIdentidad identidad={f.i…}` -- *que es la pantalla donde de
verdad hay que avisar: **la que compara el mismo producto entre tiendas**.*

**Y hay una decision escrita al lado**, en `BotonAnadirACesta.tsx:17`: *«No sustituir la eleccion concreta
antes …»*.

### Y lo que **no** he concluido, a proposito

**Mi grep de `AvisoIdentidad` no lo encontro en los resultados de busqueda.** *Y **no voy a decir por eso que
falte**.*

**Es exactamente el error que he cometido tres veces en esta sesion:**

| ronda | conclui de una capa | **y estaba en otra** |
|---|---|---|
| 82 | que no habia nutricion | **`kcal_100g`**, que la app ensena |
| 90 | que no habia orden por pasillo | **`Cesta.tsx:386`** |
| 96 | que `sin_precio` no se pintaba | **cuatro lineas del front** |

**Asi que lo que se puede afirmar es solo esto**: *el aviso **existe**, **distingue** lo confirmado de lo
probable, y **se usa en la comparacion entre tiendas**.* **Lo que NO esta medido es si los resultados del
buscador llevan su identidad y la ensenan** -- *y para saberlo hay que leer como construye sus resultados
`catalogo.buscar` (linea 254) y despues mirar la pantalla, **no un grep**.*

*Queda escrito como lo que es: **una capa medida y otra sin medir**, y la distincion dicha.*

### Y C01-C05, al cerrar esta parte

| ID | lo que pide | estado |
|---|---|---|
| **C01** | *dos sesiones sin perder cambios* | **medido**: *el tachado gana el primero; **la cantidad es un defecto**, fijado con `xfail`* |
| **C01b** | *ni exponer listas de otro hogar* | **medido y PASA** (6 pruebas) |
| **C02** | *guardado sin catalogo* | **medido** |
| **C02b** | *precio desconocido visible* | **medido y PASA** |
| **C03** | *orden por pasillo / una mano / recarga* | **el orden ESTA HECHO**; *«editable» falta*; 4 toques; recarga por F03 |
| **C04** | *preferencia contra necesidad* | **estructural, medida y correcta**; *la pantalla, sin medir* |
| **C05** | *sugerir no es afirmar* | **el aviso existe y distingue, y se usa entre tiendas**; *los resultados del buscador, sin medir* |

**De siete sub-criterios: cinco medidos, cuatro pasan, uno es un defecto fijado, y dos tienen una capa sin
medir** -- *y las dos capas que faltan son **la pantalla**, que es donde esta el trabajo que queda de F07.*


---

## 13. `C05`, la capa que faltaba: **el buscador devuelve grupos y precios, y no promete identidad**

*(Ronda 100.)* Leida la funcion que construye los resultados, `catalogo.buscar`
(`plataforma/api/catalogo.py:254`):

```python
254  def buscar(texto: str, cadenas=None, limite: int = 40, ...
258             sin_alcohol: bool = False, seccion: str | None = None) -> list[dict]:
259      """Grupos que casan con el texto, cada uno con su precio mas bajo.
261      Los productos sin grupo salen igual, marcados: son 32.522 de 51.800 y
262      esconderlos seria esconder el 63 % del catalogo.
263      """
264      palabras = [p for p in _sin_tildes(texto).lower().split() if p]
265      # Sin texto no hay busqueda... salvo que se este explorando un pasillo, que
266      # es una busqueda por si misma: "ensename lo que hay en congelados".
267      if not palabras and not seccion:
268          return []
```

### Lo que esto contesta, y lo que no

**Lo que contesta, y son dos cosas del criterio:**

1. **«Acentos»** -- *esta hecho, y se ve en la primera linea de trabajo: **`_sin_tildes(texto)`**, tanto en lo
   que se busca como, por simetria, en lo que se compara.* **El criterio pedia «acentos/typos utiles»** --
   *los acentos estan.*
2. **«Sugerir no significa declarar identidad exacta»** -- *y el buscador **no promete identidad**: devuelve
   **grupos que casan con el texto, cada uno con su precio mas bajo**.* **No hay campo `identidad` en
   `catalogo.py`** -- *ni en `buscar` ni en el resto del modulo.*

**Y hay una decision escrita que importa mas de lo que parece** -- *linea 261*:

> *«Los productos sin grupo salen igual, **marcados**: son 32.522 de 51.800 y **esconderlos seria esconder el
> 63 % del catalogo**.»*

**Es el criterio aplicado al reves, y bien**: *lo que no esta agrupado **no se esconde ni se disfraza** --
**sale, y sale marcado**.* **Que es la misma regla de `nombre_visto`, `nutricion_por` y «sin precio conocido»:
lo que no se sabe se dice.**

### Y lo que sigue sin medirse, y por que no lo cierro

**Que `buscar` no lleve `identidad` significa que **no la declara en el dato**.** *Lo que no esta medido es **que
la pantalla no la insinue de otra forma*** -- *un resultado con un nombre, una marca y un precio **sugiere**, y
sugerir es lo que el criterio permite; **pero eso hay que verlo**, no deducirlo.*

**Y sigue siendo la leccion de esta sesion**: *he leido **tres capas** de `C05` -- el aviso, su uso, y el
buscador -- y **las tres dicen lo mismo**; la cuarta, **la pantalla**, es la que no he mirado.* **No la sustituyo
por un razonamiento.**

### Y C01-C05, cerrado con lo que hay

| ID | lo que pide | capas medidas |
|---|---|---|
| **C01** | *dos sesiones sin perder cambios* | **medido** -- *el tachado gana el primero; **la cantidad es un defecto**, fijado* |
| **C01b** | *ni exponer listas de otro hogar* | **medido y PASA** |
| **C02** | *guardado sin catalogo* | **medido** |
| **C02b** | *precio desconocido visible* | **medido y PASA** (dato **y** pantalla) |
| **C03** | *pasillos / una mano / recarga* | **el orden ESTA HECHO**; *«editable» falta*; 4 toques; recarga por F03 |
| **C04** | *preferencia contra necesidad* | **estructural, medida y correcta**; *la pantalla, sin medir* |
| **C05** | *acentos/typos/filtros; sugerir no es afirmar* | **el aviso, su uso y el buscador, medidos**; *la pantalla del buscador, sin medir* |

**De siete sub-criterios: seis con su capa principal medida, cuatro pasan, uno es un defecto fijado, y tres
tienen una capa de pantalla sin mirar.** *Y las tres que faltan son la misma: **mirar la pantalla con un
navegador**, que es lo que queda de F07 y lo que el criterio llama «uso con una mano».*


---

## 14. **`C05`, medido en la pantalla: sugiere y no afirma** -- y C03/C04 necesitan otra pantalla

*(Ronda 101.)* *Las tres capas que faltaban son la misma -- **mirar la pantalla** --, asi que se anadieron al
ensayo que ya corre (`plataforma/prueba_f07_pasos.py`), con su navegador y su sesion.*

### C05: **contestado, y cumple el criterio**

**Lo que la pantalla ensena de un resultado del buscador, leido literalmente:**

```
'Gofres con chocolate Hacendado

mercadona · Hacendado

ahorras un 7,7 %

 comparable · 2 cadenas
E
sin Eco-Score
33,55 EUR
5…'
```

**Y buscadas en toda la pantalla las palabras con las que se afirmaria una identidad** -- *«confirmad»,
«exacto», «es el mismo», «probable», «parecid», «sin confirmar», «puede ser», «identidad»* --, **no aparece
ninguna.**

**Asi que el resultado dice**: *el nombre, **la cadena** (`mercadona`), **la marca** (`Hacendado`), el ahorro,
**«comparable · 2 cadenas»**, el Eco-Score y el precio. **Lo que no dice es que sea el mismo producto que otro**
-- *y **«comparable · 2 cadenas» es justo lo contrario de afirmarlo**: dice en cuantas cadenas aparece, no que
sean el mismo.*

**El criterio** -- *«sugerir no significa declarar identidad exacta»* -- **se cumple, y ahora esta medido en la
pantalla y no deducido de tres capas.** *Y la cuarta capa decia lo mismo que las otras tres, que es lo que
habia que comprobar.*

### C03 y C04: **esta pantalla no es la suya**, y se dice

```
encabezados en pantalla: 0
menciones de lo habitual: 0
menciones de en el carro: 0
```

**Y no es que falten: es que este ensayo corre sobre `/compra`, que es la pantalla de BUSCAR** -- *y ahi no hay
lista con lineas, ni agrupacion por pasillo, ni mosaico de habituales, ni nada que este en el carro.* **Un cero
aqui no dice nada de C03 ni de C04** -- *diria algo si el ensayo estuviera en la pantalla de la lista, y **no lo
esta**.*

**Decir «C03 y C04 no se ven» a partir de estos ceros seria exactamente el error de las rondas 82, 90 y 96** --
*medir en un sitio y concluir sobre otro.* **Asi que queda dicho como lo que es: el ensayo no llega a esa
pantalla, y para C03 y C04 hace falta **una lista con lineas y su agrupacion**, que es otra prueba.**

### Y C01-C05, con las capas dichas

| ID | lo que pide | **capas medidas** |
|---|---|---|
| **C01** | *dos sesiones sin perder cambios* | **dato** -- *el tachado gana el primero; **la cantidad es un defecto**, fijado* |
| **C01b** | *ni exponer listas de otro hogar* | **dato, y PASA** |
| **C02** | *guardado sin catalogo* | **dato** |
| **C02b** | *precio desconocido visible* | **dato y pantalla, y PASA** |
| **C03** | *pasillos / una mano / recarga* | **el agrupador, en el codigo** (`porPasillo`); **4 toques**; **recarga por F03**; *la pantalla con lista, sin mirar* |
| **C04** | *preferencia contra necesidad* | **dato** (dos tablas, dos columnas); *la pantalla, sin mirar* |
| **C05** | *acentos/typos/filtros; sugerir no es afirmar* | **dato, uso y pantalla** -- *y **PASA*** |

**Cinco de siete con la pantalla o el dato medido; cuatro pasan; uno es un defecto fijado; y los dos que faltan
-- `C03` y `C04` -- son **la misma prueba**: un ensayo sobre la pantalla de la lista, con lineas de varios
pasillos y un favorito.**


---

## 15. `C04`, medido en la pantalla: **seguir no es la lista**, y lo dice la propia pantalla

*(Ronda 102.)* Montado el escenario por la API -- *una lista de casa con lineas de verdad* -- y recorridas las
pantallas. **Y la de favoritos contesta `C04` sin necesidad de montar nada mas:**

```
/compra/favoritos:
  «Favoritos
   No sigues ningún producto
   Aquí van los pocos que compras siempre, para ver si se mueven sin tener que buscarlos.
   Se añaden desde la ficha de un producto, con el corazón.
   [Buscar un producto]  [Ver mi lista]»
```

**Las cuatro cosas que dice, y las cuatro son la respuesta al criterio:**

| lo que dice la pantalla | lo que contesta |
|---|---|
| **«Favoritos»** | *la **preferencia**, con su nombre* |
| **«No sigues ningún producto»** | *seguir es **otra cosa** que tener: **preferencia, no necesidad*** |
| **«los pocos que compras siempre, para ver si se mueven»** | *y para que sirve: **mirar el precio**, no para la lista* |
| **«Se añaden desde la ficha de un producto, con el corazón»** | *y **el gesto es distinto**: se anaden **a favoritos**, no a la lista* |
| **«Ver mi lista»** *(enlace aparte)* | *la lista es **otro sitio**, y estan separados **en la pantalla** |

**Asi que `C04` esta cumplido tambien en la pantalla, y no por convencion: *la pantalla misma dice que son
cosas distintas, que se llenan de sitios distintos y que sirven para cosas distintas.*** **Y el «corazón» frente
a «anadir a la lista» es la separacion que el criterio pedia, hecha gesto.**

### Y lo que sale al montar el escenario, que es mas de lo que parece

**Tres cosas que el ensayo cazo, y las tres son la misma clase:**

1. **La app ensena LA LISTA DE CASA, y yo escribia en otra.** *La primera version creaba una lista nueva con
   `crea_lista(...)`, y las seis lineas salieron **0 de 6 en las tres pantallas**: estaba mirando una lista y
   escribiendo en otra.*
2. **`crea_usuario` NO crea la lista de casa** -- *`listas_de` devolvio `[]`.* **La crea el alta por la API**
   (`POST /api/registrarse`), *y por eso en la ronda 93 el recorrido de cuenta vacia decia **«no hay boton de
   crear lista: puede que ya venga creada»**.* **Dos caminos para crear una cuenta y solo uno hace el trabajo
   entero** -- *el mismo patron que las dos vias de ficha de F05.*
3. **Las rutas no se adivinan.** *`/lista` y `/compra/lista` contestan **«Esa pantalla no existe»***, y la
   portada dice lo que hay: *«Compra: **Buscar, la lista, favoritos y lo que gastas**»*. **El camino bueno es
   pulsar «Ver mi lista», no componer la URL** -- *y para eso esta el navegador.*

### Y `C03` queda con una sola cosa: llegar a la lista

**`/compra/lista` no existe, y la pantalla de favoritos **ofrece el enlace** («Ver mi lista»).** *Asi que la
medicion de `C03` -- ver los encabezados de pasillo con lineas de verdad -- **esta a un clic**, y el clic es lo
que hay que dar: **pulsar «Ver mi lista» y leer los encabezados**, en vez de componer la ruta -- que es
exactamente lo que acabo de aprender en esta misma ronda.*

### Y C01-C05, con las capas

| ID | lo que pide | **capas medidas** |
|---|---|---|
| **C01** | *dos sesiones sin perder cambios* | **dato** -- *la cantidad es un defecto fijado* |
| **C01b** | *ni exponer listas de otro hogar* | **dato, y PASA** |
| **C02 / C02b** | *sin catalogo / precio desconocido visible* | **dato y pantalla, y PASA** |
| **C03** | *pasillos / una mano / recarga* | **4 toques** y **recarga**; *los encabezados, a un clic («Ver mi lista»)* |
| **C04** | *preferencia contra necesidad* | **dato y pantalla, y PASA** -- *«seguir» no es la lista, y el gesto es el corazon* |
| **C05** | *acentos/filtros; sugerir no es afirmar* | **dato, uso y pantalla** -- *y **PASA*** |

**Cinco de siete con dato y pantalla; cuatro pasan; uno es un defecto fijado; y `C03` es el unico que queda a
medias -- y a un clic.**


---

## 16. **`C03`, medido y PASA** -- y tres pases vacios por el camino

*(Ronda 103.)* Pulsado «Ver mi lista» -- *en vez de componer la ruta, que es lo que enseño la ronda 102* --, y
leidos los encabezados:

```
url: /compra/listas
6 de 6 productos en pantalla
encabezados: 14
  [0] 'Casa'
  [1] 'Lo que hay que coger'
  [2] 'BEBIDAS'                  <- EL PASILLO
  [3] 'Dónde compro cada cosa'
  [4] 'Sin decidir (6)'
encabezados que son pasillos: ['bebidas']
```

**`porPasillo` esta haciendo su trabajo, con su encabezado de verdad, y las seis lineas estan.** *`C03` queda
medido: **la agrupacion por pasillo, en la pantalla, con lineas de verdad***

### Y tres pases vacios hasta llegar aqui, los tres mios

**Esta medicion costo cuatro intentos, y **los tres primeros pasaron sin medir nada**:

| intento | lo que hice | **por que no medía** |
|---|---|---|
| 1 | puse las lineas **sin `grupo_id`** | *sin grupo no hay pasillo: `porPasillo` las manda al final y sin encabezado -- **su decision escrita**, y por eso no podia salir nada* |
| 2 | comprobe **«hay encabezados»** | *y habia ocho -- **«Casa», «Lo que hay que coger», «Compartir»** -- que son **secciones de la pagina, no pasillos*** |
| 3 | busque **«vinos» en el texto** | *y salio porque **los nombres de producto lo traen** («Vino tinto crianza...»)* |
| 4 | **`grupo_id` real, y el pasillo en un ENCABEZADO** | **aqui si** -- *y sale `'BEBIDAS'`* |

**Los tres primeros son el mismo error de esta fase, y ahora tres veces en una sola medicion**: *el instrumento
dando por bueno lo que no ha medido.* **Y lo que los corrige es lo de siempre: mirar lo que salio -- los ocho
encabezados, la palabra «vinos» -- en vez de mirar el `ok`.**

### Y C01-C05, al cerrar

| ID | lo que pide | **capas medidas** | |
|---|---|---|---|
| **C01** | *dos sesiones sin perder cambios* | **dato** | *la cantidad es un defecto, **fijado*** |
| **C01b** | *ni exponer listas de otro hogar* | **dato** | **PASA** |
| **C02** | *guardado sin catalogo* | **dato** | **cumple** |
| **C02b** | *precio desconocido visible* | **dato y pantalla** | **PASA** |
| **C03** | *pasillos / una mano / recarga* | **pantalla** | **PASA** -- *`'BEBIDAS'`; 4 toques; recarga por F03* |
| **C04** | *preferencia contra necesidad* | **dato y pantalla** | **PASA** -- *«seguir» no es la lista* |
| **C05** | *sugerir no es afirmar* | **dato, uso y pantalla** | **PASA** |

**Seis de los siete sub-criterios pasan; uno -- la cantidad -- es un defecto medido y fijado; y `C03`, `C04` y
`C05` ya tienen la pantalla mirada.** *Lo que queda de C01-C05 es **un arreglo** (la cantidad) y **nada mas** --
*y el arreglo espera una decision del dueno, no una medicion.*
