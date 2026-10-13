# B04 — Unificar los dos puentes: **el hallazgo, y el plan exacto**

*(13 de octubre de 2026. **Se confirma que la unificacion es tractable y se deja escrita, en vez de
empezarla y dejarla a medias.**)*

## 1. El hallazgo: **uno de los dos YA usa el sitio comun**

Se leyo `core/traspaso.py`, y en su linea 132:

```python
previa = previa_compra.previa_de_compra(hallada["ingredientes"] or [])
```

**El puente receta->lista **ya** pasa por `previa_compra`.** *Y por eso sus defectos eran solo de
ESCRITURA* -- *`round(ln.cantidad) or 1` y `None` de nota* --, **no de calculo**: *la consolidacion, los
envases y el sobrante le venian bien desde `previa_compra`.*

**Y `_del_plan` NO pasa por ahi.** *Tiene su propio bucle, con su propio escalado y su propia
consolidacion.* **Por eso era el unico de los dos que no escalaba y que descartaba la segunda receta.**

> **O sea: la unificacion no es «escribir un modulo nuevo». Es **borrar el bucle que sobra** y llamar a lo
> que el otro ya llama.**

## 2. Y la pieza que lo hace directo

`core/previa_compra.previa_de_compra(ingredientes: list[dict]) -> Previa` es **pura** -- *lo dice su propio
docstring: «no escribe, no consulta, no decide por nadie»* --, y:

- **recibe** `texto`, `cantidad`, `unidad`, y opcionalmente `producto_id`, `grupo_id`, y el tamaño del
  envase en `tamano_envase`/`unidad_envase`;
- **consolida por `clave`** (*producto + unidad*), **cuenta los envases enteros** y **calcula el sobrante**;
- **devuelve** `lineas` (`list[LineaDeCompra]`), `sin_cantidad`, `sin_consolidar` y `nota`.

**Y `LineaDeCompra` trae `clave`, `texto`, `producto_id`, `cantidad`, `unidad`, `envases`, `sobrante`,
`unidad_envase` y `de_dondo`.** *Todo lo que la nota necesita.*

## 3. El cambio exacto, en tres sitios

**`_del_plan`** (*`plataforma/api/main.py`, ~1419*):

1. Recorrer el plan como ahora, **acumulando los ingredientes de TODAS las recetas** en una lista, con la
   `cantidad` **ya escalada** por `comensales / raciones` -- *y sin factor si la receta no declara raciones,
   que es lo que hoy hace bien y no hay que perder*;
2. **Una sola llamada**: `previa_compra.previa_de_compra(todos)`;
3. Devolver `list(calculada.lineas)`, `ya` **y la `Previa` entera** -- *porque `sin_cantidad` y
   `sin_consolidar` son informacion que hoy se tira.*

**`previa_del_plan`** (*~1391*) y **`traer_del_plan`** (*~1502*): *hoy leen `uno["nombre"]`,
`uno["cantidad"]`, `uno["producto_id"]`, `uno["grupo_id"]` y `uno["receta"]`, que son las claves **del
diccionario que `_del_plan` inventaba**.* **Con `LineaDeCompra` pasan a ser `ln.texto`, `ln.cantidad`,
`ln.producto_id`, `ln.grupo_id`** *(si existe)* **y `ln.de_dondo`.**

**Y el `insertar` de `traer_del_plan` queda igual que el de `a_la_lista`** -- *una unidad y la nota con la
cantidad, la unidad, los envases y el sobrante* --, **que es literalmente compartir la escritura.**

## 4. Por que NO se ha hecho en esta ronda

**Se empezo, y se paro a proposito.** *El cambio toca tres funciones y sus dos consumidores, y una version
a medias -- con `_del_plan` devolviendo `LineaDeCompra` y los consumidores leyendo diccionarios -- **deja el
puente roto de una forma que las siete pruebas actuales no verian**, porque ellas pasan por `_del_plan`
entero.*

> **Un refactor a medias es peor que uno no empezado**: *el de en medio se queda con dos formas de lo mismo
> y sin pruebas que lo cubran.*

**Lo que si queda**: *el hallazgo de que **uno de los dos ya esta bien** -- y que por tanto esto es borrar
codigo, no escribirlo --, la firma exacta de la pieza compartida, y los tres sitios que hay que tocar.*

## 5. Y lo que hay que hacer antes de tocarlo

**Una prueba que fije el contrato de `_del_plan` con `LineaDeCompra`**, *para que el cambio tenga una red*.
*Las siete que hay hoy afirman el RESULTADO de los puentes, que esta bien y no debe cambiar; **falta una que
afirme la FORMA**.*
