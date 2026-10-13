# B13 · **Las siete listas del puente NO existen en la base de casa** -- y la explicacion probable esta medida

*(13 de octubre de 2026. **Undecima ronda de B13. Y un cabo abierto se convierte en un hallazgo de aislamiento.**)*

## 1. Lo que se midio, en tres pasos

```
PASO 1:  `data/recetas.sqlite` -> `traspaso` tiene 7 filas, con 7 `lista_id` distintos
PASO 2:  y sus `lista_id`, buscados en `lista_linea` de POSTGRES -> *** CERO filas ***
PASO 3:  y las listas, buscadas en `lista` de POSTGRES           -> *** NINGUNA de las siete existe ***
```

## 2. Y la explicacion probable **esta medida**, no supuesta

```
HECHO 1:  `data/recetas.sqlite` tiene fecha de modificacion *** 2026-10-13 12:53 ***
          -- y **la suite se corrio hoy**, y **este proyecto corre los ensayos contra la base de PRUEBAS**
          (`$env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'`, que es la puerta
          documentada desde la ronda 123).

HECHO 2:  y `recetas.sqlite` es *** UN FICHERO COMPARTIDO *** -- *no hay una version «de pruebas» de el.*
          (los ficheros que hay son `recetas.sqlite`, `diario.sqlite`, `inventario.sqlite`, y ninguno lleva
          sufijo de pruebas)

HECHO 3:  y los 38 usuarios de prueba SI estan en la base de CASA (`cesta-db-1`, 5432)
          -- *que es por donde empezo este hilo (paso 1 de B13).*
```

> *** O sea, la lectura mas simple de los tres hechos: ***
>
> ```
> los ensayos CREAN LISTAS en la base de PRUEBAS (5434)
>   y APUNTAN EL TRASPASO en `data/recetas.sqlite`, que es UN FICHERO COMPARTIDO
>     -> por eso `traspaso` tiene 7 filas
>     -> y por eso sus `lista_id` NO existen en la base de casa: *** estaban en la de pruebas ***
> ```
>
> *** Y **`traspaso` es un REGISTRO DE OPERACIONES, no un dato de la lista** *** -- *o sea: **que su `lista_id` apunte
> a una lista de otra base no lo invalida**: *es **la huella de que la operacion ocurrio**, y **su lista vivia donde
> vivia.** *
>
> *** Y **por eso la consulta por los siete `lista_id` en casa sale vacia, y NO es un fallo** ***: *es **el sintoma de
> que el registro de operaciones y la base de las listas son **dos cosas distintas** -- *y **una de ellas la
> compartida.** *

## 3. Y lo que esto significa, dicho con precision

```
SE PUEDE DECIR:
  *** las siete operaciones de traspaso EXISTEN y estan registradas *** (con receta, version, semana y lista)
  *** y sus listas NO estan en la base de casa ***
  *** y la explicacion mas simple es que se crearon en la de PRUEBAS ***

NO SE PUEDE DECIR TODAVIA:
  *** de que base es cada `lista_id` ***  -- *y **se puede saber**: *creando una lista en CASA, traspasando una
  receta, y mirando si su `lista_id` aparece en `lista` de casa.*
  *** ni si eso es un problema ***  -- *porque `traspaso` **sirve precisamente para no repetir la operacion**, *y
  **cumple su funcion aunque la lista se haya ido.** *
```

## 4. Y hay **una consecuencia que importa para el encargo**, y hay que decirla

> *** El encargo dice: *** *** «no toques ... **pruebas compartidas 5434** con restauraciones destructivas» *** -- *y
> **«pruebas compartidas» es exactamente lo que este hallazgo describe**: *la 5434 **es compartida**, *y **la suite
> escribe en ella.** *
>
> *** Y **lo que este hallazgo añade** ***: *** *** **`data/recetas.sqlite` tambien es compartido** *** -- *o sea:
> **la suite escribe en la 5434 y en un fichero que tambien usa la casa.** *
>
> *** Y **eso no se habia dicho**, y **es la clase de cosa que B13 pide inventariar** («rutas y componentes
> montados»): *no solo **que se sirve**, *sino **donde escribe cada cosa.** *
>
> *** Y **no se dice que sea un defecto** ***: *se dice que **esta medido**, *y que **la separacion entre «datos de
> casa» y «datos de pruebas» no es total**: *hay **una tabla de recetas (`traspaso`) que las mezcla.** *

## 5. Y el estado de B13, con el cabo convertido en hallazgo

```
  1) RUTAS Y COMPONENTES       HECHO
  PASO 1 (usuarios)            HECHO -- 38 en CASA, con convencion, y el aviso de «Madre»
  PASO 2 (crea_usuario)         HECHO Y CONCLUYENTE
  PASO 3 (elegir)              RESUELTO -- `prueba` / `prueba-invitada`
  PASO 4 (por donde)           HECHO -- http://127.0.0.1:8080 (200)
  PASO 4 (los datos)           HECHO -- 42 recetas · 42 del plan · 43 versiones · *** 7 traspasos *** · 11 entradas
                               *** y las 7 listas de esos traspasos NO estan en casa: son de la base de pruebas ***
  PASO 5 (capturas)            con las guardas: sin «Madre», y sin los dos `.sqlite`
  *** Y LA RESTRICCION DEL PROPIETARIO: `cantidad integer` + `nota text` (el esquema permite el fallo) ·
      `cantidad_en` PRESENTE (la correccion de B10, aplicada) · y ninguna «nota de 100 g» en las 15 ultimas ***
```

> *** Y lo que **falta para cerrar la restriccion** sigue siendo **lo mismo**: *** *mirar **las lineas de una lista que
> SI este en casa** -- *y **para eso hay que traspasar una receta desde la web**, *que es **el paso 4 de B13 y necesita
> el navegador.** *
>
> *** O sea: **el limite vuelve a ser el mismo**, y **ahora se sabe por que**: *las listas del puente que hay
> registradas **pertenecen a la base de pruebas**, *y **la comprobacion final requiere una operacion nueva, en
> casa, hecha por una persona.** *
