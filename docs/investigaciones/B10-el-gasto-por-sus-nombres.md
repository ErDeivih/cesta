# B10 · **El gasto, por sus nombres**: catorce ensayos, y la doctrina **por los dos lados otra vez**

*(13 de octubre de 2026. **Tercera ronda de B10. Y la clausula (5) queda contestada entera.**)*

## 1. `tests/test_g05_gasto.py`: catorce ensayos

```
test_suma_lo_conocido_y_DECLARA_LO_QUE_FALTA                       <- *** el criterio, literal ***
test_sin_ningun_importe_el_total_es_None_Y_NO_CERO                  <- *** la doctrina ***
test_cero_explicito_SI_es_un_importe_conocido                       <- *** ¡y el otro lado! ***
test_todo_con_importe_esta_completo
test_agrupa_por_mes_y_por_semana_ISO
test_la_fecha_que_agrupa_es_la_de_la_compra
test_una_linea_sin_fecha_NO_SE_COLOCA_EN_EL_PERIODO_DE_HOY          <- *** no inventar fecha ***
test_un_periodo_desconocido_es_un_ERROR_Y_NO_UN_SILENCIO             <- *** y decirlo ***
test_una_compra_con_lineas_sin_precio_no_esta_completa
test_una_compra_sin_total_conocido_no_suma_cero
test_lo_conocido_y_lo_desconocido_se_suman_POR_SEPARADO              <- *** los dos numeros, separados ***
test_todo_conocido_esta_completo_y_se_agrupa_por_mes
test_una_compra_sin_fecha_no_cae_en_el_periodo_de_hoy
test_la_COBERTURA_cuenta_LINEAS_Y_NO_SOLO_COMPRAS                    <- *** la unidad de la cobertura ***
```

## 2. Y contestan la clausula (5) del criterio **entera**

```
B10 PIDE:  «HISTORICO DE GASTO PAGADO, AHORRO DEMOSTRABLE frente a referencia elegible
            y ESTIMACIONES PARCIALES CON LINEAS QUE FALTAN»
```

> *** Y los catorce ensayos son **exactamente eso**: ***
>
>   - **«estimaciones parciales con lineas que faltan»** *-> `test_suma_lo_conocido_y_declara_lo_que_falta` y
>     `test_la_cobertura_cuenta_lineas_y_no_solo_compras`;*
>   - **«gasto pagado»** *-> `cierra_compra` / `_lo_que_se_paga`, y `test_lo_conocido_y_lo_desconocido_se_suman_por_separado`;*
>   - **y «agrupa por mes y por semana ISO»** *-> *que es **el «semanal/mensual» de B11**.*
>
> *** Y `test_la_cobertura_cuenta_LINEAS_Y_NO_SOLO_COMPRAS` es **una precision que vale mucho**: *** *la cobertura
> **se mide en lineas** -- *o sea: **de una compra de diez lineas, «faltan 3» quiere decir 3 lineas, no 3 compras.**
> *** Que es la misma exigencia que B11 hace de las graficas («declara MEDIDA y UNIDAD») aplicada a un numero. ***

## 3. Y la doctrina, **por los dos lados, otra vez** -- como en B08

```
test_sin_ningun_importe_el_total_es_None_Y_NO_CERO
test_cero_explicito_SI_es_un_importe_conocido
```

> *** Y es **el mismo par** que en el diario: ***
>
> ```
> DIARIO (B08):   test_un_nutriente_que_no_trae_nadie_se_dice_sin_dato_y_no_cero
>                 test_un_cero_publicado_es_un_dato_y_cuenta_como_conocido
> GASTO  (B10):   test_sin_ningun_importe_el_total_es_None_Y_NO_CERO
>                 test_cero_explicito_SI_es_un_importe_conocido
> ```
>
> *** **Cuatro ensayos, dos modulos, la misma distincion** *** -- *y **escrita en los dos sitios**, porque **el
> `<None>` y el `0` se parecen** en los dos.*
>
> *** Y aqui la distincion tiene **consecuencia de dinero**: *** *un total de `0` **dice que no se gasto nada**; un
> total de `None` **dice que no se sabe** -- *y **`test_una_compra_sin_total_conocido_no_suma_cero` es el caso que
> `None` protege.** *

## 4. Y hay **tres** ensayos que son «**no inventes**», con nombre y linea

```
test_una_linea_sin_fecha_NO_SE_COLOCA_EN_EL_PERIODO_DE_HOY      <- no le pongas la fecha de hoy
test_una_compra_sin_fecha_no_cae_en_el_periodo_de_hoy            <- ni a la compra
test_un_periodo_desconocido_es_un_ERROR_Y_NO_UN_SILENCIO          <- y no lo calles
```

> *** Y los tres juntos son **una sola regla con tres casos**: *** *una linea sin fecha **no entra en el periodo de
> hoy** -- *porque **colocarla ahi seria inventar el dato** -- *y **un periodo que no se conoce es un ERROR, no un
> silencio**.*
>
> *** Que es **el encargo, palabra por palabra**: *** *«no inventes ... **precios**» -- *y **aqui no se inventa **una
> fecha**, que es de la misma familia: **el hueco no se rellena con lo que es probable.** *

## 5. Y `test_la_estimacion_de_la_lista.py` contesta **la estimacion**, con tres

```
test_una_linea_con_producto_concreto_encuentra_su_precio
test_una_linea_de_grupo_tambien
test_DIVIDIR_LA_COMPRA_EN_LINEAS_NO_CAMBIA_EL_TOTAL
```

> *** Y la tercera es **una propiedad, no un caso**: *** *partir una compra en lineas **no cambia el total** -- *que es
> **la «suma de partes igual al total» del oraculo de B09**, **aplicada al coste de una lista**.*
>
> *** Y es **la segunda vez en dos paquetes** que aparece esa misma frase: *** *`oraculo_reparto.py`: «suma de partes
> igual al total»; y aqui: «dividir la compra en lineas no cambia el total». *** **La misma garantia, en la compra y en
> el reparto.** *

## 6. Y B10, con tres rondas

```
  1) LOS ESTADOS           -- `cambia_linea` + `SIN_CAMBIAR`                              *por leer el cuerpo*
  2) LAS LISTAS            *** HECHO: *** `crea_lista(..., es_de_casa=False)`, `listas_de`, `papel_en`, `comparte`
  3) BUSCAR Y FILTRAR      *** POR MIRAR ***
  4) LA PAGINACION         *** POR MIRAR *** -- «fijada a version/cursor»
  5) EL GASTO Y EL AHORRO  *** HECHO: *** `cierra_compra` · `_lo_que_se_paga` · `compras_de(lista_id, 12)`
                              + los **17 ensayos** (14 + 3)
  6) Y LA DUREZA           `cambia_linea` + `SIN_CAMBIAR` -- y su ensayo **POR MIRAR**
```

> *** Y las dos que faltan -- **(3) buscar/filtrar y (4) la paginacion** -- *** *son **las dos que el criterio
> describe con mas detalle tecnico** («marca/formato/EAN», «version/cursor»), **y las dos que no aparecen en los
> nombres de `almacen.py`**.*
>
> *** Asi que **probablemente sean de la capa HTTP** -- *y **no se supone**: se dice que **no estan en los nombres del
> modulo que las guardaria**, y **que la paginacion por cursor tiene nombre tecnico** (`cursor` existe, *pero en
> `almacen.py:122` es **el cursor de la base de datos**, **no el de la paginacion** -- *y **esa es una trampa de
> nombre que hay que decir**: **la misma palabra, dos cosas**). *** **Sexta vez.**
