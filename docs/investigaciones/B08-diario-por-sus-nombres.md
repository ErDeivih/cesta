# B08 · **`core/diario.py`, por sus nombres**: idempotencia **por contenido**, y la cobertura

*(13 de octubre de 2026. **Tercera ronda de B08. Y el fichero se abre, por fin, en su cuerpo.**)*

## 1. Lo que hay: 348 lineas

```
core/diario.py -- 348 lineas

l23: BASE = RAIZ / "data" / "diario.sqlite"          <- SQLITE, no PostgreSQL
l24: TABLA = "entrada"
l26: ALIMENTO = "alimento" · l27: RECETA = "receta" · l28: TIPOS = (ALIMENTO, RECETA)

l30: ETIQUETA = "etiqueta"      l31: FICHA = "ficha"
l32: ESTIMADO = "estimado"      l33: DESCONOCIDO = "desconocido"
l34: FUENTES = (ETIQUETA, FICHA, ESTIMADO, DESCONOCIDO)
l36: COMIDAS = ("desayuno", "media manana", "comida", "merienda", "cena", "otras")

l96:  def _el_mismo_reintento(previa: tuple, contenido: dict) -> bool        <- LA IDEMPOTENCIA
l116: def _respuesta_del_reintento(previa, contenido, clave) -> int
l131: def apunta(con, propietario, fecha, comida, *, ...)                    <- apuntar consumo
l227: NUTRIENTES_DE_FICHA = (...)
l235: def de_ficha(producto: dict, gramos: float) -> dict                     <- EL SNAPSHOT
l259: def apunta_de_ficha(con, propietario, fecha, comida, ...)
l274: def borrar(con, propietario, entrada_id) -> bool                        <- «borrado propio»
l282: def _trae_dato(fila: sqlite3.Row) -> bool                               <- LA DOCTRINA
l287: def _COBERTURA(filas, columna, total) -> dict                           <- *** LA COBERTURA ***
l293: def dia(con, propietario, fecha) -> dict
l335: def rango(con, propietario, desde, hasta) -> list[...]
```

## 2. Y contesta **cinco** clausulas de B08

```
B08 PIDE                                          Y AQUI ESTA
  «porciones EFECTIVAS»                             `de_ficha(producto, gramos)` -- *** gramos: la
                                                    porcion EFECTIVA, no la de la receta ***
  «consultar SNAPSHOT NUTRICIONAL ... antes de
    confirmar»                                      *** `de_ficha(...) -> dict` -- el snapshot ***
  «... Y COBERTURA»                                 *** `_cobertura(filas, columna, total) -> dict` ***
  «recibo de consumo y correccion/BORRADO PROPIOS»   `apunta(...)` y `borrar(con, propietario, entrada_id)`
                                                    -- *** y `borrar` pide el `propietario` ***
  «IDEMPOTENCIA»                                    *** `_el_mismo_reintento(previa, contenido)` ***
  «sin totalizar un dia no completo»                 `dia(...)` y `_cobertura(filas, columna, total)`
                                                    *-- la cobertura **por columna** es justo eso*
  «objetivo OPCIONAL por persona y fecha»            *POR MIRAR -- no aparece en `diario.py`*
```

> *** Y hay **dos cosas que este fichero hace al reves que `traspaso`, y las dos importan**: ***
>
>   - **la idempotencia es POR CONTENIDO** *-- `_el_mismo_reintento(previa, contenido)` --, **y no por
>     operacion**;*
>   - **y vive en SQLITE** *(`data/diario.sqlite`), **no en PostgreSQL**.*
>
> *** O sea: son **dos almacenes distintos**, y **el titulo de B05** -- «idempotencia y consistencia **ENTRE
> ALMACENES**» -- *es **literalmente** esto: **uno en sqlite, otro en postgres**, y **los dos con su propia forma de
> no duplicar**.*
>
> *** Y `_el_mismo_reintento` es **la respuesta a la clausula (2) de B05**: *** *«misma clave con contenido
> distinto produce conflicto, no exito ficticio» -- *y **aqui la clave es el contenido**, asi que **hay que
> compararlo**, y **el resultado decide si es reintento o si es otra cosa** (`_respuesta_del_reintento`).*
>
> *** Los dos ficheros, juntos, son **las dos mitades del mismo problema** -- *y **por eso B08 y B05 son
> consecutivos en el plan**.*

## 3. Y `_trae_dato` es la doctrina, **otra vez, y como funcion**

```
l282: def _trae_dato(fila: sqlite3.Row) -> bool
```

> *** Una funcion que responde **«¿este campo trae dato?»** -- *y que es **la doctrina convertida en codigo**:*
> **«no se sabe» no es «es cero»**, *y **alguien tiene que decidirlo campo por campo**.*
>
> *** Y su pareja es `_cobertura(filas, columna, total)`: *** *cuenta **cuantos** traen dato **de cuantos**, **por
> columna** -- *que es **exactamente** la «cobertura por campo» de B06, *aplicada **al dia de una persona**.*

## 4. Y lo que NO se dice

**No se ha leido el cuerpo de `apunta` (l131-227, casi cien lineas, el trozo mas grande del fichero).** *No se dice
como decide entre ALIMENTO y RECETA, ni que guarda del snapshot, ni como usa `clave`.*

```
POR LEER:
  - `apunta` (l131-227) -- *** el trozo mas grande, y el que contesta «compra no es consumo» ***
  - `de_ficha` (l235-259) -- que campos del snapshot se guardan
  - `_cobertura` (l287-293) y `_trae_dato` (l282-287) -- los diez nombres
  - y `plataforma/api/diario.py`, que es donde esta la VISTA DE PREVISTOS
```

> *** Y `apunta` es, por tamano y por tema, **el sitio donde tiene que estar «una compra no es consumo»** *** -- *y su
> ensayo (`test_una_compra_no_es_consumo`) **ya se ha visto que existe**.*
>
> *** Pero **no se dice que lo haga ahi**: se dice que **es el sitio por donde hay que mirar**. ***
