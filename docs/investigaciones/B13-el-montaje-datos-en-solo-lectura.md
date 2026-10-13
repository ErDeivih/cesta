# B13 · **El host monta `data/` en `/datos`, y en SOLO LECTURA** -- y `/app/data` es otro sitio

*(13 de octubre de 2026. **Y explica la diferencia, y ordena todo lo que se ha medido.**)*

## 1. La comprobacion, y su respuesta

```
$ docker inspect cesta-api-1 --format "{{json .Mounts}}"

[{"Type":"bind",
  "Source":"*** F:\\aprendizaje\\scrap\\data ***",
  "Destination":"*** /datos ***",
  "Mode":"*** ro ***",
  "RW":*** false ***,
  "Propagation":"rprivate"}]
```

> *** O sea: *** *** **el `data/` del host esta montado, pero en `/datos`** *** -- *y **NO en `/app/data`.** *
>
> *** Y **esta en modo `ro`** *** -- *o sea: *** *** **SOLO LECTURA.** *** *
>
> *** Y **`RW: false`** lo dice por segunda vez, *y **el `Mode: "ro"` por primera**: *los dos coinciden.*

## 2. Y **eso explica la diferencia** que no se entendia

```
*** EL HOST: *** `F:\aprendizaje\scrap\data\recetas.sqlite`  -> *** 42 recetas, 42 del plan ***  *-- y **es el que B13 midio** *
*** EL CONTENEDOR: *** `/app/data/recetas.sqlite`            -> *** 2 recetas (las mias), 0 del plan ***
   *** -> y `/app/data` NO es el `data/` del host: es OTRA COSA. *** *
```

> *** O sea: *** *** **hay DOS `recetas.sqlite`** *** -- *uno **en el host**, *y **otro dentro del contenedor.**
> *Y **la API sirve el suyo**, *que **empezo vacio.** *
>
> *** Y **la explicacion del montaje es correcta y deliberada**: *** *** `/datos` es **`ro`** porque **el
> contenedor no debe escribir el crudo** -- *eso lo hace **la ingesta, en el host.** *
>
> *** Pero **implica una consecuencia que hay que decir**: *** *** **lo que la web sirve NO son las 42 recetas del
> host.** *Sirve **las suyas**, *y **las del host estan ahi al lado, en `/datos`, y la API no las usa para eso.** *

## 3. Y **lo que esto significa para los dos puentes**, que es lo que importa

```
*** LOS DOS PUENTES FUNCIONAN: ***  *la previa de la receta dio `300.0 g`, `nota: ""`, `clave: tomate|kg` *
   -> *o sea: **el puente esta probado**, *y **con datos de verdad** *-- **en la base del contenedor.** *

*** Y EL PLAN ESTA VACIO EN EL CONtenedor ***  *-- *y **por eso la previa del plan no tenia que mirar** *
   -> *y **no es un fallo del plan: es que `plan` tiene 0 filas ahi.** *
   -> *** y en el host tiene 42 *** *-- *y **son de la base del host**, *que **la API no usa.** *
```

> *** O sea: **el puente `plan→lista` se puede probar** *** -- *pero **hay que planificar una receta primero**,
> *en **la base del contenedor**, *que es **la que la API escribe.** *
>
> *** Y **`/datos` en `ro` no estorba**: *el plan y las recetas **van a `/app/data`**, *y **no a `/datos`.** *
> *Asi que **la operacion es posible** -- *y **`ro` protege justo lo que hay que proteger: el crudo.** *

## 4. Y **el hallazgo se declara con su alcance exacto**

```
*** LO QUE ESTA MEDIDO: ***
  1. *el host monta `F:\aprendizaje\scrap\data` en *** `/datos` ***, y con *** `Mode: "ro"` / `RW: false` *** *
  2. *y `/app/data/recetas.sqlite` es *** otro fichero ***, *y **el que la API escribe** *
  3. *y por eso `plan` esta vacio en el contenedor y tiene 42 en el host*

*** LO QUE NO SE DECLARA: ***
  *** no se declara «la web sirve datos equivocados» ***  *-- *porque **no se ha mirado** **que deberia servir**:
  *si **el diseno es que la API tenga su propio estado**, *entonces **esta bien**; *
  *y si **deberia leer el del host**, *entonces **hay una diferencia**, *y **el `ro` impide que la escriba** *
  *** -> y las dos cosas son distintas, y la distincion esta en `docker-compose.yml`, que es donde se decide.** *
```

> *** Y **la comprobacion es una lectura**: *** *`docker-compose.yml`, *y **su bloque de `cesta-api`**, *con **los
> dos montajes: `/datos` y lo que haya para `/app/data`.** *
>
> *** Y **hasta entonces NO se declara fallo** *** -- *porque **puede ser el diseno**, *y **«no lo se» es una
> respuesta valida**, *y **es la que toca.** *

## 5. Y el estado de B13, con los tres puentes localizados y uno probado

```
RECORRIDO 5 · *** tu restriccion ***
  *** el puente de RECETA esta PROBADO: *** *`300.0 g`, `unidad: "g"`, `nota: ""`, `clave: "tomate|kg"` en las dos*
     *** -> y las dos se consolidan a `400 g`, y ninguna se descarta. *** *
  *** el puente del PLAN tiene sus DOS rutas (`GET` y `POST` `desde-el-plan`), ***
     *y **necesita una lista y algo planeado** -- *y **la base del contenedor tiene las dos cosas vacias.** *
  *** y hay un TERCER puente: *** `/api/listas/{lista_id}/desde-la-compra` *** -- *y **el encargo nombra dos.** *
```

> *** Y **`main.py:1608` dice que la consolidacion del plan «es la misma que la del otro puente»** *** -- *y
> **ahora se puede comprobar**, *planificando una receta en **la base del contenedor.** *
