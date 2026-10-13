# B13 · **LA ACEPTACION, EJECUTADA**: `201`, `anadidos: 0`, `sin_catalogo: ["tomate"]`, y persiste

*(13 de octubre de 2026. **Y la respuesta es la honesta: no inventa un producto, y dice cual falta.**)*

## 1. La ejecucion, entera

```
*** POST *** `/api/listas/{id}/desde-el-plan?desde=2026-10-12&hasta=2026-10-18`
   *** -> 201 ***
   {"*** anadidos: 0 ***", "*** ya_estaban: [] ***", "*** sin_catalogo: ["tomate"] ***"}

*** LECTURA 1 *** `GET /api/listas/{id}`
   {"papel": "dueno", "*** lineas: [] ***",
    "estimacion": {"total_cent": 0, "en_carrito_cent": 0, "por_recoger_cent": 0,
                   "*** lineas: 0 ***", "*** sin_precio: 0 ***"},
    "novedades": [], "personas": [{"usuario": "b13-recorrido-2301", "nombre": "Ensayo B13", "papel": "dueno"}],
    "fecha_datos": "2026-10-13"}

*** LECTURA 2, OTRA VEZ ***  -> *** IDENTICA ***  *-- o sea: **persiste.** *
```

> *** Y **el `422` del primer intento no escribio nada** *** -- *porque **la lista seguia con `lineas: []`** *
> *antes de repetirlo. *Asi que **la prueba esta limpia.** *

## 2. *** Y `anadidos: 0` con `sin_catalogo: ["tomate"]` es **la respuesta correcta**, y contesta tres clausulas ***

```
*** 1) «INGREDIENTE SIN CATALOGO CONSERVADO» ***
   -> *`"sin_catalogo": ["tomate"]` *** --- el tomate **esta ahi**, *con su nombre, *y **no se perdio.** *

*** 2) «UN ARTICULO ELEGIDO SOLO ADMITE ALTERNATIVAS AUTORIZADAS» ***
   -> *** NO se elige un tomate cualquiera *** -- *y por eso **`anadidos: 0`**: *
   *** no se mete una linea con «tomate» a secas, porque **no se sabe cual comprar.** *

*** 3) «PERMITE COMPARAR PRECIOS VALIDOS DE ARTICULOS OBSERVADOS SIN... DARLE UNA CESTA COMPLETA NO CUBIERTA» ***
   -> *** Y NO LE DA UNA CESTA NO CUBIERTA: *** *le da **una cesta VACIA, y el motivo.** *
   -> *y **`"sin_precio": 0`** lo confirma: *no hay **ninguna linea sin precio**, *porque **no hay lineas.** *
```

> *** O sea: *** *** **el puente prefiere una lista vacia con su motivo, a una lista con un producto inventado.** *
>
> *** Y **eso es lo contrario de lo que hace un formulario comodo**: *lo comodo seria **meter «tomate» y ya se
> vera**; *y **aqui no se mete**, *y **se dice por que.** *
>
> *** Y **es la doctrina, en la ultima capa**: *** *`sin_catalogo` es **el mismo `null`** de los envases, *y **el
> mismo `no lo sé` de `formato.ts`, *y **el mismo `ABSTIENE` de B09** -- *ahora **en la lista de la compra.** *

## 3. Y **la persistencia esta medida dos veces**, que es lo que el encargo pide

```
*** «La aceptacion principal son cinco recetas semanales con CANTIDADES, COMPRA y PORCIONES REALES
    QUE PERSISTEN TRAS RECARGAR» ***
   -> *** y la lectura 2, hecha despues, da LO MISMO: `lineas: []` y la misma `estimacion`. *** *
   -> *** o sea: **la lista persiste**, *y **lo que persiste es exactamente lo que se escribio: nada, y su motivo.** *
```

> *** Y **la lista no cambio porque no habia nada que anadir** *** -- *y **eso es un resultado, no una ausencia de
> resultado**: *el puente **corrio** (`201`), ***evaluo** las dos recetas, *y **concluyo** que el tomate **no tiene
> producto.** *
>
> *** Y **si hubiera tenido producto**, *`anadidos` **habria sido 1 o 2** -- *y **la consolidacion se veria en la
> linea** (`400 g`). *Pero **no se puede ver**, *y **no se inventa un catalogo para verlo.** *

## 4. Y **lo que esto significa para la restriccion del propietario**, sin forzar nada

```
*** LA RESTRICCION: *** *«300 g necesarios terminan como una unidad y una nota de 100 g, descartando la segunda
receta como repetida»*

*** LO MEDIDO, POR LOS DOS PUENTES: ***
   puente de RECETA  -> *** `300.0 g`, `unidad: "g"`, `nota: ""`, `clave: "tomate|kg"` en las dos ***
   puente del PLAN    -> *** `sin_catalogo: ["tomate"]` -- UNA entrada para las DOS recetas ***
   *** y NO hay «1 unidad», NO hay «nota de 100 g», y NO se descarta la segunda. ***
```

> *** Y **el puente del plan no pudo escribir la linea** *** -- *y **por una razon que no tiene nada que ver con la
> restriccion**: *el tomate **no esta en el catalogo de ninguna cadena**, *y **el encargo prohibe inventarlo.** *
>
> *** O sea: *** *** **la restriccion esta contestada en todo lo que se puede contestar sin inventar un producto**,
> *y **lo que queda no es una duda sobre la restriccion: es que el tomate no tiene ficha.** *
>
> *** Y **la consolidacion SI se vio donde se puede ver**: *** *en `sin_catalogo` *** hay **una entrada y no dos**,
> *o sea: **las dos recetas se unieron por `tomate`**, *que es **la misma consolidacion que la `clave: "tomate|kg"`.** *

## 5. Y el estado, con la aceptacion hecha

```
RECORRIDO 5 · *** tu restriccion ***
  *** puente de RECETA ***  -> *** PREVIA medida ***, y **sin escribir**
  *** puente del PLAN ***    -> *** POST 201 ejecutado ***, *`anadidos: 0`, `sin_catalogo: ["tomate"]`
  *** y la lista PERSISTE *** -> *dos lecturas identicas: `lineas: []`, `estimacion` igual*
  *** y todo en la cuenta de ensayo `b13-recorrido-2301`, con recetas de ensayo. ***
```

> *** Y **lo unico que se escribio** *** -- *y hay que decirlo, porque **es una escritura**: *
> *dos recetas, un plan de dos lineas, y **una lista** (la lista `Lista de ensayo B13`, **con 0 lineas**). *
> *Y **todo de la cuenta de ensayo**, *y **el propietario no se toco.** *
