# B03 · **`grupos`, medido**: la cadena hasta la comparacion, capa por capa

*(13 de octubre de 2026. **El paso que B03 tiene pendiente, empezado por donde el control dice -- midiendo, no
tocando.**)*

## 1. La respuesta, en dos lineas

```python
# plataforma/api/catalogo.py:98
con.execute(f"CREATE VIEW grupos AS SELECT * FROM '{_de_la_version('grupos.parquet')}'")
```

> **`grupos` es una vista sobre `grupos.parquet`, que vive en la carpeta `matching`.** *O sea: **no sale de la
> serie de precios** -- `diario` -- sino del **modelo de emparejamiento**.*
>
> *Que es exactamente lo que el diagnostico de la ronda 56 dijo, y ahora esta localizado en un fichero.*

## 2. Y sus 22 columnas, medidas

```
fuente · id_fuente · nombre · marca · cantidad · unidad_canon · ean
precio_cent · precio_unidad_cent · precio_ref_canon_cent · unidad_ref_canon · cantidad_fiable
imagen · alergenos · ingredientes · origen · promo_txt · categoria · url · seccion
sellos · sellos_origen
```

**Y no hay `region`.** *Y fijate en que **si hay `origen`** -- que es **el pais de fabricacion**, no la zona del
precio.* *Son dos cosas que suenan parecido y no tienen nada que ver, y confundirlas seria el mismo error que
«IAN no es EAN».*

## 3. Asi que la cadena hasta la comparacion es esta

```
la web de Lidl          79 fichas
bronze                  region 79/79          <- HECHO (ronda 42)
silver                  region 79/79          <- HECHO, y ya estaba
gold (precio_diario)    region 77/77          <- HECHO (ronda 46)
la vista `diario`       region 77/77          <- HECHO (ronda 47)
----------------------------------------------------------------------------------------
matching -> grupos.parquet                     <- NO tiene region. AQUI EMPIEZA LO QUE FALTA
la vista `grupos`       NO tiene region
donde_comprar           lee grupos y compara   <- y por eso compara zonas como si fueran la misma
```

> **Y esto explica los seis fallos de la ronda 55 de una forma que no se veia antes**: *yo anadia `region` a la
> consulta de `donde_comprar` **como si el dato estuviera una capa mas abajo**, y **estaba dos**.*
> *No era un indice: era que **el fichero del que lee no la tiene**.*

## 4. Y lo que hay que decidir antes de tocar `matching`, que es lo de verdad

**`matching` agrupa productos de distintas cadenas en un mismo `grupo_id`** -- *para poder compararlos.*
*Y hoy agrupa **sin mirar la zona**.*

> **Asi que la pregunta no es «como se anade una columna», sino:**
>
> **¿puede un `grupo_id` contener precios de DOS zonas distintas?**
>
>   - **Si puede**, *entonces el grupo **deja de ser «un producto»** y pasa a ser **«un producto en una
>     zona»*** -- *y hay que decidir si eso **parte el grupo en dos** o si se **convive** con el aviso.*
>   - **Si no puede** -- *porque `matching` ya empareja dentro de una zona --, entonces solo falta **propagar
>     la columna**, y el trabajo es mecanico.*
>
> **Y eso es una medida, no una opinion**: *se comprueba mirando si algun `grupo_id` de `grupos.parquet` tiene
> hoy filas de mas de una fuente con `region` distinta.* **Hoy no puede pasar -- las otras cinco no declaran
> zona -- pero la pregunta hay que contestarla antes de disenar, no despues.**

## 5. Y lo que se ha hecho en esta ronda, que es medir y no tocar

**Nada de codigo.** *Se ha localizado `grupos` en `catalogo.py:98`, se han leido sus 22 columnas, y se ha
dibujado la cadena entera hasta la comparacion **con la capa que falta marcada en su sitio**.*

> **Y eso es lo que impide repetir el intento de la ronda 55.** *Aquel empezo por `donde_comprar` porque yo
> creia que el dato estaba en `diario`; **ahora esta escrito que `diario` y `grupos` son dos cadenas
> distintas**, y que **la que le falta a la comparacion es la de `matching`**.*

*Y las cuatro capas de arriba -- bronze, silver, gold y la vista `diario` -- siguen hechas y comprobadas.*
