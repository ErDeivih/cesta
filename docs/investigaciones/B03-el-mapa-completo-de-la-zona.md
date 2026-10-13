# B03 · **El mapa completo**: la zona entra en la columna `grupo`, y se calcula en `emparejar`

*(13 de octubre de 2026. **El ultimo eslabon, y con el se cierra el mapa del cambio.**)*

## 1. Lo que se leyo, y lo que aclara

`core/grupos_ids.py:46-101`, entero:

```python
def estabiliza(nuevos: pl.DataFrame, anteriores) -> pl.DataFrame:
    \"\"\"`nuevos` (columnas `clave` y `grupo`) con su `grupo_id` estable.\"\"\"
    ...
    return nuevos.with_columns(
        pl.col(\"grupo\").replace_strict(mapa, default=None, return_dtype=pl.Int32)
        .alias(\"grupo_id\"))

def tabla_de(filas: list[dict], grupo_id: pl.Series) -> pl.DataFrame:
    \"\"\"La tabla que se guarda para la pasada de manana: `clave` y `grupo_id`.\"\"\"
    return pl.DataFrame({
        COLUMNA_CLAVE: [clave_de(f[\"fuente\"], str(f[\"id_fuente\"])) for f in filas],
        \"grupo_id\": grupo_id.cast(pl.Int32),
    })
```

> **Y de ahi salen dos hechos que cierran el mapa:**
>
>   1. **`nuevos` trae una columna `grupo`** -- ***que es la identidad del grupo*** --, **y `estabiliza` **no
>      la calcula: la recibe**.** *Su trabajo es **asignarle un numero estable**, heredado de ayer o nuevo.*
>   2. **Y `tabla_de` guarda `(clave, grupo_id)` por producto** -- *o sea, **lo que se conserva para manana es
>      el numero del grupo**, no como se formo.*

**Asi que `grupos_ids.py` no es donde entra la zona.** *Es donde el grupo **recibe su numero**.*

## 2. Donde esta el grupo, entonces

**La columna `grupo` se calcula en `projects/cesta/emparejar.py`:**

```
269:  def grupos_de(enlaces_: list[tuple[int, int, float, str]], filas: list[dict]) -> list[int]:
296:  def composicion(filas: list[dict], ingredientes: dict, ...
...
632:  write_parquet_file(grupos_ids.tabla_de(filas, estable[\"grupo_id\"]), ...)
```

> **`grupos_de(...)` devuelve `list[int]`** -- *la identidad del grupo de cada fila.* **Y ahi es donde la zona
> tiene que entrar**: *dos precios del mismo producto en zonas distintas **tienen que salir con `grupo`
> distinto**.*
>
> *Y `estabiliza` hara el resto **sin enterarse**: les asignara numeros estables, como a cualquier otro grupo.*

## 3. Y hay una tercera pieza, que es la que hace que la zona sobreviva al dia siguiente

**`tabla_de` guarda `(clave, grupo_id)`.** *Y `clave` es `fuente:id_fuente` -- **el producto, sin zona**.*

> **Asi que manana, `anteriores` no sabra de que zona era cada grupo.** *Y eso importa: **la herencia de
> `grupo_id` se hace por `clave`**, y si un producto esta en dos zonas, **tendra dos filas con la misma `clave`
> y distinto `grupo_id`** -- *y el `join` de `estabiliza`...*
>
> **— y ahi esta la pregunta que queda, y es la ultima:** *hoy `clave` es unica por producto; **con dos zonas
> dejaria de serlo**. Y `estabiliza` hace `join` sobre ella.*
>
> *Asi que **o `clave` incluye la zona en ESA tabla** -- *que es distinto de `clave_de`, que es el producto* --,
> **o el `join` tendra que desempatar.** *Y eso **es una medida mas**, la octava: **mirar si el `join` de
> `estabiliza` se rompe con dos filas de la misma `clave`.***

## 4. El mapa del cambio, completo y con las tres piezas separadas

```
NO SE TOCA:   core/grupos_ids.clave_de(fuente, id_fuente)
              -> es el PRODUCTO. Su docstring: «la identidad que YA USA MEDIO PROYECTO».
              -> Es el `producto_id`, y `estabiliza` hace JOIN sobre ella.

SE TOCA (1):  projects/cesta/emparejar.py :: grupos_de(...)
              -> AQUI SE FORMA EL GRUPO. La zona entra aqui: dos zonas, dos `grupo`.

SE TOCA (2):  core/grupos_ids.tabla_de(filas, grupo_id)
              -> GUARDA (clave, grupo_id) PARA MANANA. Y `clave` no lleva zona.
              -> Y de ahi sale LA ULTIMA PREGUNTA: con dos zonas, `clave` deja de ser unica
                 por producto -- y `estabiliza` hace JOIN sobre ella.

NO SE TOCA:   core/grupos_ids.estabiliza(...)
              -> recibe `grupo` y le pone numero. Si (1) esta bien hecho, esto ya funciona.

LA FORMA:     `region` AL FINAL del SELECT de `donde_comprar`  (probado: el error no fue de indices)
EL ATAJO QUE NO VALE: anadir la columna sin tocar la identidad del grupo
```

## 5. Y lo que se ha hecho en esta ronda

**Una lectura, ninguna linea de codigo.** *Y con ella el mapa tiene **las tres piezas separadas**: la que no se
toca, las dos que si, y **la pregunta que queda** -- que es nueva y es la octava medida.*

> *Y esa pregunta **no existia antes de leer esto**.* **Que es exactamente por lo que se lee antes de
> escribir**: *la ronda 65 dijo «no se toca `clave_de`», y **esta dice que `tabla_de` guarda `clave` igual** --
> *o sea que **la misma palabra, `clave`, aparece en dos sitios con dos significados**, y confundirlos seria el
> proximo error.*
