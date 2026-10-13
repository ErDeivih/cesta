# B03 · **La region llega a gold.** El historico rehecho, y las seis cifras intactas

*(13 de octubre de 2026. **El paso que tenia la decision, hecho -- y con la prueba de que no rompio nada.**)*

## 1. El cambio, y donde estaba

`projects/cesta/pipeline.py:604`, en `_serie`:

```python
# antes:  """Las cinco columnas que forman la serie de precios, con su fecha."""
columnas = ["fuente", "id_fuente", "precio_cent", "precio_unidad_cent",
            "unidad_canon",
            "region"]      # <- la sexta
```

> **`region` no es una columna mas: es parte de QUE es un precio.** *Y por eso entra en `_serie`, que es donde
> se decide que forma la serie -- **no en un `select` cualquiera**.*

## 2. Y se rehizo el historico con la funcion que existe para eso

```
$ pipeline.rehacer_historico()
  ...
  lidl       2026-10-13  77 filas
  historico rehecho: 1643898 filas, 38 dias, 6 cadenas
```

*Y comprobado en el parquet:*

```
gold tiene region: True

  alcampo    707966 filas  con_region=  0   dias=29
  aldi        74877  filas  con_region=  0   dias=36
  carrefour  509148  filas  con_region=  0   dias=31
  dia        198268  filas  con_region=  0   dias=35
  LIDL           77  filas  con_region= 77   dias=1     <- 77 DE 77
  mercadona  153562  filas  con_region=  0   dias=36
```

> **Lidl: 77 de 77 con su zona.** *Y las otras cinco con cero, que es lo correcto: no la declaran por fila.*

## 3. Y la prueba que se dejo dicha: **las seis cifras**

*Se dijo: «si despues de reconstruir siguen siendo esos, la reconstruccion es correcta -- y si cambian, se
sabra exactamente cuanto». Y siguen siendo esos:*

```
  alcampo       44001   antes 44001   IGUAL
  aldi           3312   antes  3312   IGUAL
  carrefour     17402   antes 17402   IGUAL
  dia            6346   antes  6346   IGUAL
  lidl             77   antes    77   IGUAL
  mercadona      4496   antes  4496   IGUAL
```

*Y `/api/estado`, que es lo que ve el usuario, con la version nueva (`20261013-134352`):*

```
  alcampo 22816 · aldi 2476 · carrefour 16149 · dia 5760 · LIDL 77 · mercadona 4168
  y lidl con su cobertura: ofertas_semanales_parcial
```

## 4. Y la diferencia de filas del historico, que hay que explicar

```
reconstruido:  1643898 filas, 38 dias
el de antes:   1652509 filas, 37 dias
```

**8611 filas menos, y un dia mas.** *Y no es un fallo: es la diferencia entre **reconstruir** y **acumular**.*

*Lo dice el docstring de `rehacer_historico`, con estas palabras:* **«`main()` se queda a proposito con la
instantanea mas reciente de cada cadena y la **anade** al historico».** *Asi que el fichero de antes no era «el
historico»: era **el historico mas lo que se fue anadiendo**, y **los 38 dias del reconstruido son todas las
instantaneas que hay en bronze** -- una mas que las que se habian ido acumulando.*

> **Y eso es exactamente lo que el 18 de septiembre se gano**: *que gold sea «algo que se puede tirar y
> recalcular»*, **en vez de un fichero que solo crece y que nadie sabe reproducir.**

## 5. Y lo que queda: la vista

```
diario: fuente · id_fuente · precio_cent · precio_unidad_cent · unidad_canon · producto_id · fecha
                                              <- y NO tiene region
```

*Asi que la region esta en **gold** y la vista `diario` **no la expone**.* *Un `SELECT` explicito, y hay que
anadirla.*

## 6. Estado de la region, de punta a punta

```
bronze   region, 79 de 79      HECHO
silver   region, 79 de 79      HECHO (ya estaba: with_columns es aditivo)
gold     region, 77 de 77      HECHO (esta ronda, con el historico rehecho)
vista    region                PENDIENTE -- un SELECT
API      region                PENDIENTE
pantalla region                PENDIENTE
```

*Y el paso del historico, que era el que daba miedo, **esta hecho y verificado**:* **las seis cifras iguales, y
38 dias en vez de 37 porque el reconstruido tiene todas las instantaneas.**
