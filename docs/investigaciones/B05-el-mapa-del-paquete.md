# B05 · **El mapa del paquete** -- el criterio, y donde mirar

*(13 de octubre de 2026. **Lo siguiente por el plan. Y esta vez, la leccion de B02 aplicada DESDE EL PRINCIPIO:
primero se mira que hay, y solo despues se concluye.**)*

## 1. El criterio, literal

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:261`:

> **B05 · Idempotencia y consistencia entre almacenes**
>
> *Operaciones con **recibo y huella del contenido**; **misma clave con contenido distinto produce conflicto, no
> éxito ficticio**. **Concurrencia y caída tras insertar media lista.** **Reservas de despensa** y **actualización
> del plan con cálculo incremental**: *editar un menú **no borra líneas manuales de compra ni duplica todas las
> necesidades**.* **Aceptar dos pestañas, versiones concurrentes, recuperación y destino distinto.**

## 2. Y desglosado, son seis cosas

```
1) RECIBO Y HUELLA DEL CONTENIDO        -- cada operacion deja recibo, y con la huella de lo que escribio
2) CONFLICTO, NO EXITO FICTICIO         -- misma clave + contenido distinto = CONFLICTO
                                           (*** no «ya estaba, no hago nada» ***)
3) CONCURRENCIA Y CAIDA A MITAD         -- dos pestañas · versiones concurrentes · caida tras
                                           insertar MEDIA lista
4) RESERVAS DE DESPENSA                 -- y su actualizacion
5) CALCULO INCREMENTAL DEL PLAN         -- editar un menu NO borra las lineas manuales de compra
                                           NI duplica todas las necesidades
6) DESTINO DISTINTO                     -- (ya hay trabajo de B04 en elegir lista destino)
```

> **Y la (2) es la que tiene mas fondo**: *«misma clave con contenido distinto produce **conflicto**, no **éxito
> ficticio**».* *O sea: **el sistema no puede decir «ya estaba» cuando lo que estaba es OTRA COSA**.*
>
> *** Que es, palabra por palabra, el defecto que B04 corrigio en otro sitio: **«se descarta la segunda receta
> como repetida»** -- *que es exactamente confundir «ya estaba» con «da igual».*

## 3. Y donde mirar, medido -- **doce ficheros hablan de esto**

```
$ git grep -ln "idempot|recibo|huella|fingerprint|dedup" -- core/ plataforma/api/ projects/cesta/

  core/diario.py          core/equivalencias.py    core/fetch.py
  core/manifiesto.py      core/publicacion.py      core/traspaso.py
  plataforma/api/almacen.py    plataforma/api/catalogo.py    plataforma/api/main.py
  plataforma/api/recetas.py    projects/cesta/avisos.py
  projects/cesta/collectors/alcampo.py
```

> **Y ya se pueden decir tres cosas sin suponer, solo por los nombres:**
>
>   - **`core/manifiesto.py` y `core/publicacion.py`** *-- *que son **el recibo de una publicacion** (B03 trabajo con
>     versiones publicadas, `data/gold/v<timestamp>/`);*
>   - **`plataforma/api/almacen.py`** *-- *que es **el almacen de la API**, donde tiene que vivir la idempotencia de
>     las listas;*
>   - **`core/traspaso.py`** *-- *que suena a **pasar cosas de un almacen a otro**, que es literalmente el titulo
>     del paquete: «consistencia **entre almacenes**».*
>
> *** Y NADA MAS SE DICE: no se ha abierto ninguno. ***

## 4. Y lo que NO se va a repetir de B02

**B02 costo diez rondas y nueve correcciones, y todas venian de lo mismo: concluir antes de mirar.**

```
LO QUE SE HARA EN B05, EN ESTE ORDEN:
  1) ls de la zona (hecho: los doce ficheros)
  2) LEER ENTEROS los que importan: almacen.py, manifiesto.py, traspaso.py, diario.py
  3) COMPARAR los que hacen lo mismo -- la herramienta que encontro que Lidl era el
     unico de los seis sin log_run, y que tests/fixtures/ sobraba
  4) y grep al final, con los nombres del codigo
  5) Y NO DECIR NUNCA: «no existe», «y nada mas», «hay que construirlo», «ya esta»

Y el primer sitio, por el nombre y por el titulo del paquete: `core/traspaso.py`
  -- «consistencia ENTRE ALMACENES» es el titulo, y `traspaso` es su nombre.
```

> **Y hay una pista de la propia sesion, que vale mas que el mapa**: *el fallo latente de B03 -- **los tres
> desempaquetados que rompia el `region`** -- **estuvo veinte rondas invisible porque nadie comparo lo que la
> consulta devolvia con lo que el codigo esperaba**.*
>
> *** B05 es exactamente eso, pero a proposito: **misma clave, contenido distinto** -- *que es la version de datos
> del mismo problema.* *** Y la suite ya tiene ensayos de esto (`test_runlog.py`, `test_g03_*`). ***

## 5. Y lo que se deja hecho

**El criterio desglosado, los doce ficheros localizados, el orden de trabajo escrito, y la primera parada señalada
(`core/traspaso.py`).** *Sin abrir ninguno, y sin una sola conclusion sobre lo que hay dentro.*
