# B09 · **El banco de pares**: siete ensayos, y uno dice que **un negativo descartado no es un error**

*(13 de octubre de 2026. **Quinta ronda de B09. Y la clausula (2) queda contestada.**)*

## 1. Los siete, por su nombre

```
tests/test_banco_de_pares.py

  test_los_positivos_son_el_mismo_codigo_en_dos_cadenas            <- el banco REAL: + y -
  test_los_negativos_son_misma_marca_y_codigo_distinto
  test_el_banco_MEZCLA_LAS_DOS_CLASES_Y_ES_REPETIBLE                <- *** «real/sintetico» Y repetible ***
  test_el_banco_no_revienta_si_no_hay_de_una_clase
  test_la_PRECISION_cuenta_los_dos_lados(gold)                      <- y con `gold`
  test_un_negativo_que_el_BLOQUEO_DESCARTA_NO_CUENTA_COMO_ERROR     <- *** y esto es la doctrina ***
  test_la_precision_es_REPETIBLE(gold)
```

## 2. Y contesta la clausula (2) entera

```
B09 PIDE:  «BANCO DE PARES REAL/SINTETICO con EAN, marca/variante/neto/pack Y CONTRADICCIONES»
```

> *** Y los siete ensayos son **las dos mitades, y sus controles**: ***
>
>   - **las dos clases**: *`test_los_positivos_son_el_mismo_codigo_en_dos_cadenas` y
>     `test_los_negativos_son_misma_marca_y_codigo_distinto` -- *o sea: **positivos** (*el mismo codigo en dos
>     cadenas*) y **negativos** (*misma marca, codigo distinto*);*
>   - **que se mezclan**, *y **de forma repetible** (`..._mezcla_las_dos_clases_y_es_repetible`);*
>   - **y que no revienta** *si falta una clase (`..._no_revienta_si_no_hay_de_una_clase`);*
>   - **y la medida**: *`test_la_precision_cuenta_los_dos_lados(gold)` -- **precision, con `gold`**, y **contando los
>     dos lados** (positivos y negativos, no solo los aciertos).*
>
> *** Y «real/sintetico» se resuelve asi: *** *el banco **mezcla las dos clases**, y **es repetible** -- *o sea, **el
> banco se puede regenerar y da lo mismo**, que es lo que hace falta para **medir** con el.*

## 3. Y `test_un_negativo_que_el_bloqueo_descarta_no_cuenta_como_error` es **la doctrina, decimoseptima vez**

> *** Un negativo que **el bloqueo descarta** -- *o sea: **un caso que el sistema NO empareja porque se abstiene (o
> porque lo bloquea) -- NO CUENTA COMO ERROR.** *
>
> *** Que es **la misma regla del oraculo con el `umbral`** ***: *allí, **no cubrir** no era un fallo; **aquí,
> descartar no es fallar.** *
>
> *** Y es la forma en que la doctrina entra en una **MEDIDA**: *** *si un sistema **se abstiene** y eso contara como
> error, **la medida empujaria a no abstenerse** -- *o sea, a **decidir sin poder**, que es **exactamente lo que el
> proyecto se niega a hacer.** *
>
> *** Decimoseptima vez. Y esta es la primera en que la doctrina **protege una metrica** de presionar en contra. ***

## 4. Y con esto B09 tiene **cuatro de cinco**

```
  1) REUTILIZAR (Y SER INDEPENDIENTE)  HECHO -- `oraculo_reparto.py` no importa `cesta.py`
  2) EL BANCO DE PARES                 *** HECHO: *** siete ensayos, con pos/neg, mezcla, precision a dos
                                       lados, y `gold`
  3) LOS VEREDICTOS                    LOCALIZADOS -- y son CINCO (`EXACTO · PROBABLE · ALTERNATIVA ·
                                       CUARENTENA · ABSTIENE`), y el criterio nombra otros cuatro
  4) LAS DOS REGLAS DEL EAN            `ABSTIENE` es su forma; y `identidad.py` POR LEER
  5) Y LA PROHIBICION DEL ORDINAL      *** POR MIRAR *** -- «no modificar grupos de listas historicas por ordinal»
```

> *** Y la que queda es **la unica que el plan pide como PROHIBICION** *** -- *y **es el fallo latente de B03**: *
> *«la consulta devolvia 11 columnas y el codigo esperaba 10».*
>
> *** O sea: **B09 termina donde empezo esta sesion** *** -- *en **depender de la posicion**, que el plan **prohibe
> por escrito** en el paquete de identidad.*
>
> *** Y por eso la clausula (5) **no se busca por palabra**: se busca **por patron** -- *`[0]`, `[1]`, tuplas
> desempaquetadas, `sorted` sin clave -- **que es exactamente lo que rompio en `cesta.py`.** *
