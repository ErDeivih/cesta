# B03 · **La pieza central ya tiene la forma correcta**: la invariante de la cadena

*(13 de octubre de 2026. **Iba a ser la pieza que hay que disenar, y resulta que el diseño ya esta hecho -- para
otra cosa.**)*

## 1. Lo que dice `grupos_de`

`projects/cesta/emparejar.py:269`:

```python
def grupos_de(enlaces_, filas) -> list[int]:
    """... Y se le pasan las cadenas y los EAN porque la invariante del reparto --
    **un grupo no puede tener dos productos de la misma cadena** -- es la que mas limpia:
    los 74 de 74 grupos grandes la incumplian.
    """
    return agrupar_enlaces(
        enlaces_, len(filas),
        precios=[(f.get("unidad_canon"), f.get("precio_unidad_cent")) for f in filas],
        cadenas=[f["fuente"] for f in filas],       # <- UN ATRIBUTO POR FILA
        eans=[f.get("ean") for f in filas],
        nombres=[f.get("nombre") for f in filas])
```

> **Y fijate en lo que es `cadenas`: **un atributo de cada fila**, que se le pasa a `agrupar_enlaces` para que
> **imponga una invariante** -- *«un grupo no puede tener dos productos de la misma cadena».*
>
> **Eso es, exactamente, la forma que la zona necesita.** *No hay que disenar nada: **hay que anadir un
> parametro al lado de uno que ya existe**.*

## 2. Y entonces la zona entra en la MISMA invariante

```
cadenas=[f["fuente"] for f in filas]        hoy
+  regiones=[f.get("region") for f in filas]   y lo que pide la zona
```

**Y la invariante pasa a ser:**

> **«Un grupo no puede tener dos productos de la misma cadena **en la misma zona**.»**

*Que es **literalmente la decision de identidad** de la ronda 63 -- «la zona entra en la identidad del grupo» --
**ya escrita en la forma que el codigo usa**.* *Dos precios del mismo producto en zonas distintas **no pueden
estar en el mismo grupo**, y la misma maquinaria que hoy impide juntar dos productos de Mercadona lo impedira.*

## 3. Y esto cambia la naturaleza del trabajo, que es lo importante

*En la ronda 71 quedo dicho:* **«(1) es el unico sitio donde de verdad hay que decidir algo nuevo»**.

> **Y era falso.** *`grupos_de` **no hay que disenarlo**: hay que **anadirle un parametro**, y **la decision de
> que hace con el ya esta tomada** -- *porque es la misma que ya toma con las cadenas.*
>
> *Y `agrupar_enlaces` (`core.matching`) es quien tiene el freno, y ya sabe recibir listas de atributos por
> fila.* **Lo que habra que mirar alli es una cosa sola**: *si la invariante esta escrita **para `cadenas` en
> concreto** o **para una lista de atributos**.*
>
> *Si es lo primero, hay que generalizarla -- **y eso si es un cambio**, pero **con el molde ya hecho y a la
> vista**.* *Si es lo segundo, es pasar la lista.* **Y eso es una medida, la novena -- y es la ultima.**

## 4. Y las cuatro piezas, con la tercera a la vista

```
HECHO:   donde_comprar PIDE la zona (si esta)                -- f952c80
HECHO:   tabla_de GUARDA la zona (si las filas la traen)     -- 0d1a50c
A LA VISTA: grupos_de -- la zona va AL LADO DE `cadenas`, en la misma invariante
FALTA:   (1) `agrupar_enlaces`: ¿la invariante es para `cadenas` o para atributos?  <- LA NOVENA MEDIDA
         (2) que la clave con la que se hereda incluya la zona
         (3) y que donde_comprar HAGA algo con ella -- comparar dentro de la zona, o avisar
```

## 5. Y por que esto es una buena noticia que hay que decir con cuidado

**La pieza que iba a ser un diseño es un parametro.** *Y eso **no es suerte**: es que **el problema de juntar
cosas que no deben ir juntas ya estaba resuelto** -- para las cadenas.*

> *Que es la forma en que este proyecto lleva veinte fases resolviendo lo mismo:* **la invariante del reparto**,
> *que ya limpio los 74 grupos grandes, **es la misma clase de regla que hacía falta para las zonas**.*
>
> *Y el peligro, dicho tambien:* **una invariante generalizada de mas puede romper el caso que ya funciona.**
> *Asi que la novena medida no es «como se anade»: es **«que hace hoy exactamente, y con que»** --* y hay que
> leerla, **no suponerla**. *Que es lo que ha costado veintisiete correcciones aprender.*
