# B03 · **La region llega a la API.** El recorrido entero, y la version que lo publico

*(13 de octubre de 2026. **La ultima pieza del ambito regional: de la web a la vista.**)*

## 1. Y aparecio una pieza que no estaba en el plan: **la vista lee una VERSION, no el parquet**

*La vista `diario` es `SELECT *`*:

```python
con.execute(f"CREATE VIEW diario AS SELECT * FROM '{_de_la_version('precio_diario.parquet')}'")
```

> **`SELECT *` -- o sea que expone las columnas que tenga el parquet.** *Asi que parecia que bastaba con
> reconstruir gold.*
>
> **Y no bastaba, y el motivo esta en `_de_la_version(...)`**: *la vista **no lee `data/gold/precio_diario.parquet`**, lee
> **la copia de la version publicada** -- `data/gold/v20261013-134352/`.*
>
> *Y esa version se creo **a las 13:43**, y el historico se rehizo **despues**.** *Asi que la version publicada
> **no tenia la columna**, y la vista decia 7 columnas con toda la razon.*

**Medido:**

```
data/gold/precio_diario.parquet                    21223 KB   <- el reconstruido
data/gold/v20261013-134352/precio_diario.parquet           <- la version, ANTERIOR
```

## 2. Asi que habia que republicar, y es lo que el sistema espera

```
$ pipeline.main()
  1651966 filas, 6 cadenas
  silver: 51725 filas de 6 cadenas
  gold: 1643898 filas de historico, 38 dias acumulados     <- EL RECONSTRUIDO
pipeline: hecho

data/gold/:  v20261013-132451 · v20261013-134352 · v20261013-135533   <- la nueva
```

> **Y fijate en que el pipeline ya reporta `1643898` y `38 dias`** -- *las cifras del reconstruido, no las del
> acumulado.* *O sea que **la republicacion no rehace el historico**: se lo encuentra hecho y lo publica.*
>
> **Que es exactamente la separacion que el docstring describia**: *`main()` **anade** la instantanea del dia al
> historico, y **`rehacer_historico()` lo recalcula entero**.* *Dos operaciones distintas, y esta ronda ha usado
> las dos en el orden correcto.*

## 3. Y ahora si: la vista expone la region

```
la vista diario: ['fuente', 'id_fuente', 'precio_cent', 'precio_unidad_cent',
                  'unidad_canon', 'region', 'fecha', 'producto_id']
¿expone region? True

  alcampo    707966 filas  con_region=  0
  aldi        74877  filas  con_region=  0
  carrefour  509148  filas  con_region=  0
  dia        198268  filas  con_region=  0
  LIDL           77  filas  con_region= 77
  mercadona  153562  filas  con_region=  0
```

> **Lidl: 77 de 77.** *Y las otras cinco con cero, que es lo correcto.*

## 4. El recorrido entero, cerrado

```
la web de Lidl                       79 fichas, las 79 con precio regional
bronze    region, 79 de 79           HECHO
silver    region, 79 de 79           HECHO
gold      region, 77 de 77           HECHO (historico rehecho)
vista     region, 77 de 77           HECHO (con la version republicada)
API       region                     HECHO -- la vista la expone
pantalla  mostrar de que zona es     PENDIENTE
```

## 5. Y las tres lecciones que deja este paso

**1. Una vista que lee una version no se actualiza porque cambies el original.** *Reconstruir gold **no** cambia
lo que la API sirve hasta que se republica.* *Y eso no es un fallo del sistema: es **lo que hace que una version
publicada sea una version** -- que el dato de ayer no cambie porque hoy se recalcule algo.*

**2. `SELECT *` no significa «todo lo que hay ahora», sino «todo lo que habia cuando se creo».** *La vista se
crea al abrir la conexion, y apunta a un fichero concreto.* **Un `SELECT *` sobre una copia es un `SELECT *`
sobre esa copia.**

**3. Y las dos juntas explican por que no bastaba con lo que parecia obvio.** *Yo di por hecho que anadir la
columna a `_serie` y reconstruir seria suficiente.* **Y faltaba republicar** -- *porque el camino de un dato
hasta la pantalla tiene **una parada mas de las que se ven**: la version que se publico.*

> **Y esta vez no fue una suposicion mia que hubiera que corregir**: *lo dijo la propia consulta* -- *la vista
> devolvia 7 columnas, y la septima no era `region`.* **Mirar antes de afirmar, otra vez.**

*Y con esto, el ambito regional de Lidl esta **demostrado de punta a punta**, que es lo que B03 pedia: no
«acreditado en el colector», sino **medido en cada parada del recorrido**.*
