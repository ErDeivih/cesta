# B08 · **`de_ficha` ya resuelve el caso dificil**: «nutriente a nutriente, no en bloque»

*(13 de octubre de 2026. **Y es, literalmente, el caso que el plan pide aceptar.**)*

## 1. Las dos firmas, y lo que dicen

```python
# core/diario.py
*** def de_ficha(producto: dict, gramos: float) -> dict: ***
    """*** Los nutrientes de una cantidad, a partir de los valores por 100 g del producto. ***

    *** Se calcula NUTRIENTE A NUTRIENTE, NO EN BLOQUE. *** Si el producto trae kilocalorias pero no
    proteinas, la entrada lleva las kilocalorias y deja las proteinas en `None`: es lo que sabe.
    *** Rellenar con ceros seria afirmar que no lleva proteina, y eso no lo sabemos. ***

    De una cantidad negativa o no finita no se calcula nada: son las mismas reglas que `apunta` comprueba,
    y aqui se paran antes."""

# plataforma/api/catalogo.py
*** def producto(producto_id: str) -> dict | None: ***
    fuente, _, id_fuente = producto_id.partition(":")
    # ... FROM grupos WHERE fuente = ? AND id_fuente = ?
    *** # y devuelve None si no esta ***
```

## 2. *** Y `de_ficha` es **exactamente** el caso que B08 pide aceptar ***

> *** El criterio de B08 dice: ***
> > *** «Aceptar *** R1=270, media=135, AUSENCIA DE ENERGIA CON PROTEINA CONOCIDA ***, idempotencia, recarga y
> > aislamiento A/B» ***
>
> *** Y **`de_ficha` dice**: *** *** «si el producto trae kilocalorias pero no proteinas, la entrada lleva
> *** las kilocalorias y deja las proteinas en `None` ***». *
>
> *** O sea: *** *** **el caso mas dificil de la aceptacion de B08 ya tiene codigo, y con su motivo
> escrito** *** -- *y **el motivo es la doctrina**: *** *** «rellenar con ceros seria afirmar que no lleva
> proteina, y eso no lo sabemos.» *** *
>
> *** Y **falta el simetrico**, *y es el que el plan nombra: *«**ausencia de ENERGIA con proteina
> conocida**» -- *o sea: **kcal `None` y proteina con valor.** *
> *** Y **`de_ficha` tambien lo da**, *porque **calcula nutriente a nutriente**: *si el producto **no trae
> kcal pero si proteina**, *la entrada **lleva la proteina y deja la energia en `None`.** *
> *** -> **el mismo mecanismo, en los dos sentidos.** *

## 3. Y **lo que esto cambia en la especificacion**: nada, y eso es buena senal

```
*** LA ESPECIFICACION DECIA: ***
  paso 4 -> *`catalogo.producto(id)` + `diario.de_ficha(producto, gramos)`* ✓ *** y la firma es esa *** *
  paso 6 -> *`diario.resumen(filas)`*                                 ✓ *** y ya esta extraida (`d50a2c0`) *** *
*** Y LA SALIDA: ***
  *`cobertura` POR NUTRIENTE* -> *y **`de_ficha` la hace posible** *-- *porque **cada nutriente puede ser
  `None` por separado.** *
  *** -> o sea: sin `de_ficha` nutriente a nutriente, la cobertura por nutriente seria **un adorno**;
     *y con el, **es la unica forma de no mentir.** *
```

> *** O sea: *** *** **la especificacion no cambio al encontrar las firmas**, *y **eso es la senal de que se
> escribio sobre el proyecto y no sobre una idea.** *
>
> *** Y **`catalogo.producto(id) -> dict | None`** *** *-- *y **el `None` esta previsto**: *
> *si **el producto no esta**, **no hay ficha**, *y **la linea va a `sin_dato`** *-- *y **no se inventa.** *

## 4. Y el estado, con **todo lo que hace falta para escribir `prevision` ya leido**

```
*** LO QUE SE SABE YA, PARA ESCRIBIRLA: ***
  *** el fichero ***     -> `plataforma/api/recetas.py` (`rutas = APIRouter(prefix="/api/recetas")`, `l21`)*
  *** el patron ***      -> `con = _con()` · `try: ... finally: con.close()`  *(el de `plan`, `l107`)*
  *** los imports ***    -> `from core import importar_receta, recetas` (`l17`) *-- y **hay que anadir `diario`***
  *** el plan ***        -> `recetas.plan(con, usuario["id"], desde, hasta)` *
  *** la receta ***      -> `recetas.leer(con, propietario, rid)` *-- y **devuelve los ingredientes ESCALADOS***
  *** el producto ***    -> `catalogo.producto(id) -> dict | None` *
  *** la conversion ***  -> `diario.de_ficha(producto, gramos) -> dict` *-- **nutriente a nutriente***
  *** y la suma ***      -> `diario.resumen(filas) -> {conocido, cobertura, completo}` *-- **ya extraida***
```

> *** Y **queda UNA cosa por decidir**, *y es la del paso 3: *** *** de donde sale **la cadena** *** *-- *
> *porque `cesta.py:98` resuelve **«en una cadena dada»**. *
>
> *** Y **la respuesta esta en `lista_linea`** *** (`cadena_elegida`), *y **eso obliga a que la prevision
> tenga una lista** -- *o a que **la cadena sea un parametro explicito.** *Y **es la decision que la
> especificacion ya dejo abierta**: *`cadena=None` -> *se usa la de la lista, *y **si no hay, `ABSTIENE`.** *
