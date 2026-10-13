# B03 · **La pregunta de diseño, medida**: un `grupo_id` ya abarca hasta cinco cadenas

*(13 de octubre de 2026. **Se dijo que era «una medida, no una opinion». Hecha, y contesta la pregunta.**)*

## 1. La medida

```
grupos: 38931  ·  con mas de una fuente: 8746   (el 22 %)

  1 fuente:  30185 grupos
  2 fuentes:  5764
  3 fuentes:  2182
  4 fuentes:   665
  5 fuentes:   135
```

> **Un `grupo_id` no es «un producto de una cadena»: es «el mismo producto visto en varias».** *Y **135 grupos
> abarcan las cinco**.* **La estructura ya esta hecha para eso** -- *es literalmente el trabajo de `matching`.*

## 2. Y entonces la pregunta «¿puede un grupo tener dos zonas?» se contesta sola

**La pregunta era**: *si un `grupo_id` puede contener precios de dos zonas distintas, **el grupo deja de ser «un
producto» y pasa a ser «un producto en una zona»**.*

**Y la respuesta es que la estructura ya admite lo segundo:**

  - **hoy NO PASA**, *y se puede decir por que*: **solo Lidl declara zona, y sus 77 filas son todas la `28`**.
    *Asi que ningun grupo puede tener dos zonas hoy* -- **no por diseño, sino porque solo hay una.**
  - **y manana SI PUEDE PASAR**, *en cuanto otra fuente declare la suya*: *y como **8746 grupos ya cruzan
    fuentes**, cruzar zonas es **la misma forma**, no una nueva.*

> **Asi que la decision no es «si hay que partir el grupo»: es «cuando».** *Y hacerlo cuando ya hay grupos con
> dos zonas seria **descubrir el problema con los datos ya mezclados** -- que es exactamente lo que se evito con
> el grano de `diario`.*

## 3. Y esto cierra la decision que quedaba abierta

*En la ronda 58 quedo escrito, como pregunta:*

> **«¿Puede un `grupo_id` contener precios de DOS zonas distintas?»**
>   - *Si puede, el grupo deja de ser «un producto» y pasa a ser «un producto en una zona».*
>   - *Si no puede, solo falta propagar la columna, y el trabajo es mecanico.*

**Y la medida dice que puede** -- *`matching` ya cruza fuentes, asi que cruzar zonas es lo mismo un paso mas
alla.* **Asi que el trabajo NO es mecanico: la identidad del grupo tiene que incluir la zona.**

> **Y decirlo asi es lo que impide el atajo** -- *que seria **anadir `region` a `grupos` y ya***, con lo que un
> grupo con dos zonas tendria **dos filas con el mismo `grupo_id` y distinta `region`**, y **la comparacion
> elegiria por precio entre dos zonas** -- *que es el error que B03 lleva toda la sesion intentando evitar.*

## 4. El trabajo, entonces, con su forma exacta

  1. **La zona entra en la identidad del grupo** -- *`(grupo_id, region)`*, o *el `grupo_id` se calcula ya
     incluyendo la zona.* **Es la misma decision que la del grano de `diario`, una capa mas arriba.**
  2. **`grupos.parquet` lleva `region`** *-- y entonces la vista `grupos` la expone sola, porque es
     `SELECT *`.*
  3. **Y `donde_comprar` la lee**, *al final del `SELECT`, que ya se probo que no mueve indices.*
  4. **Y la comparacion decide que hace**: *comparar solo dentro de la misma zona, o comparar avisando.*
     *Y las dos se pueden decir, que es lo que el plan pide.*

> **Y el paso 2 no se hace antes que el 1.** *Anadir la columna sin cambiar la identidad daria **grupos con dos
> zonas y el mismo id**, que es peor que no tenerla: **pareceria resuelto.***

## 5. Y lo que se ha hecho en esta ronda

**Una medida, ninguna linea de codigo.** *Y contesta la unica pregunta que quedaba abierta en B03.*

```
LA ZONA EN LA COMPARACION   PENDIENTE
  donde empieza:               groups / matching      (ronda 58, medido)
  la decision de identidad:    LA ZONA ENTRA EN EL ID  (esta ronda, medido)
  la forma de la columna:      al final del SELECT     (ronda 55, probado)
  por que no vale el atajo:    8746 grupos ya cruzan fuentes
```

*Tres de las cuatro cosas que hacian falta para empezar estan medidas. La cuarta -- escribir el codigo -- es
una ronda entera, y ahora se sabe exactamente que tiene que hacer.*
