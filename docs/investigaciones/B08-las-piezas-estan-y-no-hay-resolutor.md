# B08 · **Las piezas del enlace estan, y NO hay resolutor**: el inventario exacto del paso 1

*(13 de octubre de 2026. **Y es la lista de lo que hay que encadenar para resolver el `producto_id`.**)*

## 1. El inventario, literal -- y **no hay `resuelve`/`busca`/`empareja`**

```
$ grep "^def (resuelve|resolver|busca|mejor|empareja|asigna|producto_de|del_texto)" core/*.py
*** -> NINGUNA COINCIDENCIA *** *
```

> *** Y **lo que SI hay son las piezas**, *y **con nombres precisos**: *
> ```
> *** `core/matching.py` ***              *-- **el parecido** *
>   l38  `raiz(palabra)`                  *la raiz de una palabra*
>   l52  `tokens_sin_marca(nombre, marca)` *los tokens, sin la marca*
>   l65  `tokens(nombre, marca)`           *los tokens*
>   l83  `trigramas(nombre, marca)`        *y los trigramas*
>   l130 `dice(a, b)`                     *el coeficiente de Dice*
>   l136 `idf(documentos)`                *la frecuencia inversa*
>   l145 `parecido(a, b, pesos)`           *y el parecido, **con pesos***
>   l163 `pesos_por_pasillo(docs, ...)`    *y **los pesos por pasillo***
>   l196 `parecido_de_par(vi, vj, ti, tj)` *-- y **el de un par de grupos***
>   l216 *** `bloque(cantidad, unidad)` ***  *-- y **el bloque, con `unidad` DENTRO** *
>   l320 `precio_imposible(a, b)`          *-- **y el precio como filtro***
>   l339 `adelgaza(filas)`                 *-- y **el adelgazado** *
>   l344 *** `nivel(a, b)` ***               *-- y **el NIVEL del par** *

> *** `core/identidad.py` ***             *-- **la identidad** *
>   l54  `_numero(texto)`                  *un numero de un texto*
>   l58  `normaliza_gtin(codigo)`          *-- y **el GTIN** *
>   l77  `atributos(nombre)`               *-- y **los atributos de un nombre** *
>   l158 *** `decide(a, b)` ***              *-- *** EL ORACULO ***, *el que B09 midio como INDEPENDIENTE*
>   l218 `candidatos_por_gtin(productos)`  *-- y **los candidatos por GTIN** *
>   l227 *** `candidatos_por_bloque(productos)` ***  *-- y **por bloque** *
>   l247 *** `ampliar_grupo(grupo, candidato)` ***   *-- y **la consolidacion por transitividad** *
> ```

## 2. *** Y de aqui salen tres conclusiones, y las tres son utiles ***

```
*** 1) EL ORACULO ESTA ENTERO, Y CON SUS DOS CAMINOS ***
   *`decide` (el veredicto) + `candidatos_por_gtin` y `candidatos_por_bloque` (los dos caminos) *
   *+ `ampliar_grupo` (la transitividad) + `nivel` (el nivel del par) *
   *** -> o sea: **B09 y B12 midieron bien, y aqui esta el codigo que lo hace.** *

*** 2) Y NO HAY RESOLUTOR ***  ⚠️
   *** -> o sea: **nadie recibe «tomate» y devuelve candidatos del catalogo.** *
   *Las piezas **existen**, *y **falta el que las encadena** -- *y **eso es exactamente el paso 1 de B08.** *

*** 3) Y `bloque(cantidad, unidad)` LLEVA LA UNIDAD DENTRO ***  ✓✓✓
   *** -> o sea: **el proyecto ya trata `(cantidad, unidad)` como una cosa**, *y no dos. *
   *** -> y **es la misma distincion `g`/`ud` del propietario**, *y del `placeholder` de la web. *
```

## 3. *** Y la conclusion del paso 1, con su forma ***

```
*** LO QUE FALTA, y se puede escribir sin inventar nada: ***
  *** una funcion que, dado un NOMBRE de linea, devuelva CANDIDATOS del catalogo ***
     *-- y **las piezas son**: *`tokens`/`trigramas` (del nombre) -> `parecido` (con pesos) *
     *-> y **`decide`** para el veredicto, *con `candidatos_por_gtin` y `candidatos_por_bloque` como caminos*
  *** y su salida tiene que decir lo que NO sabe ***
     *-- y **el veredicto ya lo sabe hacer**: `identidad.py:33-37` tiene **CINCO veredictos**, *
     *y uno es *** `ABSTIENE` *** (B09) -- *o sea: **«no lo se» ya esta en el vocabulario.** *
```

> *** O sea: *** *** **el paso 1 es un encadenamiento, no una invencion** *** -- *y **el vocabulario de la
> respuesta ya existe** (`ABSTIENE`). *
>
> *** Y **lo que NO se hace**: *** *no **inventar un producto** cuando el parecido es bajo; *y **eso es
> `ABSTIENE`**, *y **es lo que la lista ya usa** (`sin_catalogo`). *
>
> *** Y **la prevision, entonces, tendra TRES estados por ingrediente**: ***
> ```
> *** resuelto ***    -> *hay `producto_id`, *y **hay nutricion** -> *suma, y cuenta en `con_dato`*
> *** ABSTIENE ***    -> *y **no se adivina** -> *entra en `sin_dato` **con su nombre** *
> *** y sin cantidad *** -> *y **el puente ya lo dice** -> *`sin_cantidad`*
> ```
