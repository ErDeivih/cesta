# B03 · **La novena medida, y ultima**: la invariante esta escrita para `cadenas`, no para atributos

*(13 de octubre de 2026. **La ultima incognita del cambio de B03, medida. Y con esto el mapa esta entero.**)*

## 1. La respuesta

`core/matching.py`:

```
801:  def agrupar_enlaces(enlaces_: list[tuple], n: int,
804:                      cadenas: list[str] | None = None,
818:      grupo correcto **no puede tener dos productos de la misma cadena**. La union por
944:      cadenas=[f["fuente"] for f in filas],
```

> **Es un parametro llamado `cadenas: list[str] | None = None`.** *No una lista generica de atributos, no un
> `dict` de invariantes: **`cadenas`, y una sola.***
>
> **Asi que es el primero de los dos casos**, *y la respuesta a la novena medida es:*
>
> **la invariante esta escrita PARA `cadenas`, y hay que generalizarla.**

## 2. Y eso es un cambio, pero con el molde a la vista

**No es «pasar una lista».** *Es:*

  1. **que `agrupar_enlaces` acepte la zona** *-- un parametro mas, o una lista de atributos*;
  2. **y que la union por cadena** -- *que es la que impide el grupo monstruo* -- **se haga por (cadena, zona)**;
  3. **y que siga funcionando igual cuando la zona viene vacia** -- *que es el caso de las otras cinco fuentes,
     **y el de todos los dias hasta hoy**.*

> **Y el paso 3 es el que no se puede saltar.** *Una generalizacion que cambie el comportamiento **cuando no hay
> zona** rompe el caso que ya funciona* -- *los 74 grupos grandes que esta invariante limpio.*
>
> **Asi que la prueba de este cambio no es «con zonas funciona»**: es **«sin zonas, sale exactamente lo mismo que
> antes»**. *Que es la forma de probar una generalizacion, y es lo que hay que escribir primero.*

## 3. El mapa del cambio, entero y sin incognitas

```
HECHO:        donde_comprar PIDE la zona (si esta)              -- f952c80
HECHO:        tabla_de GUARDA la zona (si las filas la traen)   -- 0d1a50c
MEDIDO:       grupos_de -- la zona va al lado de `cadenas`, en la misma invariante
MEDIDO:       agrupar_enlaces -- tiene `cadenas: list[str] | None`; HAY QUE GENERALIZARLA
FALTA:        (1) generalizar la invariante a (cadena, zona), SIN CAMBIAR el caso sin zona
              (2) que la clave con la que se hereda incluya la zona
              (3) y que donde_comprar HAGA algo con ella -- comparar dentro de la zona, o avisar
```

**Nueve medidas. Ninguna incognita. Y las tres piezas que faltan tienen su fichero, su funcion y su prueba
escrita.**

## 4. Y la pieza que mas miedo daba es la que menos tiene, y hay que decir por que

*Al empezar esta parte, en la ronda 48, se aparco el cambio con este motivo:*

> *«No se empezo: la consulta devuelve tuplas posicionales y anadir un campo desplaza los indices de la funcion
> mas central del paquete.»*

**Y era falso, en las tres cosas:**

  - **no era `donde_comprar`**, era `grupos`/`matching` -- *dos capas mas abajo*;
  - **no eran los indices** -- *se comprobo midiendo: el error era una columna que no existia*;
  - **y no habia que disenar la invariante** -- *estaba hecha, **para las cadenas**.*

> **O sea: el miedo estaba en el sitio equivocado, por la razon equivocada, y sobre la pieza equivocada.**
> *Y lo que lo deshizo no fue pensar mejor: fue **medir nueve veces** -- y **una de ellas contradecirme a mi
> mismo**.*
>
> **Lo que queda es un cambio de tres sitios con una condicion clara**: *generalizar sin cambiar el caso que ya
> funciona.* *Que es, ahora si, escribir codigo -- y **es lo unico que queda de B03**.*

## 5. Estado de B03

```
captura · bronze con zona (79/79) · cobertura y contador · silver · gold (historico rehecho)
la vista diario (77/77) · /api/estado · la pantalla · CORRE EN LA PASADA DIARIA
club, fechas, nutricion y ausencias                PROBADOS
la zona en donde_comprar (si esta)                 HECHO -- f952c80
la zona en la clave que se hereda (si esta)        HECHO -- 0d1a50c
la zona en el grupo                                MEDIDO -- falta escribirlo
la invariant generalizada                          MEDIDO -- falta escribirlo
y que la comparacion haga algo con ella            FALTA -- con su decision escrita
```

*Todo lo de arriba de la linea esta hecho y comprobado; lo de abajo esta medido y con su forma escrita.*
