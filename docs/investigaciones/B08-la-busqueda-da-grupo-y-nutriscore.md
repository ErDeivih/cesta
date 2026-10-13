# B08 · **La busqueda devuelve `grupo_id` y `nutriscore`** -- y no `producto_id` ni `kcal`

*(13 de octubre de 2026. **Y localiza el enlace que falta para la prevision.**)*

## 1. Lo que devuelve la busqueda, medido

```
$ `GET /api/buscar?q=leche`
{
  "fecha_datos": "2026-10-13",
  "resultados": [{
     *** "producto_id": None ***,          <- *** y NO hay producto ***
     *** "grupo_id": 10645 ***,             <- *pero **si hay grupo** *
     "nombre": "Leche semidesnatada Simpl 1 l.",
     "marca": "SIMPL",
     "cadena_mas_barata": "carrefour",
     "precio_cent": 81,
     "precio_unidad_cent": 81.0,
     ...
  }]
}

*** Y LAS CLAVES CON NUTRICION, EN LA RESPUESTA: ['nutriscore'] ***  ⚠️
   -> *o sea: **una letra A-E**, *y **NO `kcal`, ni `energia`, ni proteinas.** *
```

> *** O sea: *** *** **la busqueda da GRUPOS, con precio y con `nutriscore`** *** -- *y **no da productos, ni
> nutrientes.** *
>
> *** Y **`producto_id: None` es correcto**: *una busqueda **agrupa** los productos **de todas las cadenas**
> *bajo un `grupo_id`; *y **el `producto_id` concreto se elige despues**, *cuando se elige **la cadena.** *
>
> *** Y **por eso el `producto_id` es `None` incluso para «leche»** *** -- *que **si esta en el catalogo**, *
> *y con precio.* *

## 2. *** Y ESO LOCALIZA EL ENLACE QUE FALTA, y son DOS pasos y no uno ***

```
*** LO QUE HAY: ***
  *** `nombre` de la linea ***  -> *«tomate», o «leche»*          *-- y es TEXTO*
  *** `grupo_id` ***             -> *y el catalogo **sabe agrupar** (10645)*
  *** `producto_id` ***          -> *y **aqui se elige la cadena**, *y **es donde vive la nutricion** *
     *(`Producto.tsx` **enseña `nutricion`**, `kcal_100g`, y Open Food Facts)*

*** Y EL ENLACE QUE FALTA, para la prevision: ***
  1. *** del texto de la linea a un GRUPO ***   -> *y **el catalogo ya sabe buscar** (`/api/buscar`)*
  2. *** y del grupo a un PRODUCTO ***          -> *** y aqui esta lo que falta: elegir la cadena *** *
     *** -> y sin cadena elegida, **no hay `producto_id`**, *y **sin `producto_id`, no hay nutricion.** *
```

> *** O sea: *** *** **la nutricion de un ingrediente necesita DOS decisiones, y no una**: *a **que grupo**
> pertenece, *y **de que cadena** es el producto. *
>
> *** Y **la segunda es una decision de la persona** *** -- *y el encargo lo dice **dos veces**: *
> ```
> *** «un articulo elegido solo admite alternativas autorizadas» ***
> *** y «no le des una cesta completa no cubierta» ***
> ```
>
> *** *** Y ESO ES LO QUE HACE QUE LA PREVISION SEA HONESTA: *** *** *no se puede **adivinar la cadena** --
> *y por eso **`sin_dato` y `sin_catalogo` son la respuesta correcta** *hasta que alguien **elija.** *

## 3. Y **el `nutriscore` es un dato, y no es nutricion** -- y hay que decirlo

```
*** LA BUSQUEDA DA: `nutriscore` ***  -> *y es **una letra**, *de **A a E** *
*** Y LA PREVISION NECESITA: `kcal`, proteinas, hidratos, grasas ***  *-- y **con su cobertura por nutriente***
```

> *** O sea: *** *** **`nutriscore` no sirve para sumar** *** -- *no se puede **sumar una letra**; *y
> **`Diario.tsx` ya lo sabe**: *«**cobertura por nutriente**: de cuantas entradas sale cada numero.» *
>
> *** Y **por eso la prevision tiene que ir al **producto** y no al **grupo** *** -- *porque **el grupo trae
> `nutriscore`**, *y **el producto trae `kcal_100g`.** *
>
> *** Y **esto reordena el trabajo de B08**: *** *** lo primero no es **sumar**, *sino **resolver el
> `producto_id` de cada ingrediente** -- *y **con eso, la suma es aritmetica.** *

## 4. Y el estado de B08, con el hueco **localizado en dos pasos**

```
*** B08 · y la prevision necesita: ***
  *** 1) el TEXTO de la linea -> un GRUPO ***   -> *y `/api/buscar` **ya lo hace** (`grupo_id: 10645`)*
  *** 2) y el GRUPO -> un PRODUCTO ***           -> *** y falta elegir la cadena *** ⚠️
     *** -> y sin cadena, no hay `producto_id`; y sin `producto_id`, no hay nutricion. *** *
  *** 3) y con el producto: `kcal_100g` x cantidad x comensales -> y sumar CON COBERTURA *** *
     *-- y **`escala` ya sabe** la parte de comensales (ronda 262), *y **`desde-la-compra` ya tiene** el patron
     de la cobertura.* *
  *** y el criterio sigue siendo el del plan: `R1=270`, `media=135`, «ausencia de energia con proteina conocida» *** *
```

> *** Y **la (2) es una decision de la persona, y el proyecto tiene donde guardarla**: *** *`lista_linea` tiene
> **`cadena_elegida`**, **`autorizado`** y **`autorizado_producto`** (B13: la tabla, medida) *-- *o sea:
> **el sitio existe**, *y **es el mismo que usa la lista para «un articulo elegido solo admite alternativas
> autorizadas».** *
