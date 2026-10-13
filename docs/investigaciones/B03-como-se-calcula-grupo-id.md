# B03 · **Como se calcula `grupo_id`**: hay un modulo que los asigna, y son estables entre dias

*(13 de octubre de 2026. **La ultima medida del relevo, y la que decide si el cambio es una linea o un
diseno.**)*

## 1. Lo que se ha medido

```
projects/cesta/emparejar.py:8      «grupos.parquet -- UNA FILA POR PRODUCTO con grupo_id, calidad y su origen»
projects/cesta/emparejar.py:263    lee `[grupos_ids.COLUMNA_CLAVE, "grupo_id"]` de ayer
projects/cesta/emparejar.py:581    de_ayer = set(anteriores["grupo_id"].cast(pl.Int32).to_list())
projects/cesta/emparejar.py:582    heredados = sum(1 for g in estable["grupo_id"] if g in de_ayer)
projects/cesta/emparejar.py:614    pl.Series("grupo_id", grupo, dtype=pl.Int32)
projects/cesta/emparejar.py:632    write_parquet_file(grupos_ids.tabla_de(filas, estable["grupo_id"]), ...)
```

**Y de ahi salen tres hechos, y los tres importan:**

  1. **Hay un modulo `grupos_ids`** *-- con `COLUMNA_CLAVE` y `tabla_de` -- **que es quien asigna y conserva
     los identificadores.** *No es un `hash` suelto en `emparejar.py`: es una pieza propia.*
  2. **El grano esta escrito**: *«**una fila por producto** con `grupo_id`, calidad y su origen»*.
  3. **Y los ids SE HEREDAN DE AYER.** *`de_ayer`, `heredados`.* **O sea que un `grupo_id` no se recalcula cada
     dia: se conserva** -- *y por eso un producto mantiene su identidad a lo largo del tiempo.*

## 2. Y eso cambia la forma del cambio, para bien

**El miedo era**: *«si `grupo_id` sale de agrupar por nombre, meter la zona dentro obliga a decidir donde
entra»* -- *o sea, un diseno.*

**Y lo que hay es mejor**: *hay **una pieza dedicada** (`grupos_ids`) **cuya responsabilidad es exactamente
esa** -- asignar y conservar identidades.* **Asi que meter la zona en la identidad es un cambio EN ESA PIEZA**,
*no una cirugia por todo el emparejador.*

> **Y la herencia de ayer anade una condicion que hay que respetar**: *si la zona entra en la clave, **un cambio
> de CP cambiaria los `grupo_id` de golpe*** -- *y los de ayer ya no casarian.*
>
> *Eso **no es un problema hoy** -- solo Lidl declara zona, y es una sola --, pero **si es la pregunta que hay
> que contestar escribiendo el codigo**:* **que pasa con los grupos heredados cuando la zona cambia.**
> *Y la respuesta probable esta en el propio modulo: `COLUMNA_CLAVE` y `tabla_de` ya saben conservar
> identidades; lo que hay que decidir es **si la zona forma parte de esa clave o es un atributo que viaja con
> ella.***

## 3. Asi que el relevo de B03 queda completo, y con una decision escrita

```
LA ZONA EN LA COMPARACION   PENDIENTE -- y ya no falta ninguna medida
  el fichero:      projects/cesta/emparejar.py (35,6 KB), linea 632
  la pieza:        grupos_ids  -- el modulo que asigna y conserva los ids
  el grano:        «una fila por producto», escrito en la linea 8
  la identidad:    la zona entra en la clave ... o viaja como atributo
  y la pregunta:   QUE PASA CON LOS GRUPOS HEREDADOS CUANDO LA ZONA CAMBIA
  la forma:        al final del SELECT en donde_comprar (probado, ronda 55)
  y el atajo que NO vale: anadir la columna sin tocar la identidad
```

**Seis medidas, ninguna suposicion, y un intento fallido documentado.** *Eso es lo que hay que leer antes de
escribir la primera linea -- y esta escrito.*

## 4. Y lo que se ha hecho en esta ronda

**Una medida, ninguna linea de codigo.** *Y con ella **deja de faltar informacion**: lo que falta es una
decision de diseno y su codigo.*

> *Que es un estado mucho mejor que el de la ronda 48, cuando esto se aparco porque «la consulta devuelve
> tuplas posicionales».* **Aquello era una hipotesis, y era falsa.** *Ahora hay seis hechos medidos y un
> intento fallido que dice por donde no se va.*
