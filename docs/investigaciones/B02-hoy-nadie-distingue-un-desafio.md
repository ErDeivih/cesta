# B02 · **La primera medida**: hoy ningun colector distingue un desafio de un catalogo vacio

*(13 de octubre de 2026. **La pregunta mas barata de B02, y la que dice por donde empezar.**)*

## 1. La pregunta

*El plan lo pide con estas palabras:* **«Parser de cero resultados valido versus HTML de desafio/error; 429/503 y
`Retry-After`… **HTTP 200 no garantiza datos; desafios no son catalogo vacio**.»**

**Y la primera pregunta, antes de escribir nada: ¿que hace hoy el colector cuando recibe un desafio?**

## 2. La respuesta, y es una sola linea en todo el arbol

```
$ git grep -rn "desafio|captcha|Retry-After|retry_after|429|503|backoff|requiere_interaccion" \
      -- projects/cesta/collectors/

projects/cesta/collectors/carrefour.py:69:ESTADOS_DE_BLOQUEO = (403, 429)
```

> **En los seis colectores, la unica nocion de bloqueo es esa linea de Carrefour.** *No hay deteccion de desafio,
> ni de CAPTCHA, ni `Retry-After`, ni `503`, ni backoff, ni `requiere_interaccion`.*
>
> *Y fijate en lo que **si** esta: **403 y 429, en una tupla con nombre** -- o sea que **alguien penso en el
> bloqueo**, y lo dejo dicho. Lo que no hay es **que se haga nada mas** con esa distincion.*

## 3. Y esto es exactamente lo que B02 pide, sin nada que interpretar

*De las siete cosas del criterio (ver `B02-el-mapa-del-paquete.md`), **la quinta no existe** y **la sexta no
existe**:*

```
5) CERO RESULTADOS VALIDO  vs  HTML DE DESAFIO/ERROR      NO EXISTE
6) 429/503 + Retry-After · backoff · circuit breaker · checkpoints   NO EXISTE
   (y solo Carrefour nombra 403/429)
```

*Y las cuatro de MEDIR -- requests efectivos, cobertura de ramas, productos unicos, tiempo y motivo de cada
reintento -- **tampoco**, porque **no hay reintentos que medir**.*

> **Asi que B02 no es «mejorar lo que hay»: es construir lo que no hay.** *Y decirlo asi cambia el tamano del
> paquete, que es lo que hay que saber antes de empezarlo -- no despues.*

## 4. Y por donde empezar, con esta medida delante

**El orden que se deduce de la propia medida:**

  1. **Distinguir el cero valido del desafio** *-- porque es lo que hace que todo lo demas tenga sentido: hoy un
     desafio **se guarda como catalogo vacio**. Y eso es peor que no capturar: **es escribir que la cadena no
     tiene productos**.*
  2. **Y `ESTADOS_DE_BLOQUEO = (403, 429)` es el sitio donde ya hay una idea** *-- y donde tiene que vivir la
     distincion, **subiendo a los seis**.*
  3. **Y despues** el `Retry-After`, el backoff con limite, el circuit breaker y los checkpoints.

> **Y antes de tocar nada, hay que contestar una cosa que esta medida no contesta: ¿que pasa HOY cuando una
> cadena devuelve un desafio?**
>
> *Se sabe que **no se distingue**; no se sabe **que se guarda**.* **Puede ser un bronze vacio -- y entonces el
> catalogo de esa cadena aparece con cero productos, y la app dice que no hay nada. O puede ser un fallo que
> aborta la cadena.** *Son dos danos distintos y hay que verlo, no suponerlo.*

## 5. Y lo que no se ha hecho, y se dice

**Nada de codigo.** *Una medida, y el mapa de por donde empieza el paquete.*

*Que es lo que en B03 encontro, **en la primera medida**, que el veto estaba en una linea de `en_tienda` y que el
motivo no lo llamaba produccion.* **Empezar midiendo es lo que ha evitado quince sitios mal elegidos.**
