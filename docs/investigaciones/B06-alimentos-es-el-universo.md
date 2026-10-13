# B06 · **El fichero que el titulo nombra**: `core/alimentos.py` **es el «universo»**, y con la doctrina dentro

*(13 de octubre de 2026. **Segunda ronda de B06. Y el fichero contesta la clausula mas sutil del criterio.**)*

## 1. Lo que hay: 106 lineas, y tres funciones

```
core/alimentos.py -- 106 lineas

l56: def que_es(seccion: str | None) -> Respuesta
l84: def es_comida(seccion: str | None) -> bool
l91: def cobertura_sobre_comida(con_dato: int, de_comida: int, de_mezcla: int = 0) -> dict
```

## 2. Y su docstring es **la respuesta a «campo, cadena y universo»**, entero

```python
"""**Que parte del catalogo es comida**, y que parte no.

**Por que existe.** *El capitulo 18 del material mide la cobertura de nutricion y da un 21,6 p[or
ciento].* **Y ese numero no se puede juzgar sin saber de que se esta hablando**: *si una cuarta parte
de [el catalogo] es lejia, gel de ducha y comida de gato, **pedirle nutricion a eso es pedirle peras al
olmo** -- [y] lee como una carencia cuando parte de el es una categoria que **no aplica**.*

> *Decir un porcentaje sin haber mirado el universo es inventarlo*, que es lo que el capitulo [dejo]
> escrito. **Esto es mirarlo.**

**De donde sale la regla, y no de mi cabeza.** *Se midieron las **19 secciones** ... filas, cuantas
tienen `kcal_100g` y cuantas tienen `ingredientes`.* ... **la separacion es nitida:**

    despensa              7 783 filas   2 745 kcal   1 503 ingredientes
    higiene-belleza       7 303 filas       1 kcal       0 ingredientes     <- NO
    drogueria-limpieza    3 536 filas       8 kcal       0 ingredientes     <- NO
    mascotas              1 584 filas       0 kcal      65 ingredientes     <- NO
    hogar                    56 filas       0 kcal       0 ingredientes     <- NO

**Una seccion de comida tiene cientos o miles de calorias; una que no lo es tiene cero o casi [cero].**
*No hay zona gris en los extremos.*

**Y las ambiguas se tratan como ambiguas.** *`promociones`, `bebe`, `parafarmacia` y `ecologic[os]`*
[son] **mezclas**: en `bebe` hay potitos y hay toallitas; en `parafarmacia` hay cremas y hay
compleme[mentos]. **Devolver «si» o «no» para esas seria inventar** -- *y por eso hay **tres respuestas,
no dos**.*
"""
```

## 3. Y contesta **cuatro** de las cinco clausulas de B06

```
B06 PIDE                                          Y AQUI ESTA
  1) «por campo, cadena y UNIVERSO»                *** «por universo» ES ESTE FICHERO ***
                                                   `que_es(seccion)` + `es_comida(seccion)`
  3) «AUSENTE / NO APLICABLE / NO PUBLICADO /
      ERROR / PENDIENTE, DIFERENCIADOS»            *** «NO APLICABLE» ESTA, Y SE LLAMA ASI: ***
                                                   «parte de el es una categoria que NO APLICA»
  4) «hash y presupuesto por fuente»               `cobertura_sobre_comida(con_dato, de_comida,
                                                   de_mezcla)` -- la MEDIDA, con su universo
  5) y el HISTORICO                                 no aqui
```

> *** Y hay dos frases que hay que subrayar, porque son la respuesta a «no inventes»: ***
>
>   1. ***«Decir un porcentaje sin haber mirado el universo es inventarlo.»*** *O sea: **una cifra sin su
>      universo es una invencion** -- *y **por eso el fichero existe**: para decir **sobre que** es el 21,6 %.*
>   2. ***«Devolver "si" o "no" para esas seria inventar -- y por eso hay TRES RESPUESTAS, NO DOS.»*** *Que es
>      **exactamente** la distincion de la clausula (3): *«no aplicable» **no es** «no».*
>
> *** Y es la QUINTA VEZ en esta sesion que el proyecto resuelve un caso dificil **anadiendo un valor** en vez de
> forzar dos: ***
>
>   ```
>   la columna `cantidad` de la despensa   ->  NULL = «no se sabe», que no es 0
>   sin_precio                             ->  «no se sabe el precio», que no es gratis
>   diario.fuente_dato                     ->  de donde viene el dato
>   COALESCE en `anade_linea`              ->  «no llega» no es «llega vacio»
>   y `core/alimentos.py`                  ->  «mezcla», que no es ni «si» ni «no»
>   ```
>
> *** Y las cinco son la misma regla: **si el mundo tiene tres casos, la respuesta tiene tres valores** -- *y
> forzarla a dos **es inventar**.* ***

## 4. Y lo que NO se dice

**No se han leido las 106 lineas.** *No se dice que `que_es` devuelva exactamente que, ni si `Respuesta` es un
`Enum` de tres valores, ni como se calcula la mezcla.*

```
POR LEER:
  - el cuerpo de `que_es` (l56-84), `es_comida` (l84-91) y `cobertura_sobre_comida` (l91-106)
  - `Respuesta` -- que debe ser el tipo de tres valores, y no se ha visto su definicion
    *** (no aparece en los `class` del fichero: o viene de un import, o es un `Literal`/`StrEnum`) ***
  - y los ensayos: `test_dia_nutricion.py`, `test_de_la_ficha_al_diario.py`, `test_campos_del_grupo.py`
```

> *** Y el siguiente, por lo que informa, es el paso (3) del metodo: **los nombres de los ensayos**. ***
> *Que es lo que encontro, en B02, que Lidl era el unico de los seis sin registro.*
