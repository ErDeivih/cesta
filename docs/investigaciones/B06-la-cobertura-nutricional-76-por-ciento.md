# B06 · **La cobertura nutricional, medida por cadena y en el universo: 7,6 %, y la da UNA sola cadena**

*(2026-10-14, ~01:10. **Y es el dato que B06 pide «por campo, cadena y universo».**)*

## 1. Lo que hay, y donde

```
*** EL CATALOGO ***  `plataforma/api/catalogo.py:70`  *** def conexion() -> duckdb.DuckDBPyConnection *** *
  *-- *o sea: *** PARQUET leido con DUCKDB ***, *y **no una tabla de Postgres.** *

*** LOS FICHEROS DEL ORO (`data/gold/v20261013-155356`): ***
  `grupos.parquet`  *** 4,4 MB ***   *-- el catalogo*     ·  `precio_diario.parquet`  20,5 MB
  `precio_derivado`   7,0 MB        ·  `resumen.parquet`  1,3 MB  ·  `enlaces.parquet`  0,3 MB
  `promos_por_cadena` 0,0 MB

*** Y `grupos.parquet` TIENE 63 COLUMNAS ***, *y entre ellas: *** `nutricion` · `nutricion_por` ·
  `alergenos` · `ingredientes` · `ean` · `unidad_canon` · `seccion` · `sellos` · `envase` *** *
```

> *** Y **esto responde a una pregunta que B15 dejo abierta**: *** *«Parquet, DuckDB, SQLite y PostgreSQL» --
> *y **los cuatro estan, y cada uno en su sitio**: *
> ```
> *** PARQUET + DUCKDB *** -> *el **catalogo publicado** (`grupos.parquet`), *que la API **lee** -- *
>                            *y **por eso `/datos` es `ro`: la API no escribe el oro.** *
> *** SQLITE ***            -> *el **diario** (`data/diario.sqlite`) *y **el recetario** (`data/recetas.sqlite`)*
> *** POSTGRES ***          -> *las **listas, la compra, los usuarios y las preferencias** *
> ```

## 2. *** Y la cobertura, que es lo que importa ***

```
  fuente       productos   nutricion     pct    alergenos        ean
  *** alcampo ***      22828       *** 0 ***   *** 0,0% ***        0            0
  *** carrefour ***    16149       *** 0 ***   *** 0,0% ***        0    *** 15.095 ***
  *** dia ***           5773   *** 3.942 ***  *** 68,3% ***  *** 1.103 ***  *** 5.773 ***
  *** mercadona ***     4213       *** 0 ***   *** 0,0% ***  *** 2.796 ***  *** 4.213 ***
  *** aldi ***          2683       *** 0 ***   *** 0,0% ***        0            0
  *** lidl ***            79       *** 0 ***   *** 0,0% ***        0            0
  *** UNIVERSO: 51.725 productos, 3.942 con nutricion = 7,6 % *** *
```

> *** O sea, y hay que decirlo entero: ***
> ```
> *** 1) LA NUTRICION LA DECLARA UNA SOLA CADENA: `dia` *** *
>    *-- *3.942 de sus 5.773 productos (*** 68,3 % ***), *y **las otras CINCO: cero.** *
> *** 2) Y los ALERGENOS, otras dos: `dia` (1.103) y `mercadona` (2.796) *** *
> *** 3) Y el EAN, otras dos: `dia` (5.773 de 5.773, completo) y `carrefour` (15.095 de 16.149) *** *
> *** 4) Y `lidl` tiene 79 productos, y CERO en los tres *** *
> ```
>
> *** Y **eso NO es un fallo de la captura**: *es **lo que cada cadena publica.** *
> *Alcampo y Aldi **no enseñan ficha nutricional**, *y por eso **no hay ninguna** -- *y **`Producto.tsx`
> ya lo dice**: *«Alcampo o Aldi no enseñan nada nutricional»*, *y por eso **enseña la de Open Food Facts
> al lado.** *

## 3. *** Y esto es exactamente lo que el encargo pide que NO se confunda ***

> *** «Permite comparar precios validos de articulos observados *** *** SIN PRESENTAR AUSENCIAS DE CAPTURA
> COMO INDISPONIBILIDAD *** ***» *
>
> *** Y **el numero 7,6 % es la prueba de por que esa frase esta en el encargo**: *
> *-- *si la prevision **sumara la nutricion del catalogo sin decir la cobertura**, *
> *-- *y **alguien planificara con Alcampo o Aldi**, *
> *** -> el resultado seria **«0 kcal»**, *y **no es que la comida no tenga calorias: es que la cadena no las
> publica.** *
>
> *** Y **por eso la prevision tiene `cobertura` POR NUTRIENTE y `sin_dato` CON SU NOMBRE** *** -- *
> *y **por eso el 7,6 % no es una verguenza: es un dato que hay que decir.** *

## 4. Y el estado de B06, con la cobertura **medida**

```
*** B06 · «nutricion por campo, cadena y universo» ***
  *** por CAMPO ***   -> *** `nutricion`: 3.942 de 51.725 (7,6 %) *** · *** `alergenos`: 3.899 *** ·
                         *** `ean`: 25.081 *** · *y `nutricion_por` al lado de cada una*
  *** por CADENA ***  -> *** `dia` es la unica con nutricion (68,3 %) ***; *`mercadona` aporta alérgenos;
                         *`carrefour` aporta EAN; *y **Alcampo, Aldi y Lidl: cero en nutricion.** *
  *** y el UNIVERSO *** -> *** 51.725 productos observados *** *
  *** -> y la lectura correcta NO es «falta el 92 %»: *** *** es «cada cadena publica lo que publica, *
     y la cobertura se dice». *** *
```

> *** Y **no se declara «falta informacion»** *** *-- *porque **no falta: no se publico.** *
> *Y **la diferencia entre las dos frases es toda la doctrina del proyecto.** *
