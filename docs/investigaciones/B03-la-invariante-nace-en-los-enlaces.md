# B03 · **La invariante no nace en la guarda: nace en como se generan los enlaces**

*(13 de octubre de 2026. **El ultimo sitio, y lo dice el docstring de la funcion que iba a tocar.**)*

## 1. Lo que dice, y que mueve el sitio otra vez

`core/matching.py:816`:

> *«`cadenas` (y `eans`) activan **la invariante del reparto**, que es el freno que mas limpia de todos:* **los
> enlaces son 1-a-1 por par de cadenas**, *asi que un grupo correcto **no puede tener dos productos de la misma
> cadena**.»*

> **«Los enlaces son 1-a-1 por par de cadenas.»** *Eso no es una descripcion de la guarda: es **la razon por la
> que la guarda funciona**.*
>
> **La invariante no es una regla que alguien decidiera: es una consecuencia de como se generan los enlaces.**
> *Solo conectan un producto de la cadena A con uno de la cadena B, **y uno a uno por par**.* *Asi que un grupo
> -- que es lo que queda conectado -- **no puede tener dos de la misma**.*

## 2. Y entonces la zona no entra (solo) en la guarda

**Si la invariante se deduce de los enlaces, hay dos sitios, y el primero manda:**

```
1) DONDE SE GENERAN LOS ENLACES   -- «1-a-1 POR PAR DE CADENAS»
   -> y con zona tiene que ser «1-a-1 por par de (cadena, zona)»
   -> AQUI NACE LA INVARIANTE

2) LA GUARDA DE agrupar_enlaces   -- «no puede tener dos de la misma cadena»
   -> y con zona, «... de la misma cadena EN LA MISMA ZONA»
   -> AQUI SE COMPRUEBA
```

> **Y el orden importa**: *si solo se cambia la guarda (2) y no los enlaces (1), **la guarda rechazaria uniones
> que los enlaces no deberian haber propuesto*** -- *y el resultado seria **grupos peores**, no mejores.*
>
> *Al reves -- cambiando (1) y no (2) --, la guarda seguiria prohibiendo lo que ya no se propone, **y no pasaria
> nada**: seria una guarda mas estricta de lo necesario.* **Que es el lado seguro por el que empezar.**

## 3. Y esto explica por que el cambio parecia pequeño y no lo es

*En la ronda 74 se dijo, con razon, que `grupos_de` «ya tiene la forma»: **pasa `cadenas` por fila**.* *Y es
verdad.* *Pero **de donde salen esos enlaces** -- los `enlaces_` que `grupos_de` recibe -- **es otra cosa**, y
es donde la invariante nace.*

> **Asi que el cambio de B03 no son «tres sitios»: son cuatro, y el que faltaba es el primero.**
>
>   1. **donde se generan los enlaces** *-- «1-a-1 por par de (cadena, zona)»* *← EL QUE FALTABA*
>   2. `grupos_de` *-- pasar `regiones` al lado de `cadenas`*
>   3. `agrupar_enlaces` *-- la guarda, por `(cadena, zona)`, con su prueba de «sin zonas nada cambia»*
>   4. `tabla_de` *-- la clave que se hereda, con la zona* *(ya hecho: `0d1a50c`)*

## 4. Y lo que hay que medir antes de escribir nada, que es la decima

**Donde se generan los enlaces.** *La pista es la propia frase: «1-a-1 **por par de cadenas**».*

> *Se busca el sitio que **empareja por pares de cadenas** y **decide que enlaces existen**.* *Y lo que hay que
> contestar es una pregunta sola:*
>
> **¿el emparejamiento por pares de cadenas sabe de zonas?** *Si la zona esta en las filas que compara, **es un
> `group_by` mas**; si no, **hay que llevarla hasta alli** -- y eso puede ser mas largo que todo lo demas.*

## 5. Y esto es, exactamente, la clase de cosa que estas nueve medidas han estado evitando

**La ronda 55 fracaso por empezar en `donde_comprar`.** *La 68, por creer que el fallo estaba en `estabiliza`.*
*La 71, por decir que `grupos_de` era «el unico sitio donde hay que decidir algo nuevo».*

> **Y las tres veces, la causa fue la misma: mirar el sitio donde el sintoma aparece, en vez de la cadena que
> lo produce.**
>
> *Esta vez no se ha escrito nada, y el docstring ya ha dicho **que el sitio que iba a tocar no es el primero**.
> **Que es lo que se gana leyendo antes de escribir** -- y lo unico que estas nueve medidas han comprado.*
