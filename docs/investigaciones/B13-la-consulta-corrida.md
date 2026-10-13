# B13 · **La consulta, corrida**: **no hay ninguna «nota de 100 g»** -- y lo que salio son filas de ensayo

*(13 de octubre de 2026. **Decima ronda de B13. Y la restriccion del propietario queda medida del lado de los datos.**)*

## 1. La consulta, y lo que devolvio

```sql
SELECT cantidad, coalesce(nota,''), coalesce(nombre_visto,''), (producto_id IS NOT NULL)
  FROM lista_linea WHERE borrado_en IS NULL ORDER BY anadido_en DESC LIMIT 15;
```

```
  1 |  | Pan de molde          | NULL
  1 |  | Leche entera          | NULL
  1 |  | Pan de molde          | NULL
  1 |  | Leche entera          | NULL
  1 |  | Pan de molde          | NULL
  1 |  | Leche entera          | NULL
  1 |  | Pan de molde          | NULL
  1 |  | Leche entera          | NULL
  1 |  | Pan de molde          | NULL
  1 |  | Leche entera          | NULL
  1 |  | Sal                   | NULL
  1 |  | Pan de molde          | NULL
  2 |  | Brick de leche        | NULL
  1 |  | *** Linea exacta ***          | NULL
  1 |  | *** Linea alternativa_2 ***   | NULL
```

## 2. Y lo que se puede decir, y lo que no

```
SE PUEDE DECIR:
  *** `nota` esta VACIA en las quince. ***  *Ni una «nota de 100 g».*
  *** `cantidad` es 1 o 2. ***  *Enteros pequenos, no 300.*
  *** y `producto_id` es NULL en las quince. ***

NO SE PUEDE DECIR:
  *** que la restriccion este cumplida *** -- porque **estas quince filas NO son del puente**:
  *«Linea exacta» y «Linea alternativa_2» son **nombres de ensayo**, *y «Pan de molde»/«Leche entera» **se repiten
  emparejados** (`Pan de molde`·`Leche entera`·`Pan de molde`·`Leche entera`...): eso es **un bucle de prueba**, no
  siete recetas distintas.*
```

> *** O sea: **la consulta pregunto por las ULTIMAS lineas, y las ultimas son de la suite** *** -- *que **corre contra
> la base de casa** (por eso estan los 38 usuarios de prueba del paso 1).*
>
> *** Y **la respuesta a la restriccion esta en OTRA parte de la tabla**: *** *** en las lineas de **las siete listas**
> que `traspaso` nombra *** -- *y **esas listas tienen su `lista_id`**, *que **ya se leyo** (los siete
> `fc42d59b…`, `5e8c6564…`, `f1db039a…`, `6704f0a5…`, `47006a80…`, `378ab590…`, `928f44a0…`).*
>
> *** Y **esa es la consulta que falta**, y **ahora se puede escribir con datos**: ***
>
> ```sql
> SELECT ll.cantidad, ll.nota, ll.nombre_visto, ll.producto_id
>   FROM lista_linea ll
>  WHERE ll.lista_id IN ('fc42d59b-…','5e8c6564-…','f1db039a-…','6704f0a5-…',
>                        '47006a80-…','378ab590-…','928f44a0-…')
>  ORDER BY ll.lista_id, ll.nombre_visto;
> -- *** LAS LINEAS QUE ENTRARON POR EL PUENTE, con su cantidad y su nota. ***
> ```

## 3. Y un hallazgo que si vale, y no es menor

> *** En las quince filas, **`producto_id` es NULL** *** -- *o sea: **ninguna de esas lineas tiene producto elegido**,
> *y **por eso `_con_precios` no les pondria precio** (B11/B08: «sin `producto_id` **no se pone precio**, ni se busca
> por nombre»).*
>
> *** Y **`nombre_visto` es lo unico que las identifica** *** -- *que es **exactamente para lo que esta**: *«lo que se
> vio al anadirlo» -- *y **es la forma de que un ingrediente SIN catalogo se conserve** (que es **una clausula del
> encargo**: «ingrediente sin catalogo **conservado**»).*
>
> *** O sea: **la consulta confirma, de paso, que el proyecto conserva el nombre cuando no hay producto** *** -- *y
> **`cantidad = 1` con `nota` vacia** es **una linea normal**, no el fallo.*

## 4. Y el estado de la restriccion, con precision

```
RESTRICCION: «300 g necesarios terminan como UNA UNIDAD y UNA NOTA DE 100 g,
              DESCARTANDO LA SEGUNDA RECETA COMO REPETIDA.»

  LADO «descartar la segunda receta como repetida»:  *** MEDIDO Y NO PASA ***
     `traspaso` tiene 7 filas de 7 recetas DISTINTAS en la MISMA semana -- la clave las distingue por `receta_id`.

  LADO «300 g terminan como una unidad y una nota de 100 g»:  *** MEDIDO EN PARTE ***
     - en las 15 lineas mas recientes: *** `nota` VACIA, `cantidad` 1 o 2, y `producto_id` NULL ***
     - *** pero esas 15 son de la suite, NO del puente *** -> **falta la consulta por los 7 `lista_id`**
     - y el esquema **permite** el fallo (`cantidad integer` sin unidad + `nota text`) **y tambien la solucion**
       (la unidad por el catalogo).
```

> *** Y **`cantidad_en`** (la columna que trae la migracion `019`, B10) esta en el esquema *** -- *o sea: **la correccion
> de la cantidad concurrente esta aplicada en la base de casa**, *y **`lista_linea` la tiene.** *
>
> *** Que es **una comprobacion de la restriccion que si se puede cerrar hoy**: *** *** la columna que B10 dijo que
> traia la migracion `019` **existe en la base de casa.** *
