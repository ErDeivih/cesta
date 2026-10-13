# B13 · **El esquema de `lista_linea`, medido**: `cantidad integer` y `nota text` -- **y no hay columna de unidad**

*(13 de octubre de 2026. **Novena ronda de B13. Y la restriccion del propietario aparece en el esquema.**)*

## 1. Las columnas, medidas

```
$ docker exec cesta-db-1 psql -U cesta -d cesta -tAc \
    "SELECT column_name || ' ' || data_type FROM information_schema.columns \
     WHERE table_name='lista_linea' ORDER BY ordinal_position;"

  id uuid · lista_id uuid · grupo_id bigint · producto_id text · nombre_visto text
  *** cantidad integer ***
  *** nota text ***
  anadido_por uuid · anadido_en timestamptz · tachado_por uuid · tachado_en timestamptz
  borrado_en timestamptz · tocado_en timestamptz · en_carrito boolean
  cadena_elegida text · autorizado boolean · autorizado_en · autorizado_producto · autorizado_cadena
  cantidad_en timestamptz
```

## 2. Y la restriccion del propietario, palabra por palabra

> **La restriccion, literal:**
>
> > *«el fallo de que **300 g** necesarios terminan como *** una unidad *** y *** una nota de 100 g ***,
> > **descartando la segunda receta como repetida**.»*
>
> *** Y el esquema tiene: ***
>
> ```
> *** cantidad integer ***   -- *o sea: UN ENTERO. **No cabe «300 g»**: cabe 300, o cabe 1.*
> *** nota      text ***     -- *y «**una nota de 100 g**» es LITERALMENTE esta columna.*
> y *** NO HAY `unidad` ***  -- *o sea: **la cantidad no lleva su unidad consigo.***
> ```

## 3. Y **por eso la unidad tiene que venir de otro sitio** -- y hay que decirlo, no suponerlo

> *** Si `lista_linea` **no guarda la unidad**, entonces **el «300 g» de una linea no puede estar en `cantidad`
> sola** *** -- *y hay **dos caminos** para que la unidad llegue:*
>
> ```
> a) *** POR EL PRODUCTO ***: `producto_id` / `grupo_id` apuntan al catalogo, y el catalogo **si** tiene
>    `unidad_canon` (B06) -- *o sea: **la linea guarda «300» y la unidad la pone el producto.** *
> b) *** O POR LA NOTA ***: `cantidad = 1` y `nota = '100 g'` -- *** que es EXACTAMENTE el fallo que el
>    propietario describe. ***
> ```
>
> *** Y **`nombre_visto`** esta ahi para **lo que se vio al anadirlo** *** -- *que es **la pista de que el proyecto
> guarda el texto de origen**, y **no solo el id.** *
>
> *** Y **`_lo_que_se_paga(cent, parte, cantidad) -> int | None`** (B10) **recibe `parte`**, *que es **la parte del
> envase** -- *o sea: **el reparto por envases que B10 pide («separar coste de ingredientes usados del desembolso por
> envases») se calcula con una `parte`, y esa parte sale de algun sitio que no es esta tabla.** *

## 4. Y **NO SE CONCLUYE**: se dice **la pregunta exacta y la consulta que la contesta**

> *** Lo que **no** se puede decir todavia: *** **si el fallo esta arreglado o no**.
>
> *** Y lo que **si** se puede decir: *** *el esquema **permite** el fallo (una `cantidad` entera y una `nota` de
> texto), **y tambien permite la solucion** (la unidad por el producto, y `cantidad` con el numero real). *
>
> *** Y la consulta que lo decide es **una sola**, y **no se ha hecho**: ***
>
> ```sql
> -- ¿QUE HAY EN LAS LINEAS QUE ENTRARON POR EL PUENTE?
> SELECT cantidad, nota, nombre_visto, producto_id IS NOT NULL AS tiene_producto
>   FROM lista_linea
>  WHERE borrado_en IS NULL AND nota <> ''
>  ORDER BY anadido_en DESC
>  LIMIT 20;
> -- *** Si salen `cantidad = 1` con nota «100 g» -> EL FALLO ESTA.
> -- *** Si salen `cantidad = 300` con producto -> LA UNIDAD VIENE DEL CATALOGO, y esta bien.
> ```
>
> *** Y **esa consulta decide la restriccion del propietario del lado de los datos**, *y **es la siguiente accion** --
> *y **no requiere abrir el navegador.** *

## 5. Y el hallazgo que esto deja, que vale mas que la respuesta

> *** La restriccion del propietario se puede **localizar en el esquema**: *** *** `cantidad integer` + `nota text` son
> **las dos piezas que su descripcion nombra** -- «una unidad» y «una nota de 100 g». ***
>
> *** O sea: **el propietario no describio un sintoma vago: describio **dos columnas** *** -- *y **por eso se puede
> comprobar**, *y **por eso B04 pudo corregirlo**: *habia **un sitio concreto** donde mirar.*
>
> *** Y es **la misma forma que las otras tres prohibiciones del plan** («por ordinal» -> la posicion; «la hora de
> llegada» -> el reloj; «el texto de la restriccion» -> el esquema): *** *** el sintoma nombra **la cosa exacta** que
> hay que mirar. ***
