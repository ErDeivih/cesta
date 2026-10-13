# B08 · **EL ULTIMO PASO DE LA PREVISION YA EXISTE** -- en `core/diario.py`, y entero

*(13 de octubre de 2026. **Y reduce lo que falta de B08 a UNA pieza.**)*

## 1. Lo que hay, literal

```python
# core/diario.py
l13   # `sin_dato` y el dia no esta `completo`. Y los macronutrientes se suman con independencia de si la [...]
l140      **Rechaza `compra` a proposito.** Comprar no es comer: si una compra entrara aqui, el diario sumaria [...]
l235  *** def de_ficha(producto: dict, gramos: float) -> dict: ***      *<- de una FICHA a una ENTRADA*
l259  def apunta_de_ficha(con, propietario, fecha, comida, *, ...)
l282  def _trae_dato(fila) -> bool:
l283      """Si esa entrada aporta energia al total. *** **Sin dato no es cero**: es que no se sabe. ***"""
l287  *** def _cobertura(filas, columna, total) -> dict: ***
l288      """Cuantas entradas traen ESE nutriente, de cuantas hay. *** La cobertura es POR NUTRIENTE. ***"""
l289      con_dato = sum(1 for f in filas if f[columna] is not None)
l290      return {"con_dato": con_dato, "total": total, "completa": con_dato == total and total > 0}
l293  def dia(con, propietario, fecha) -> dict:
l294      """El dia entero **de quien pregunta**: entradas, subtotal conocido y lo que no se sabe.
l296      *** El subtotal se llama `conocido` Y NO `total` A PROPOSITO. *** Y `completo` es la cobertura energetica"""
l307      def suma(columna: str) -> float | None:
l319-321      "kcal": ..., "proteinas_g": ..., "grasas_g": ..., "hidratos_g": ...
l323-325  # *** **La cobertura, por nutriente.** *** Sin esto, una entrada con proteina y sin energia perderia su
          # proteina en el subtotal, o peor: *** se leeria como que el dia esta cubierto. ***
l335  def rango(con, propietario, desde, hasta) -> list[dict]:
l339      sum(CASE WHEN kcal IS NOT NULL THEN 1 ELSE 0 END) AS con_dato
l346      "*** kcal_conocida ***": round(...) if f["con_dato"] else None,
l348      "*** completo ***": f["con_dato"] == f["entradas"] and f["entradas"] > 0
```

## 2. *** Y son las CUATRO piezas que la prevision necesita, y las cuatro estan ***

```
*** 1) DE UNA FICHA A UNA ENTRADA ***  -> *** `de_ficha(producto, gramos)` *** ✓ *
   *** -> o sea: **nutricion del producto + gramos -> una entrada con sus nutrientes** *
   *** -> y **es exactamente el paso 5 de la prevision** (escalar por cantidad)*

*** 2) LA SUMA, CON `None` CUANDO NO SE SABE ***  -> *`suma(columna) -> float | None`* ✓
   *** -> y **no devuelve 0**: *devuelve **`None`** *-- *«**sin dato no es cero**: *es que no se sabe»*

*** 3) LA COBERTURA, POR NUTRIENTE ***  -> *** `_cobertura(filas, columna, total)` *** ✓
   *** -> y devuelve `{con_dato, total, completa}` *** -- *y **`completa` exige `total > 0`** *
   *** -> y **el motivo esta escrito**: *«una entrada con proteina y sin energia perderia su proteina en el
   subtotal, *o peor: **se leeria como que el dia esta cubierto**»*

*** 4) Y EL NOMBRE CORRECTO DEL SUBTOTAL ***  -> *** `conocido`, Y NO `total`, A PROPOSITO *** ✓✓✓
   *** -> y **es la doctrina en un nombre de campo**: *«**conocido**» **no promete completitud**, *
   *y «**total**» **si** -- *y **por eso el campo se llama como se llama.** *
```

> *** O sea: *** *** **el ultimo paso de la prevision esta hecho, probado y con sus motivos escritos** *** -- *
> *y **en el diario**, *que es **donde se sumaba lo consumido.** *
>
> *** Y **eso significa que la prevision puede REUTILIZARLO** *** *-- *y **es lo correcto**: *
> *porque **la prevision y el consumo tienen que sumar IGUAL**, *o **los dos numeros no serian comparables** --
> *y **`Tendencias.tsx` los pone en la misma grafica.** *

## 3. *** Y por eso lo que falta de B08 se reduce a UNA pieza ***

```
*** LA PREVISION, paso a paso, y su estado: ***
  1. las recetas del plan          -> *** HECHO *** *(`GET /api/recetas/plan`: `comensales`, `version`)*
  2. y sus ingredientes, escalados -> *** HECHO *** *(`core/recetas.py:134 escala` + «las dos cifras»)*
  3. *** de la linea a un PRODUCTO *** -> *** FALTA: es el unico hueco *** ⚠️
     *y el sitio para la eleccion existe (`lista_linea`: `cadena_elegida`, `autorizado`, `autorizado_producto`)*
  4. y del producto a nutrientes   -> *** HECHO *** *(`catalogo.producto(id)`, `de_ficha(producto, gramos)`)*
  5. y escalar por cantidad        -> *** HECHO *** *(`de_ficha` toma `gramos`)*
  6. *** y sumar CON COBERTURA ***   -> *** HECHO: `suma()`, `_cobertura()`, `conocido`, `completo` *** ✓
  *** -> o sea: CINCO DE SEIS PASOS ESTAN HECHOS, y el que falta es uno. *** *
```

> *** Y **es un resultado grande, y se dice sin exagerar**: *** *** **la prevision no hay que construirla
> entera**; *hay que **resolver un enlace** *y **encadenar piezas que ya existen.** *
>
> *** Y **el paso 3 es el que el encargo protege**: *** *«**un articulo elegido solo admite alternativas
> autorizadas**» -- *o sea: *el paso 3 **no se puede automatizar del todo**, *porque **la cadena la elige la
> persona.** *
>
> *** Y **eso hace que la prevision tenga, por diseno, dos partes**: ***
> ```
> *** lo que se puede resolver solo ***  -> *la linea que coincide con un producto (EXACTO / PROBABLE)*
> *** y lo que necesita a la persona ***   -> *ALTERNATIVA, que se OFRECE y se AUTORIZA*
> *** y lo que no se sabe ***              -> *** ABSTIENE -> `sin_dato` CON SU NOMBRE ***
> ```

## 4. Y la conclusion de la ronda, y del paquete

```
*** B08 · la vista de previstos ***
  *** lo registrado ***   -> *HECHO (diario, cobertura, `conocido`/`completo`, `kcal_conocida`, rango)*
  *** el ultimo paso ***  -> *** HECHO: `suma` + `_cobertura` + `de_ficha`, con sus motivos escritos ***
  *** y lo que falta ***  -> *** el paso 3: de la linea al producto *** *
  *** y su forma ***      -> *un encadenamiento: `tokens`/`trigramas` -> `parecido` -> `decide` -> veredicto*
  *** y su vocabulario *** -> *** los CINCO veredictos, con `ABSTIENE` = «resultado valido y no un fallo» ***
```

> *** Y **nada de esto se declara hecho**: *** *la **vista de previstos NO existe** (medido en cuatro vias), *
> *y **lo que se ha hecho es localizar exactamente que falta** *-- *que es **un paso de seis.** *
