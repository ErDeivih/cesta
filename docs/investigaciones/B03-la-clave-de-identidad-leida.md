# B03 · **La clave de identidad, leida**: `clave_de(fuente, id_fuente)` -- y no incluye la zona

*(13 de octubre de 2026. **La ultima pieza, leida. Y la decision queda en una firma.**)*

## 1. La pieza, y su API entera

`core/grupos_ids.py`:

```python
38:  COLUMNA_CLAVE = "clave"
41:  def clave_de(fuente: str, id_fuente: str) -> str:
46:  def estabiliza(nuevos: pl.DataFrame, anteriores: pl.DataFrame | None) -> pl.DataFrame
96:  def tabla_de(filas: list[dict], grupo_id: pl.Series) -> pl.DataFrame
```

> **Cuatro cosas, y las cuatro dicen lo que hay que saber:**
>
>   - **`clave_de(fuente, id_fuente)`** -- *la identidad de un producto **son dos cosas: de que cadena es y
>     como se llama alli**.* **Y no incluye la zona.** ✗
>   - **`estabiliza(nuevos, anteriores)`** -- *esta es **la herencia de ayer***, la que hace que un `grupo_id`
>     se conserve.
>   - **`tabla_de(filas, grupo_id)`** -- *adjunta los ids a las filas.*
>   - **`COLUMNA_CLAVE = "clave"`** -- *el nombre de la columna donde vive esa clave.*

## 2. Asi que la decision cabe en una firma

**Y deja de ser «un diseno»:**

```python
def clave_de(fuente: str, id_fuente: str) -> str:            # hoy
def clave_de(fuente: str, id_fuente: str, region: str | None = None) -> str:   # y lo que pide la zona
```

> **Y esa es toda la decision de identidad**: *si la zona **forma parte de la clave** -- *tercer parametro* -- o
> **viaja como atributo** y la clave se queda como esta.*
>
> **Y la diferencia se puede decir en una frase**: *con la zona en la clave, **el mismo producto en dos zonas
> son dos entradas distintas** -- que es lo que hay que decidir si se quiere; **sin ella, son la misma** y la
> comparacion tendria que elegir entre dos precios de zonas distintas.*

## 3. Y la pregunta de la herencia, ahora con el nombre exacto

*En la ronda 61 quedo dicha asi:* **«que pasa con los grupos heredados cuando la zona cambia»**.

**Y ahora tiene nombre**: *la herencia vive en **`estabiliza(nuevos, anteriores)`***. *Asi que la pregunta
concreta es:*

> **si la zona entra en la clave y alguien cambia su `SCRAP_CP`, los `nuevos` de hoy tendrian claves que **no
> estan** entre los `anteriores`** -- *y `estabiliza` los trataria como **productos nuevos**.*
>
> *O sea: **un cambio de zona renueva todas las identidades de Lidl de golpe.***

**Y eso hay que decidirlo, no descubrirlo**, *porque tiene dos respuestas legitimas y muy distintas:*

  - **o se acepta** -- *«cambiar de zona es empezar de nuevo en esa cadena»* --, *que es simple y **se dice**;*
  - **o se separa** -- *la clave sigue siendo `(fuente, id_fuente)` y **la zona es un atributo que viaja con el
    grupo*** --, *con lo que un grupo puede tener dos zonas y **hay que decidir que hace la comparacion**.*

> *Y esa es exactamente la misma disyuntiva que la ronda 59 midio para `grupos` -- «la zona entra en el
> `grupo_id`» --, **ahora con un nombre y un fichero**.*

## 4. Y con esto, B03 deja de faltarle informacion

```
LA ZONA EN LA COMPARACION   PENDIENTE -- y ya no falta NADA por medir
  el fichero:      projects/cesta/emparejar.py, linea 632
  la pieza:        core/grupos_ids.py, 4 funciones
  LA DECISION:     clave_de(fuente, id_fuente)  ->  con region o sin ella
  la herencia:     estabiliza(nuevos, anteriores)  -- y un cambio de CP renueva ids
  el grano:        «una fila por producto»
  la forma:        al final del SELECT en donde_comprar (probado, ronda 55)
  y el atajo que NO vale: anadir la columna sin tocar la identidad
```

**Siete medidas, ninguna suposicion, un intento fallido documentado, y la decision reducida a una firma.**

## 5. Y lo que NO se ha hecho, que es lo correcto

**No se ha tocado `clave_de`.** *Y es la tentacion mas fuerte de todo el paquete: **es una firma, y anadir un
parametro opcional con valor por defecto no rompe nada** -- las llamadas de hoy siguen valiendo.*

> **Y precisamente por eso hay que parar**: *el cambio **compila, pasa las pruebas, y no hace nada*** -- *porque
> nadie pasa la zona todavia.* **Seria un `por_que_no_se_compara` mas: una pieza correcta que nadie llama.**
>
> *Lo que hay que escribir antes es **quien la pasa y que hace `estabiliza` con dos zonas**.* **Y eso ya no es
> medir: es decidir, y es una ronda entera.**
