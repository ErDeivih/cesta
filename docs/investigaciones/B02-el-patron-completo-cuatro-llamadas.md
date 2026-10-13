# B02 · **El patron completo, leido**: cuatro llamadas -- tres de fracaso y una de exito

*(13 de octubre de 2026. **Se leyeron las cuatro llamadas de Alcampo. Y con esto el trabajo de Lidl queda
especificado entero.**)*

## 1. Las cuatro llamadas, con su linea

```
alcampo.py:721:   log_run(FUENTE, 0, 1, time.monotonic() - t0)                    <- fracaso
alcampo.py:729:   log_run(FUENTE, 0, 1, time.monotonic() - t0)                    <- fracaso
alcampo.py:732:   log_run(FUENTE, 0, 1, time.monotonic() - t0)                    <- fracaso
alcampo.py:1028:  log_run(FUENTE, len(filas), errores, segundos, completa)        <- EXITO
```

> **Tres salidas de fracaso con `(0, 1, ...)` -- *«cero filas, un error»* -- y **una de exito** con los numeros de
> verdad y **el veredicto `completa`**.*
>
> *Y las tres de fracaso son **identicas**: *no dicen **por que** se fallo, solo que no se capturo nada.* **Que es
> lo correcto -- el motivo vive en el mensaje que se imprime al lado.***

## 2. Y con esto, el trabajo de Lidl queda especificado sin nada que decidir menos una cosa

```
PARA LIDL:
  1) en cada SALIDA DE FRACASO (y las tiene: «no se publica: no hay precios regionales
     con vigencia comprobada» es una, y devuelve 1):
        log_run(FUENTE, 0, 1, time.monotonic() - t0)
  2) en la SALIDA DE EXITO:
        log_run(FUENTE, len(filas), errores, segundos, completa)
     con `segundos = time.monotonic() - t0` -- y el t0 ya esta
  3) Y DECIDIR `completa` -- que es lo unico que no se copia.

Y DE LAS CINCO COSAS QUE log_run PIDE, LIDL YA TIENE DOS:
  fuente    -- FUENTE, que ya esta
  filas     -- len(filas), que ya esta
  segundos  -- t0 ya esta; falta restarlo
  errores   -- HAY QUE CONTARLOS: que cuenta como error en Lidl
  completa  -- HAY QUE DECIDIRLO: que es «una pasada buena» de Lidl
```

## 3. Y «completa» para Lidl, con todo lo leido delante

**Lo que se sabe de Lidl, medido en esta sesion:**

```
captura 79 fichas de ofertas semanales («ofertas conocidas»)
region acreditada por nombre (55 regiones), o NO sigue
precio en 77 de 79 · nutricion 0 · ean 0 (y no se inventan)
el `resumen` YA TIENE: fichas_leidas · productos_padre · guardados
                       fuera_de_alcance · en_revision · con_precio · precios_con_vigencia_comprobada
```

> **Y su unica salida de fracaso que se ha leido dice:** *«no se publica: **no hay precios regionales con vigencia
> comprobada**».*
>
> *Asi que «una pasada buena» de Lidl **no es «no hubo errores»**: es **haber leido las ofertas que la pagina
> publica, con su region acreditada y sus precios vigentes**.* ***Que es un juicio que el resumen ya tiene los
> datos para hacer*** -- *`fichas_leidas`, `con_precio`, `precios_con_vigencia_comprobada`, `region`.*
>
> **Y no se decide aqui**: *se deja dicho con sus datos, **porque el docstring de `log_run` avisa de que deducirlo
> de `errores == 0` estuvo mal diecinueve veces**.*

## 4. Y B02, con esto, queda especificado entero

```
1) LIDL: cuatro llamadas a log_run (tres de fracaso y una de exito) y DECIDIR `completa`
   -> los datos para decidirlo ya estan en su `resumen`
2) CARREFOUR Y ALCAMPO: escribir su fichero de cobertura por dia (las 5 lineas de lidl.py:278-285)
3) LOS FIXTURES en tests/fixtures/
4) Y LA DECISION DEL NAVEGADOR -- del propietario
```

> **Cuatro cosas, todas pequenas, y todas medidas.** *Y la unica que pide un juicio -- `completa` de Lidl -- **tiene
> sus datos delante**.*
>
> *Que es, despues de nueve rondas y siete correcciones, el estado en que se puede empezar a escribir: **sin
> ninguna pregunta abierta y sin ninguna suposicion viva**.*
