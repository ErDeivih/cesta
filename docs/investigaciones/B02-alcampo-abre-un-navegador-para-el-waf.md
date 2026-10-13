# B02 · **Lo que de verdad hace Alcampo con el WAF**: abre un navegador -- y el plan dice otra cosa

*(13 de octubre de 2026. **La lectura que faltaba, y cambia la pregunta de B02 entera.**)*

## 1. Lo que dice el ensayo, con sus nombres

`tests/test_waf_alcampo.py` -- **9,3 KB, y su docstring es la primera pista:**

> *«**El navegador del WAF**: que no se abra una ventana si no hace falta.»*

```
test_renueva_prueba_sin_ventana_y_no_abre_nada_si_pasa
test_si_sin_ventana_no_pasa_el_reto_se_abre_la_ventana          <- *** ABRE UNA VENTANA ***
test_la_ventana_se_abre_fuera_de_la_vista
test_la_posicion_se_calcula_con_el_escritorio_de_verdad
test_el_escritorio_de_verdad_se_lee_y_no_se_supone
test_el_colector_reintenta_con_la_misma_sesion_antes_del_navegador
test_una_pagina_que_navega_se_relee_hasta_que_deja
test_si_de_verdad_no_se_puede_leer_se_dice_none                  <- y ahi SI se rinde
test_el_bazar_no_se_pide / test_la_comida_si_se_pide / ...
```

> **Alcampo, cuando el reto no pasa sin ventana, ABRE UNA VENTANA** -- *fuera de la vista, calculada con el
> escritorio de verdad -- **para que el reto se resuelva**.*
>
> *Y si **de verdad** no se puede leer, **dice `None`**: no se inventa un catalogo.* **Eso esta bien.**

## 2. Y aqui esta la pregunta de B02, que no es la que yo estaba haciendo

*El plan dice, literalmente:*

> *«**No eludir CAPTCHA**, no aumentar presion ni introducir proxies furtivos. **Si exige interaccion humana,
> marcar `requiere_interaccion`**, conservar ultimo valido y continuar otras cadenas.»*

**Y Alcampo hace algo que esta entre las dos cosas:**

  - **no es un proxy furtivo** *-- es una ventana del navegador de verdad, en la maquina;*
  - **no aumenta presion** *-- reintenta con la misma sesion antes de abrir ventana, y hay un limite;*
  - **pero abre una ventana para pasar un reto**, *que es lo que el plan llama «interaccion humana» -- **aunque
    aqui la hace la maquina, no una persona**.*

> **Asi que B02 no es «anadir resistencia a Carrefour».** *Es **decidir que hacer con una resistencia que ya
> existe y que el plan no preveia en esa forma**.*
>
> *Y esa decision **no la puedo tomar yo**: el plan dice «marcar `requiere_interaccion`», y **el codigo hace otra
> cosa que funciona**. *Cambiar lo que funciona por lo que dice el plan es una decision del propietario, no un
> detalle de implementacion.*

## 3. Y lo que si se puede decir sin decidir nada

```
READO, CON NOMBRE Y LINEA:
  - Alcampo abre un navegador para el reto del WAF, y tiene 13 usos de RetoWAF,
    AVANCE_MINIMO, CORTES_PARA_RENDIRSE, MAX_RENOVACIONES y `detener`.
  - Y si no puede leer, dice None -- NO INVENTA CATALOGO.
  - Carrefour tiene ESTADOS_DE_BLOQUEO = (403, 429) y lo usa UNA vez, en la 528.
  - tests/fixtures/ EXISTE Y ESTA VACIA.
  - Y hay 11 ensayos de colectores, uno de ellos del WAF.

NO LEIDO TODAVIA:
  - carrefour.py 500-545 (que hay alrededor de la 528)
  - los otros cuatro colectores
  - y si la ventana del WAF exige que haya un escritorio -- o sea, si la ingesta diaria
    puede depender de que alguien tenga sesion grafica
```

> **Y la ultima de esas tres es la que importa de verdad**: *si el colector **abre una ventana**, entonces
> **la pasada diaria necesita un escritorio**.* *Y eso es una **capacidad limitada** que hay que declarar, no un
> detalle.* **El plan pide declarar cada capacidad implementada/verificada/limitada** -- *y esta podria ser una
> de las limitadas.*

## 4. Y la leccion de las seis rondas, que ya es una sola

```
105  grep con MIS palabras      -> «no existe nada»                 FALSO
106  correccion sin abrir       -> «falta la distincion»            FALSO
107  leer 20 lineas             -> «tiene una linea y nada mas»     FALSO
108  no mirar el directorio     -> «no se sabe si hay fixtures»     FALSO
109  ls + mirar el WAF          -> «es completar, no construir»
110  y LEER el ensayo           -> Y NO ES NINGUNA DE LAS ANTERIORES: es DECIDIR
```

> **Seis rondas, y la respuesta final no era «que falta» ni «que hay»: era «esto ya funciona de una forma que el
> plan no preveia, y hay que decidir si se deja».**
>
> *Y **no se habria llegado ahi con ningun `grep`**, ni con ninguna lectura parcial. **Hizo falta leer los
> nombres de los ensayos** -- que es lo unico que dice **que se considera correcto hoy**.*
>
> **Los nombres de los ensayos son la documentacion que no miente.** *Y eran el sitio numero once por el que se
> miro.*
