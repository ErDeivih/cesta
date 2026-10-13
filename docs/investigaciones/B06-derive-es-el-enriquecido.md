# B06 · **`core/derive.py` es el «enriquecido» y el «por cadena»** -- pero no la etiqueta de los tres

*(13 de octubre de 2026. **Cuarta ronda de B06. Y el fichero cubre dos clausulas y deja una a medias.**)*

## 1. Lo que hay: 138 lineas, tres funciones

```
core/derive.py -- 138 lineas

  l27:  def enriquecer(df: pl.DataFrame) -> pl.DataFrame
  l105: def resumen_producto(df: pl.DataFrame) -> pl.DataFrame
  l124: def duracion_tipica_promo(df: pl.DataFrame) -> pl.DataFrame
```

**Y su docstring:**

```python
"""Campos derivados del historico propio.

Aqui es donde se iguala a las cadenas que dan menos. Mercadona regala el precio
anterior y Aldi la fecha de fin de promocion; el resto no. A partir del dia ~30
nosotros tenemos ESO Y MAS para las seis, calculado igual para todas.

Entrada: polars.DataFrame de precio_diario con columnas
    producto_id, fecha, precio_unidad_cent, precio_cent, unidad_canon, promo (opcional)

`unidad_canon` no es opcional aunque el resto del proyecto la trate con cuidado: sin
ella la ventana movil mezcla EUR/kg con EUR/ud y todo lo que sale de aqui -- la base,
el minimo de 90 dias, la posicion y el descuento real -- se calcula contra un numero
que no es comparable. Ver `enriquecer()`.
"""
```

## 2. Y contesta **dos** clausulas de B06 -- y **media** de una tercera

```
B06 PIDE                                   Y AQUI ESTA
  2) «Campo NATIVO / ENRIQUECIDO / MANUAL»   *** EL «ENRIQUECIDO» ESTA -- y se llama asi: ***
                                             *«Campos DERIVADOS del historico propio»*,
                                             y la funcion se llama `enriquecer`.
  1) «por CAMPO, CADENA y universo»          *** «por CADENA» ESTA, Y CON EL MOTIVO: ***
                                             *«Aqui es donde se IGUALA A LAS CADENAS QUE DAN
                                             MENOS. Mercadona regala el precio anterior y Aldi
                                             la fecha de fin de promocion; el resto no.»*

  5) «HISTORICOS DE FICHA, no mezclar
      precio actual con detalle obsoleto»     *** MEDIA: *** el historico existe y se usa
                                             (`precio_diario`, ventana movil, minimo de 90 dias,
                                             posicion, descuento real) -- *** pero «no mezclar
                                             precio actual con detalle obsoleto» NO SE HA MIRADO. ***
```

> *** Y la clausula (2) queda a medias, y hay que decirlo con precision: ***
>
> *`derive.py` **produce** un campo enriquecido. **Lo que no se ha visto es la ETIQUETA**: *el plan pide
> **«campo nativo / enriquecido / manual»** -- *o sea, **para cada campo, de donde salio**.* **Y eso es una
> columna que diga el origen, o tres sitios distintos que lo impliquen.** *Ninguna de las dos se ha visto.*
>
> *** Y `MEDIA` es una respuesta, no una evasiva: *** *lo que hay es **el enriquecimiento**, y **lo que no se ha
> visto es su etiqueta** -- *que son dos cosas distintas, y decirlas juntas seria el error de B02.*

## 3. Y `unidad_canon` es la misma doctrina, **septima vez**

**«`unidad_canon` no es opcional aunque el resto del proyecto la trate con cuidado: sin ella la ventana movil
mezcla EUR/kg con EUR/ud y todo lo que sale de aqui se calcula contra un numero que no es comparable.»**

> *** O sea: sin la unidad, las cifras son **incomparables** -- y el proyecto **se niega a calcularlas**. ***
>
> *Que es **la septima vez** que aparece la misma regla, y ahora con una forma nueva: **no «no se sabe», sino «no
> es comparable»** -- *y la respuesta es **la misma**: **no calcularlo**, en vez de calcularlo mal.*
>
> *** Siete sitios: ***
>
>   ```
>   1) la columna `cantidad` de la despensa    ->  NULL = «no se sabe», que no es 0
>   2) sin_precio                              ->  «no se sabe el precio», que no es gratis
>   3) diario.fuente_dato                      ->  de donde viene el dato
>   4) COALESCE en anade_linea                 ->  «no llega» no es «llega vacio»
>   5) core/alimentos.py                       ->  «mezcla», que no es ni «si» ni «no»
>   6) test_un_cero_no_se_confunde_con_no_haber_dato
>   7) *** `unidad_canon`: sin unidad, las cifras NO SON COMPARABLES -- y no se calculan ***
>   ```

## 4. Y B06, con cuatro rondas, queda asi

```
  1) EL INVENTARIO DE CAMPOS     LOCALIZADO -- 21 ensayos, campo por campo
  2) NATIVO / ENRIQUECIDO / MANUAL   *** MEDIA: *** el «enriquecido» esta (`derive.enriquecer`),
                                     *la ETIQUETA del origen NO se ha visto*
  3) AUSENTE / NO APLICABLE / ...    tres de cinco con sitio; «no publicado» y «pendiente» POR MIRAR
  4) LA COLA CON PRESUPUESTO     *** POR MIRAR *** -- y el plan da DOS numeros: «88 horas», «cada dia»
  5) Y EL HISTORICO DE FICHA     *** MEDIA: *** el historico existe y se usa; «no mezclar precio
                                     actual con detalle obsoleto» POR MIRAR
```

> *** Y las dos que estan «por mirar» apuntan al mismo sitio: *** **el tiempo** -- *con que prioridad se pide un
> campo, y que se guarda del pasado.* *Y las dos **medias** apuntan a **la identidad de cada campo**: de donde
> salio, y de cuando es.*
>
> *** O sea: B06 no va de nutricion. Va de **que cada dato diga de donde viene y de cuando es** -- *y la nutricion
> es solo el ejemplo que el plan usa para pedirlo.* ***
