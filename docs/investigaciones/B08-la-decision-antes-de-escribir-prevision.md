# B08 · **La decision que hay que tomar antes de escribir `prevision()`**: reutilizar, no copiar

*(13 de octubre de 2026. **Y el propio proyecto tiene la regla escrita.**)*

## 1. El problema, en una linea

```
*** LA PREVISION NECESITA: *** *sumar por nutriente, y decir la cobertura (`{con_dato, total, completa}`)*
*** Y ESO YA EXISTE, y es PRIVADO: *** *`core/diario.py:287` *** `_cobertura` *** (con guion bajo)*
*** y la suma: *** *`diario.py:307` `suma(columna)`, *que es **una funcion de dentro de `dia()`** *
```

> *** O sea: *** *** **lo que la prevision necesita esta escrito, y esta **dentro** de `dia()`, y **con guion
> bajo.** *
>
> *** Y **copiarlo seria un error, y no por estilo**: *** *porque **`Cesta.tsx:136-139` ya dice por que**: *
> *** «las reglas viven en la API... *** *** COPIAR AQUI EL MINIMO DE LA CLAVE SERIA UNA SEGUNDA COPIA QUE SE
> QUEDA VIEJA *** ***» *** *
>
> *** -> y **aqui el riesgo es peor que una clave**: *si **la prevision y el diario suman distinto**, *
> *los dos numeros **no serian comparables** -- *y **`Tendencias.tsx` los pone en la misma grafica.** *

## 2. *** Y las dos salidas posibles, con su coste ***

```
*** A) HACER PUBLICO EL TROZO QUE HACE FALTA ***
   *-- `diario.resumen(filas) -> dict` con `conocido` y `cobertura`, *y que `dia()` lo use.*
   *** -> y es lo mas limpio: UNA sola funcion, y los dos consumidores la usan.** *
   *** -> y toca `diario.py`, que tiene `test_diario` y su doctrina escrita: *hay que **no romperla.** *

*** B) QUE LA PREVISION USE `dia()` ***
   *-- o sea: **apuntar las lineas de la prevision en una estructura con la MISMA forma que una fila del
   diario**, *y **llamar a `dia()`**.*
   *** -> y es mas barato, y mas raro: *la prevision **no es un dia del diario**, *y **fingirlo** seria
   **mentir en la estructura.** *
```

> *** Y **la (A) es la que el proyecto elegiria**, *y se puede decir por que: *el propio `diario.py` **ya
> separo** `_trae_dato` (`l282`), `_cobertura` (`l287`) y `suma` (`l307`) *-- *o sea: **las escribio como piezas**,
> *y **solo les falta el nombre sin guion bajo.** *
>
> *** Y **la (B) se descarta, y el motivo es del encargo**: *** *** «apuntar» una prevision en el diario
> **seria convertir un previsto en un registrado** *-- *y **el encargo dice, literal: «compra nunca genera
> consumo por si sola»**, *y **el diario rechaza `compra` a proposito** (`diario.py:140`). *
> *Y **fingir una fila del diario** es **la misma confusion, con otro nombre.** *

## 3. Y **la decision, entonces, es una y esta clara**

```
*** ANTES DE ESCRIBIR `prevision()`, y en este orden: ***
  1. *** extraer el resumen a una funcion con nombre en `core/diario.py` ***
     *-- `resumen(filas) -> {"conocido": {...}, "cobertura": {...}}`, *y **que `dia()` la llame** *
  2. *** y comprobar que los ensayos del diario siguen pasando *** *-- *sin tocarlos*
  3. *** y despues escribir `prevision(...)` en la API ***, *llamando a esa funcion*
  *** -> y asi hay UNA sola aritmetica de la nutricion en el proyecto, y no dos. *** *
```

> *** Y **esto no es un detalle de estilo**: *** *** es **lo que hace que la grafica de
> «registrado versus previsto» sea legible.** *Si las dos series **se sumaran con reglas distintas**, *
> *la comparacion **seria una mentira** -- *y **la mentira no estaria en los datos, sino en el codigo.** *

## 4. Y el estado de B08, con su siguiente paso **en orden**

```
*** B08 · la vista de previstos ***
  *** ESPECIFICADA ***   -> *`prevision(con, propietario, desde, hasta, *, cadena=None)`*
  *** y los SEIS pasos *** -> *existen, cada uno con su fichero y su linea*
  *** y ANTES de escribirla, UN paso mas: *** *** sacar el resumen del diario a una funcion con nombre *** *
  *** y despues: `prevision(...)`, el ensayo con `R1=270` y `media=135`, *y **`ABSTIENE` -> `sin_dato`** *** *
  *** y la cadena: *** *de `lista_linea` (`cadena_elegida`), *y **si no hay, no se adivina.** *
```

> *** Y **no se escribe codigo en esta ronda, y el motivo es el de siempre**: *** *mi contexto esta agotado, *
> *y **una refactorizacion de `diario.py` hecha a ciegas** *puede romper **los ensayos de la doctrina que mas
> importa** -- *y **prefiero dejar la decision escrita que arriesgarla mal.** *
>
> *** Y **lo que si queda hecho es la parte que evita el error**: *** *** la decision **tomada y justificada**,
> *con **las dos salidas y sus costes**, *y **con el motivo por el que la (B) se descarta** -- *que es **el
> mismo motivo de `diario.py:140`.** *
