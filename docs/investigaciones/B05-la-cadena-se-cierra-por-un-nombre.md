# B05 · **La cadena se cierra**: `traspaso.id_de_linea` -> `almacen.anade_linea(linea_id=...)`

*(13 de octubre de 2026. **Cuarta ronda de B05. Y los dos ficheros encajan por un nombre.**)*

## 1. `almacen.py` por sus nombres

```
plataforma/api/almacen.py -- 1230 lineas
docstring: «PostgreSQL: cuentas, listas y favoritos. LO UNICO QUE SE ESCRIBE.»

  l10:  import hashlib                                       <- HUELLAS
  l51:  class UsuarioRepetido(RuntimeError)
  l55:  class DemasiadasAltas(RuntimeError)
  l137: def migra()
  l368: def anade_linea(lista_id, usuario_id, linea_id, nombre, ...)   <- *** POR `linea_id` ***
  l405: def cambia_linea(lista_id, linea_id, usuario_id, *, ...)
  l554: def cierra_compra(lista_id, usuario_id, ...)
```

> **Y el docstring dice algo que importa para B05**: *«PostgreSQL: cuentas, listas y favoritos. **Lo unico que se
> escribe**».*
>
> *** O sea: **hay un solo almacen que se escribe**, y los demas (bronze, silver, gold, parquet) **se generan**.***
> *Que es exactamente el problema de «**consistencia entre almacenes**»: **uno manda y los otros derivan**.*

## 2. Y la cadena se cierra por un nombre

```
core/traspaso.py:56     def id_de_linea(lista_id, clave) -> str        <- CALCULA el id
core/traspaso.py:89     def pasar_a_lista(...)                         <- y lo usa
plataforma/api/almacen.py:368  def anade_linea(lista_id, usuario_id, linea_id, ...)   <- lo RECIBE
```

> *** `anade_linea` recibe `linea_id` -- y no lo genera.** *
>
> *Asi que **la identidad de la linea la decide quien traspasa, no quien escribe** -- *y **eso es la idempotencia
> entera**: el mismo `linea_id` **pisa** la linea (repetir no duplica), y **otro `linea_id`** -- *de otra semana,
> de otra version -- **crea otra**.*
>
> *** Y `linea_id` **no depende del contenido** de la linea, que es lo que el docstring de `traspaso` razona: **dos
> semanas con los mismos ingredientes producen lineas identicas, y no hay forma de distinguirlas por su
> contenido.***

## 3. Y las dos excepciones dicen donde esta el «conflicto, no exito ficticio»

```
l51:  class UsuarioRepetido(RuntimeError)      <- «ya existe»
l55:  class DemasiadasAltas(RuntimeError)      <- «demasiadas»
```

> **Hay excepciones CON NOMBRE para los dos casos de «esto ya estaba».** *Y eso es lo que el plan pide:*
> **conflicto**, no **exito ficticio** -- *o sea: **se levanta y se dice**, en vez de **devolver «vale» sin haber
> hecho nada**.*
>
> *Y **estan en `almacen.py`**, que es donde se escribe.* *Que es **el sitio correcto**: **la idempotencia se
> decide donde se escribe, no en la pantalla** -- *la misma frase que el docstring de `traspaso` usa para el dueño.*

## 4. Y lo que NO se dice

**No se ha leido el cuerpo de `anade_linea`.** *Asi que **no se dice que sea idempotente**: se dice que **recibe
`linea_id`** y que **hay una excepcion con nombre para «repetido»**.*

```
POR LEER, y no se concluye:
  - el cuerpo de `anade_linea` (l368-405) y de `cambia_linea` (l405-497)
    -> ahi esta si el `linea_id` repetido PISA, IGNORA o LEVANTA
  - `cierra_compra` (l554) -- «caida tras insertar MEDIA lista» puede estar ahi
  - `migra()` (l137) -- el esquema: que restricciones tiene la tabla de lineas
    *** y una restriccion UNIQUE en `linea_id` seria la idempotencia, DICHA POR LA BASE ***
  - y los ensayos de la API (`test_cesta_api.py`, `test_lineas_api.py`, `test_g03_*`)
```

> *** Y el mas informativo de todos es `migra()`: *** *porque **una restriccion `UNIQUE` sobre `linea_id` es la
> idempotencia garantizada por la base** -- *y **eso es lo unico que la sostiene de verdad cuando hay **dos
> pestañas** y **concurrencia**, que es lo que B05 pide.*
>
> *** Porque una comprobacion en Python («¿ya existe?») **tiene una carrera**: *dos peticiones a la vez pueden
> mirar, ver que no, y escribir las dos.* **Una restriccion `UNIQUE` no la tiene.** *** Y eso es exactamente
> «concurrencia», la palabra del criterio. ***
