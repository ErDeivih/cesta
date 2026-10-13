# B03 · **La octava medida, hecha**: `estabiliza` no revienta con dos zonas -- **y eso es peor**

*(13 de octubre de 2026. **Se le dio de comer el caso de dos zonas, y la respuesta cambia el plan.**)*

## 1. El experimento

*No hizo falta tocar nada: `estabiliza(nuevos, anteriores)` es una funcion pura y se le puede dar de comer lo
que se quiera.*

```python
# A) el caso normal: una clave por producto
hoy  = {"clave": ["lidl:1", "lidl:2", "dia:9"], "grupo": [10, 10, 20]}
ayer = {"clave": ["lidl:1", "lidl:2", "dia:9"], "grupo_id": [7, 7, 3]}

# B) DOS ZONAS: el mismo producto, dos grupos distintos
hoy2 = {"clave": ["lidl:1", "lidl:1", "lidl:2"], "grupo": [10, 11, 11]}
```

## 2. Y el resultado

```
A) caso normal       clave   grupo   grupo_id
                     dia:9   20      3
                     lidl:1  10      7        <- hereda
                     lidl:2  10      7        <- hereda

B) DOS ZONAS         clave   grupo   grupo_id
                     lidl:1  10      8        <- *** NO HEREDA: id NUEVO ***
                     lidl:1  11      7        <- este si hereda el 7
                     lidl:2  11      7
```

> **`estabiliza` no revienta.** *No hay excepcion, no hay `null`, no hay perdida de filas.* **Y por eso mismo
> hay que mirarlo despacio: **el fallo no da error.***

## 3. Y lo que de verdad pasa, que es peor que un fallo

**`grupo 10` -- que existia ayer, dentro del grupo 7 -- recibe hoy un id NUEVO (el 8).** *Y `grupo 11` se queda
con el 7.*

> **O sea: de los dos grupos que comparten clave, **uno conserva el id de ayer y el otro no** -- y **cual de los
> dos es depende del desempate**.*
>
> *El desempate esta escrito y es determinista (`sort(["miembros", "grupo_viejo", "grupo_nuevo"],
> descending=[True, False, False])`, con su comentario sobre el PC y el contenedor).* **Pero es determinista
> sobre un empate que, con dos zonas, es arbitrario**: *los dos grupos solapan **igual** con el de ayer --
> `miembros` = 1 cada uno --, asi que gana el que tenga el `grupo_nuevo` mas bajo.*
>
> **Y eso significa que `grupo_id` puede CAMBIAR de un dia para otro** *para un (producto, zona) concreto* --
> *que es **exactamente lo contrario de lo que `estabiliza` existe para hacer**.*

## 4. Y por que esto cambia el plan, en vez de solo anadir un aviso

**La ronda 66 dijo**: *«o `clave` incluye la zona en esa tabla, o el `join` tendra que desempatar».*

**Y la medida dice que el `join` **ya desempata** -- y que desempatar **no basta**.** ✗

> **Porque el problema no es que el `join` sea ambiguo: es que **la clave con la que se hereda no distingue lo
> que hay que heredar**.** *Con `clave = fuente:id_fuente`, dos zonas del mismo producto **son la misma clave**,
> y `estabiliza` **no tiene forma de saber cual de los dos grupos de hoy es el de ayer**.*
>
> **Asi que la clave de la tabla que se guarda (`tabla_de`) TIENE que incluir la zona.** *No como desempate:
> **como parte de la identidad que se hereda**.*
>
> *Y eso **no es `clave_de`** -- *que es el producto, y no se toca.* **Es la `clave` de `tabla_de`, que es otra
> cosa con el mismo nombre.** *Que es justo lo que la ronda 66 avisaba: **la misma palabra en dos sitios.***

## 5. Y las tres piezas del mapa, ahora con la tercera resuelta

```
NO SE TOCA:   core/grupos_ids.clave_de(fuente, id_fuente)
              -> es el PRODUCTO. Su docstring: «la identidad que YA USA MEDIO PROYECTO».

SE TOCA (1):  projects/cesta/emparejar.py :: grupos_de(...)
              -> AQUI SE FORMA EL GRUPO. La zona entra aqui: dos zonas, dos `grupo`.

SE TOCA (2):  core/grupos_ids.tabla_de(filas, grupo_id)   *** Y AHORA SE SABE POR QUE ***
              -> guarda (clave, grupo_id) para manana, y `clave` NO lleva zona.
              -> MEDIDO: con dos zonas, `estabiliza` da a uno de los dos grupos un id NUEVO,
                 y CUAL de los dos depende del desempate -> `grupo_id` puede cambiar de un dia
                 para otro, que es lo contrario de lo que `estabiliza` existe para hacer.
              -> ASI QUE LA CLAVE DE ESTA TABLA TIENE QUE INCLUIR LA ZONA. No como desempate:
                 como parte de la identidad que se hereda.

NO SE TOCA:   core/grupos_ids.estabiliza(...)
              -> recibe `grupo` y le pone numero. Con la clave bien, ya funciona.

LA FORMA:     `region` AL FINAL del SELECT de `donde_comprar`  (probado: el error no fue de indices)
```

## 6. Y lo que deja esta ronda, que es una leccion y no un dato

**El fallo que buscaba era «¿revienta?». Y la respuesta fue «no».** *Y ese «no» era la respuesta **menos util**:
habria cerrado la pregunta **dejando el fallo dentro**, porque **un `grupo_id` que cambia de un dia para otro no
da error -- da historicos partidos**.*

> **Asi que la pregunta estaba mal hecha**, y se ve al escribir el resultado: *«¿se rompe el `join`?» **no es la
> pregunta**; la pregunta es **«¿hereda bien?»**.* ***Y un `join` que no revienta puede estar heredando mal.***
>
> *Que es la misma forma de todo este paquete: **el fallo silencioso es el que hay que buscar** --* y esta vez
> se encontro **antes** de escribir el codigo, y **midiendo en vez de suponiendo**.
