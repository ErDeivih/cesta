# B03 · **Correccion: la zona no entra en `clave_de`, entra en el GRUPO**

*(13 de octubre de 2026. **La decision de la ronda 63 apuntaba a la clave equivocada, y lo dice el docstring de
la funcion.**)*

## 1. Lo que se leyo, y por que cambia el diseño

```python
def clave_de(fuente: str, id_fuente: str) -> str:
    """`dia:147509`. Es la identidad estable que YA USA MEDIO PROYECTO."""
    return f"{fuente}:{id_fuente}"
```

> **«La identidad estable que ya usa medio proyecto.»** *Escrito en su propio docstring.*
>
> *Y es literal*: **es el `producto_id`** -- *las consultas de `donde_comprar` escriben `fuente || ':' ||
> id_fuente` a mano, **que es la misma cadena*** --, *y `estabiliza` **hace `join` sobre ella*** para saber que
> grupo de hoy es cual de ayer.

**Asi que cambiar `clave_de` no es «una firma».** *Es cambiar **el nombre de un producto en todo el proyecto***:
*`producto_id`, los `join`s de `estabiliza`, y cualquier sitio que compare claves.* **Y eso rompe el
emparejamiento entero, no la comparacion de zonas.**

> **La ronda 63 dijo «la zona entra en la clave» y eso sigue siendo verdad.** *Lo que estaba mal es **en cual**:
> `clave_de` es la clave del **producto**, y la zona no es una propiedad del producto.*

## 2. Y entonces, ¿de quien es la zona?

**Un producto ES `fuente:id_fuente`.** *Eso es un hecho sobre el producto: de que cadena es y como se llama
alli.* **Y no cambia porque el precio sea de otra zona.**

**La zona es una propiedad del PRECIO.** *Un mismo producto, en la misma cadena, **tiene un precio en cada
zona**.* *Y por eso la pregunta «¿el mismo producto en dos zonas es uno o dos?» **estaba mal planteada**:*

  - **el PRODUCTO es uno**, *y su clave `fuente:id_fuente` es correcta y no se toca;*
  - **el GRUPO es lo que se compara**, *y ahi es donde la zona tiene que entrar* -- *porque un grupo con dos
    precios de zonas distintas **es lo que la comparacion no puede resolver**.*

> **Y eso encaja con lo medido en la ronda 59**: *«la zona entra en el `grupo_id`»*. *Era correcto.* **Lo que
> sobraba era el paso por `clave_de`.**

## 3. Asi que la decision, corregida y mas pequeña

```
NO SE TOCA:   clave_de(fuente, id_fuente)        -- es el producto, y el producto no tiene zona
SE TOCA:      la clave del GRUPO                  -- y ahi entra la zona
```

*Y el sitio es `estabiliza` / el calculo del `grupo`:* **la clave con la que se agrupa y con la que se hereda
de ayer** -- *las columnas `clave` y `grupo` de `nuevos`, y el `join` con `anteriores`.*

> **Y de paso se aclara lo del cambio de `SCRAP_CP`**: *las identidades **de producto** no se renuevan* -- *el
> producto es el mismo* --, **y lo que se renueva es su agrupacion**, *que es exactamente lo que tiene que
> pasar: **el mismo producto, en otra zona, se compara con otros**.*
>
> *O sea que la consecuencia que en la ronda 63 daba miedo **es mas pequeña y mas precisa de lo que dije**: no
> se renueva «todo Lidl», se reagrupa.*

## 4. Y por que esto importa mas que la correccion en si

**La ronda 63 decia que la decision «ya no es medir, es decidir».** *Y resultó que **todavia faltaba una
medida**: leer el cuerpo de `clave_de` en vez de su firma.*

> *Su firma es `(fuente, id_fuente) -> str`; **su docstring dice que la usa medio proyecto**. Y yo decidi
> mirando la firma.*
>
> **La vigesimosexta, y es la misma forma que las veinticinco anteriores**: *yo supuse por lo que se ve, y **el
> codigo tenia razon por lo que dice dentro.*** *Aqui, por suerte, **antes de tocar nada** -- que es la unica
> diferencia con las otras.*

## 5. Lo que queda, corregido

```
LA ZONA EN LA COMPARACION   PENDIENTE -- con el mapa corregido
  el fichero:      projects/cesta/emparejar.py, linea 632
  la pieza:        core/grupos_ids.py
  NO SE TOCA:      clave_de  -- es el producto, y el producto no tiene zona
  SE TOCA:         la clave del GRUPO  -- en `estabiliza` y en el calculo del grupo
  la forma:        al final del SELECT en donde_comprar (probado, ronda 55)
  y el atajo que NO vale: anadir la columna sin tocar la identidad del grupo
```

*Y la decision de fondo **no cambia**: la zona entra en la identidad **del grupo**. Lo que cambia es **donde esta
esa identidad** -- que no era donde yo la iba a escribir.*
