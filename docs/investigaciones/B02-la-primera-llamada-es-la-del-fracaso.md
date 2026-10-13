# B02 · **La primera llamada es la del fracaso** -- y no se concluye mas

*(13 de octubre de 2026. **Se comparo la primera llamada de los cinco, y sale identica. Y no se dice mas.**)*

## 1. Lo que sale al comparar la PRIMERA llamada

```
alcampo     log_run(FUENTE, 0, 1, time.monotonic() - t0)
carrefour   log_run(FUENTE, 0, 1, time.monotonic() - t0)
dia         log_run(FUENTE, 0, 1, time.monotonic() - t0)
mercadona   log_run(FUENTE, 0, 1, time.monotonic() - t0)
aldi        log_run(FUENTE, 0, 1, time.monotonic() - t0)
```

> **Las cinco son la misma linea, y es la del fracaso: `filas=0, errores=1`.** *O sea: **«no se capturo nada, y
> cuenta como un error»** -- la salida temprana.*
>
> *Y son **la primera coincidencia** de la busqueda. **Con 4 a 6 usos por colector, hay mas llamadas** -- *y esas
> son las que llevan los numeros de verdad.*

## 2. Y por eso esta ronda NO concluye

**Se podria escribir, y seria falso:** *«los cinco solo registran el fracaso»*. **No se ha leido.**

> *Lo que se sabe, y se dice:*
>
>   - **la llamada del fracaso es identica en los cinco** *-- `log_run(FUENTE, 0, 1, time.monotonic() - t0)` --, **y
>     eso es una invariante**: *todos registran el fallo igual.*
>   - **y hay entre 4 y 6 llamadas por colector**, *asi que **hay mas**.*
>   - **y no se ha leido ninguna de las otras.**
>
> *Asi que **lo unico que se puede decir de Lidl** es lo que ya estaba medido: **no llama a `log_run` ninguna
> vez** -- *ni en el exito ni en el fracaso.* **Que ya es bastante: es el unico de los seis que no deja rastro de
> si salio bien o mal.***

## 3. Y la linea que hay que anadir a Lidl, ahora con la comparacion delante

**La del fracaso es trivial y se puede copiar tal cual** -- *«no se capturo nada, y cuenta como un error»*:

```python
log_run(FUENTE, 0, 1, time.monotonic() - t0)
```

**Y la del exito hay que leerla en Alcampo** *-- que tiene 6 usos --* **para ver que le pasa a `completa`.** *Que
es la parte que el docstring de `log_run` avisa que **no se deduce de `errores == 0`**.*

## 4. Y esta ronda es un ejemplo de lo que hay que hacer y de lo que no

```
LO QUE SE HIZO BIEN:   comparar los cinco -- y la comparacion dio una invariante de verdad
LO QUE NO SE HIZO:     concluir de la primera coincidencia, que es lo que habria sido el error numero nueve
```

> *La diferencia entre esta ronda y las seis primeras **no es el esfuerzo: es que aqui se sabia que faltaba algo
> por leer**, y **se dijo**.*
>
> *Que es, al final, lo unico que estas rondas han ensenado: **no que hay que leerlo todo antes de hablar -- eso es
> imposible -- sino que hay que decir QUE NO SE HA LEIDO**.*
>
> *Las seis conclusiones falsas de B02 tenian todas la misma forma: **afirmar sobre lo que no se habia leido, sin
> decirlo.*** *Y esta dice: **«la primera es la del fracaso, y no se ha leido ninguna de las otras».***
