# B03 · **El veto de Lidl y el motivo que ya existe** -- las dos frases, y como encajan

*(13 de octubre de 2026. **Dos textos que parecen contrarios y no lo son. Y de como se leen depende el
diseno.**)*

## 1. Las dos frases, juntas y enteras

### Lo que hace hoy el codigo -- `plataforma/api/cesta.py:37`

> *«**Por que Lidl no esta en la segunda, y no es una decision pendiente.** `collectors/lidl.py` publica
> **ofertas semanales parciales**, no el surtido completo.* ***Meterlo en las comparaciones haria que
> pareciera tener precio para cosas que no cataloga*** *-- y un «Lidl no lo tiene» que en realidad es «no lo
> hemos capturado» es exactamente la clase de mentira que esta fase lleva cazando. Se declara capturada y no
> comparable, y se dice por que.»*

*Y hay dos listas, con la distincion escrita:*

```python
CADENAS_QUE_SE_CAPTURAN = ("carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl")   # seis
CADENAS                 = ("alcampo", "aldi", "carrefour", "dia", "mercadona")            # cinco
```

### Y lo que pide el plan -- B03

> *«**Eliminar veto global a precios validos de Lidl**: permitir **candidatos observados, vigentes y de
> identidad acreditada**, y **marcar los no observados como desconocidos**. Lidl no gana una cesta completa si
> faltan lineas; **si puede ofrecer una linea exacta con precio valido** o una alternativa que la persona
> acepte.»*

## 2. Y **no son contrarias**, y la diferencia es exactamente esta

  - **`cesta.py` prohibe una cosa muy concreta**: *que Lidl **pierda una comparacion** por no tener un
    producto* -- *porque «Lidl no lo tiene» seria falso: es «no lo hemos capturado».*
  - **El plan prohibe otra**: *un **veto global**, o sea descartar **todos** sus precios por ser parcial su
    catalogo.*

> **Y las dos se pueden cumplir a la vez, y es lo que el plan pide con sus propias palabras:**
>
> *«permitir **candidatos observados, vigentes y de identidad acreditada**, y **marcar los no observados como
> desconocidos**.»*
>
> **O sea: Lidl entra en la comparacion **por candidato y no por cadena**, y **solo con lo que se ha visto**.
> Lo que no se ha visto **no se cuenta como «no lo tiene»: se cuenta como desconocido** -- que es justo lo que
> `cesta.py` teme, resuelto en vez de evitado.**

**Y la frase del plan que lo cierra es la segunda mitad**: *«Lidl **no gana una cesta completa** si faltan
lineas; **si puede ofrecer una linea exacta** con precio valido.»*

> *Asi que la regla no es «Lidl no compara» ni «Lidl compara igual que los demas»*: **es «Lidl puede ganar una
> linea, y no puede ganar una cesta».** *Que es una regla mas fina, y mas util.*

## 3. Y la pieza que hace falta ya existe: **el motivo**

`cesta.py:53`:

```python
def por_que_no_se_compara(cadena: str) -> str | None:
    """El motivo por el que una cadena capturada no entra en las comparaciones.
    *Devuelve `None` si si se compara.* **Existe para que la pantalla pueda decir por que falta una cadena,
    en vez de dejarla simplemente ausente.**"""
```

> **Y ese es el patron de toda la fase, ya escrito**: *la cadena no se deja ausente, **se explica**.* **Lo que
> B03 anade es**: *que el motivo pase de ser «esta cadena no compara» a «**esta linea** de esta cadena es un
> candidato observado, y **aquellas** no se vieron».*

## 4. Lo que hay que cambiar, entonces, y **no** es quitar Lidl de una lista

**Quitar `lidl` de `CADENAS` seria el arreglo equivocado**, y ademas romperia lo que `cesta.py` protege:
*Lidl apareceria como una cadena comparable mas, y **perderia cestas enteras por productos que nunca
cataloga**.*

**Lo que corresponde:**

  1. **La comparacion, por candidato.** *Un precio de Lidl **observado, vigente y de identidad acreditada**
     puede ser candidato para esa linea.* **Y el que no se observo no es candidato, y se dice desconocido.**
  2. **Y la cesta, con su regla**: *Lidl **no puede cerrar una cesta** por si solo si le faltan lineas* --
     *que es lo que `por_que_no_se_compara` ya sabe decir.*
  3. **Y todo esto con `cobertura` delante**: *el fichero de cobertura dice `ofertas_semanales_parcial` y
     **`con_precio: 77` de `79`**.* **Asi que la aplicacion sabe, por linea, si el dato es observado o
     no** -- *que es la condicion que el plan pone y que hoy no se usa.*

## 5. Y lo que no se va a hacer

**No se va a quitar `lidl` de `CADENAS` y ya esta.** *Seria el cambio de una palabra y el efecto contrario al
que se busca: **el veto global se cambiaria por una comparacion global**, y Lidl perderia cestas por lo que no
cataloga.*

**No se va a inventar identidad.** *«identidad acreditada» quiere decir que se sabe **que** producto es* -- *y
el colector dice, con estas palabras, que **el EAN no se inventa** porque la ficha trae `ians` e
identificadores internos que no son un EAN comprobado.* **Asi que una linea de Lidl sera candidata con la
identidad que tenga, y cuando no la tenga se dira -- no se rellenara.**
