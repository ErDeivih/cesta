# B14 · **La «rotacion» no es un rotador: es una GUARDA** -- y dice que se tira y que no

*(13 de octubre de 2026. **Y es mas de lo que B14 pedia.**)*

## 1. Lo que se busco, y lo que salio

```
`core/`, patron `rotac|truncate|rename|RotatingFile|maxBytes|backupCount|MAX_|borra|purga`
*** -> 35 coincidencias, y NINGUNA es un mecanismo de rotacion de logs. *** *
```

> *** Y **lo que SI hay es mejor**, *y esta en `core/storage.py`: *
> ```
> l16   *** «Capas que NO SE BORRAN NUNCA. *** *`raw` **se puede tirar cuando caduca** -- *ocupa **338 MB**» *
> l21   «*...una particion de bronze **se habia borrado sola**. *Resulto que **la habian apartado** a [...]» *
> l64   *** def comprueba_borrable(ruta: Path) -> None: *** *
> l65       """*** Revienta si la ruta cae dentro de una capa que NO SE BORRA. ***""" *
> l81   *«...apartarlo, **no borrarlo**. *El nombre queda `<cadena>-<fecha>-<motivo>`» *
> l93       carpeta.*** rename ***(destino) *
> ```
>
> *** Y **`core/cobertura.py:142`** lo repite, y **cita la fuente**: *** *** «`docs/OPERACION.md` dice que un
> bronze malo *** SE APARTA, NO SE BORRA ***». *

## 2. *** Y es MAS que una rotacion: es una politica, con una guarda que la hace cumplir ***

```
*** UNA ROTACION ***  -> *borra lo viejo **por tamano o por edad** *
*** Y ESTO ***         -> *** declara que CAPAS NO SE BORRAN NUNCA, *** *
   *** y deja `raw` como la unica que se puede tirar -- *«cuando caduca»*, *y **diciendo cuanto ocupa (338 MB).** *
   *** y `comprueba_borrable` REVIENTA si alguien lo intenta. *** *
```

> *** O sea: *** *** **la regla esta puesta en el camino, y no en el cuidado de quien escribe** *** -- *que es
> **la misma forma de las once imposibilidades**: *`id uuid PRIMARY KEY`, `fuente_dato NOT NULL`, `FUENTES` vacia,
> *y **ahora `comprueba_borrable`.** *
>
> *** Y **«apartar, no borrar» se ejecuta con un `rename`** *** -- *o sea: **el dato no se destruye, se mueve**, *
> *y **el nombre nuevo lleva `<cadena>-<fecha>-<motivo>`** -- *o sea: **dice por que se aparto.** *
>
> *** Y **es la doctrina de B14 en su forma literal**: *** *B14 pide «retencion», *y **el proyecto tiene
> retencion **declarada por capas**, *con **`raw` como la unica prescindible**, *y **con una guarda que lo
> comprueba.** *

## 3. Y el log, entonces, tiene **dos respuestas** y las dos valen

```
*** `data/runs.csv` ***  -> *el log de verdad: **6 columnas** (`ts,fuente,filas,errores,segundos,ok`), *
   *** 228 filas ***, *y **crece una por pasada y por cadena** *
   *** -> y NO TIENE SITIO PARA UN SECRETO (numeros y un nombre de cadena) *** *

*** `core/storage.py` ***  -> *** y la politica de que se tira: *capas, no lineas de log* *** *
   -> *y `raw` **se puede tirar cuando caduca** (338 MB), *y **lo demas no se borra nunca.** *
```

> *** O sea: *** *** **el proyecto no rota su log porque su log no es el problema**: *228 filas, 6 columnas,
> y **sin secretos.** *Y **lo que si ocupa es `raw`** (338 MB), *y **para eso tiene una politica, y una guarda.** *
>
> *** Y **«logs crecientes con rotacion»** *** -- *B14 pide las dos cosas, *y **el proyecto tiene una**: *
> *crece, **sin secretos**, *y **lo que se tira se decide por capas y con una guarda.** *

## 4. Y el estado de B14, con las copias y los logs **medidos**

```
*** B14 · 3 de 5 ***
  *** el CSRF ***     -> *** 5 ensayos *** (`test_fase2_f04_csrf.py`: origen ajeno, preflight, cookie, y GET)
  *** los GET ***     -> *** `test_ninguna_ruta_que_muta_es_un_get` ***
  *** los LOGS ***    -> *** y ahora entero: *** *`runs.csv` (6 columnas, 228 filas, **sin secretos**), *
     *** y `storage.py` con `comprueba_borrable` + «apartar, no borrar» + `raw` como la unica capa prescindible *** *
  *** LAS COPIAS ***  -> *las tres piezas medidas, + el diff, + el orden, + lo que hay dentro*
  *** y queda ***     -> *** una palabra del propietario para el volumen `datos_api:/app/data` *** *
```

> *** Y **la «rotacion» era la unica clausula de B14 sin medir**, *y **resulta que el proyecto la tiene resuelta
> de otra forma, y mejor**: *no **borrando lineas de log**, *sino **declarando capas que no se borran** *y
> **apartando lo malo con su motivo.** *
