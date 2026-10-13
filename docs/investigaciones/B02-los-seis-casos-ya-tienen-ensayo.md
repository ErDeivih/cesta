# B02 · **Los seis casos del plan YA TIENEN ENSAYO** -- los seis, con nombre

*(13 de octubre de 2026. **La ultima pregunta de B02, contestada. Y la respuesta es que esta hecho.**)*

## 1. Los seis, uno a uno, con su ensayo

*El plan pide, de B02:* *«Aceptar **fixtures de desafios, esquema cambiado, pagina vacia, corte a mitad, reanudar y
publicacion final**, mas captura acotada real cuando sea posible.»*

```
CASO DEL PLAN        ENSAYO QUE LO CUBRE                                          FICHERO
  desafio            test_waf_alcampo.py -- 13 ensayos, y el reto se simula
                     cambiando `obtener`                                           tests/test_waf_alcampo.py
  esquema cambiado   test_una_pagina_sin_navigation_id_no_inventa_redireccion      tests/test_carrefour.py
  pagina vacia       test_categoria_sin_results_no_es_un_error_fatal               tests/test_carrefour.py
                     test_sin_paginacion_el_total_es_cero_y_no_revienta            tests/test_carrefour.py
  corte a mitad      test_un_cuerpo_cortado_se_vuelve_a_pedir_sin_cache             tests/test_carrefour.py
  reanudar           test_si_tambien_falla_sin_cache_se_da_por_perdida              tests/test_carrefour.py
                     test_sin_fallos_no_se_habla_de_vueltas                        tests/test_carrefour.py
                     test_los_bloqueos_seguidos_se_cuentan_desde_cero_tras_un_acierto
  publicacion final  `guardar = completa` -- y su ensayo es el de la pasada          tests/test_runlog.py
                     (y en Alcampo, `test_ninguna_rama_excluida_no_se_escribe_como_fichero_vacio`)
```

> **Los seis. Y los nombres lo dicen sin adornos: *«sin results **no es un error fatal**»*, *«sin paginacion el
> total es cero **y no revienta**»*, *«una pagina sin navigation_id **no inventa** redireccion»*, *«un cuerpo
> cortado **se vuelve a pedir**»*, *«si tambien falla sin cache **se da por perdida**»».**
>
> *** Y estan donde tienen que estar: en los ensayos de los colectores, no en `tests/fixtures/`. ***

## 2. Y lo que esto significa para B02, que ya se puede cerrar por partes

```
DE LAS CUATRO COSAS QUE B02 PEDIA:

  1) MEDIR  -- las cinco medidas del plan (requests, cobertura, productos, tiempo, motivo)
     -> LAS CINCO EXISTEN: peticiones · core/cobertura.py · log_run/check_drift · time.monotonic
        · _por_que_fallan.  Y Lidl ya las usa (5039b9c).
     *** HECHO, salvo lo que se dice abajo del fichero de cobertura. ***

  2) LA RESISTENCIA de Carrefour y Alcampo
     -> LOS DOS LA TIENEN, y mas de lo que el plan pide.
     *** HECHO. ***

  3) LOS FIXTURES de los seis casos
     -> LOS SEIS TIENEN ENSAYO, y con nombres que lo dicen.
     *** HECHO -- y sin crear `tests/fixtures/`, que sobra (cd9f7fe). ***

  4) LA CAPTURA ACOTADA REAL
     -> ES LA SEGUNDA MITAD DE LA ACEPTACION, y no se ha hecho en este paquete:
        Alcampo y Carrefour no se han capturado aqui (B03 capturo Lidl, 79 fichas).
     *** PENDIENTE. Y es lo unico de B02 que toca la red. ***
```

## 3. Y lo que queda de B02, con esto, es corto y esta claro

```
PENDIENTE DE B02:
  a) LA COBERTURA POR DIA de Carrefour y Alcampo -- que es DISEÑO, no copia
     (seis de los trece campos de Lidl no aplican; y la pista esta en el docstring
      de log_run: «Carrefour tiene siempre cuatro o cinco categorias que fallan
      y las da por buenas» -- eso es lo que su cobertura tiene que decir)
  b) LA CAPTURA ACOTADA REAL de Carrefour y Alcampo -- acotada, sin duplicar, sin
     aumentar presion
  c) Y LA DECISION DEL NAVEGADOR -- del propietario
```

> *** Y las tres son distintas de lo que B02 parecia en la ronda 105 ***: *no hay nada que construir, **nada que
> inventar, y nada que copiar** -- *hay **una decision de diseño** (los campos de la cobertura), **una captura
> acotada**, y **una pregunta al propietario**.*

## 4. Y el balance, que ya se puede hacer

**Diez rondas de B02. Dos cosas escritas -- `log_run` en Lidl y un fallo latente de B03 -- y nueve de las diez
gastadas en mirar.**

> *Y lo que se encontro mirando, que **no se habria encontrado escribiendo**:*
>
>   - **que la resistencia entera ya estaba**, *y que la primera conclusion («no existe nada») **habria puesto un
>     sexto colector al lado de cinco que funcionan**;*
>   - **que Lidl era el unico de los seis sin registro de pasada** -- *y eso **no es de B02, es un agujero en mi
>     propio cierre de B03**;*
>   - **que el `region` que yo puse en B03 rompia tres desempaquetados por posicion**, *latente veinte rondas;*
>   - **que `tests/fixtures/` vacio era una decision**, *no una tarea;*
>   - **y que los seis casos del plan ya tienen ensayo.**
>
> *** Ninguna de esas cinco se ve desde un `grep` con las palabras propias. *** *Y **las cinco** se ven **mirando y
> comparando** -- que es lo unico que estas diez rondas han hecho, y **lo unico que hay que seguir haciendo**.*
