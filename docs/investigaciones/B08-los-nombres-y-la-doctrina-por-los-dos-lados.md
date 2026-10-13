# B08 · **Los nombres de los ensayos**: cada cifra de la aceptacion tiene el suyo -- y la doctrina, **por los dos lados**

*(13 de octubre de 2026. **Segunda ronda de B08. Y el paso (3) contesta el paquete entero.**)*

## 1. `test_g01_diario_aceptacion.py`: quince ensayos, y **la aceptacion esta dentro**

```
test_los_NUMEROS_EXACTOS_del_caso_de_aceptacion              <- *** R1=270 y media=135 ***
test_la_mitad_de_la_porcion_es_la_mitad_de_todo
test_ENERGIA_CONOCIDA_Y_PROTEINA_CON_COBERTURA_DISTINTA      <- *** EL CASO DE LA ACEPTACION ***
test_un_nutriente_que_no_trae_nadie_SE_DICE_SIN_DATO_Y_NO_CERO   <- LA DOCTRINA, 13ª VEZ
test_un_CERO_PUBLICADO_ES_UN_DATO_y_cuenta_como_conocido      <- *** ¡Y EL OTRO LADO! ***
test_dos_comidas_legitimas_del_mismo_alimento_son_dos
test_la_identidad_de_la_entrada_es_su_ID_no_su_CONTENIDO      <- identidad por OPERACION
test_UNA_COMPRA_NO_ES_CONSUMO                                 <- *** LA RESTRICCION DEL PROPIETARIO ***
test_los_valores_negativos_y_no_finitos_no_entran
test_la_comida_tiene_que_ser_UNA_DE_LAS_SUYAS                 <- lista blanca (`FUENTES`/`COMIDAS`)
test_el_dia_de_una_persona_NO_VE_EL_DE_OTRA                   <- AISLAMIENTO A/B
test_la_misma_operacion_dos_veces_NO_DUPLICA                  <- idempotencia
test_dos_operaciones_DISTINTAS_con_lo_mismo_SON_DOS           <- *** ¡y las dos mitades! ***
test_sin_clave_sigue_funcionando_como_antes
test_la_clave_no_cruza_entre_personas
```

## 2. `test_procedencia_diario.py`: seis, y son **la procedencia** (= `fuente_dato`, de B06)

```
test_una_receta_que_no_existe_no_se_anota
test_una_VERSION_que_no_existe_tampoco                        <- *** LA VERSION, y no se anota ***
test_la_receta_de_otra_persona_tampoco_se_puede_anotar        <- el dueno
test_una_receta_sin_numero_se_rechaza_CON_SU_MOTIVO            <- *** «con su motivo» ***
test_mi_receta_se_anota_y_QEDA_VINCULADA
test_lo_anotado_a_mano_es_MANUAL                               <- *** ¡`MANUAL` DE `FUENTES`! ***
```

> *** Y `test_lo_anotado_a_mano_es_manual` cierra el circulo con B06: *** *`FUENTES = (ETIQUETA, FICHA, ESTIMADO,
> DESCONOCIDO)` -- *y **`MANUAL` no era de esa lista**.* *** O sea: **hay mas de una lista**, o **`MANUAL` es el
> nombre con el que se anota a mano** -- *y **no se dice cual**, porque **no se ha leido el cuerpo**.*
>
> *** Y es un dato que vale: **el mismo concepto, con dos nombres en dos sitios** -- *que es **exactamente** el
> `cadena`/`fuente` de B04 y el `fuente` del ingrediente de B07.* *** Tercera vez. ***

## 3. Y la doctrina, **por los dos lados, en el mismo fichero**

```
test_un_nutriente_que_no_trae_nadie_SE_DICE_SIN_DATO_Y_NO_CERO
test_un_CERO_PUBLICADO_ES_UN_DATO_y_cuenta_como_conocido
```

> *** Y esto es **lo mas fino de todo el proyecto**, y solo se ve leyendo los dos juntos: ***
>
>   - **si nadie trae el nutriente** -> *«**sin dato**», y **no cero**;*
>   - **si la cadena publica un `0`** -> *es **un dato**, y **cuenta como conocido**.*
>
> *** O sea: **el `0` publicado es informacion, y el hueco no es un `0`** *** -- *y **el proyecto distingue las dos
> cosas en dos ensayos seguidos.***
>
> *** Y es **la decimotercera y decimocuarta vez** que aparece la misma regla: *** *«no se sabe» y «es cero» son
> **dos cosas distintas** -- *y **aqui esta la demostracion de que no es una excusa: hay un caso en que el `0` **si**
> es un dato, y el codigo lo trata como tal.***

## 4. Y B08, con dos rondas, tiene **la aceptacion entera localizada**

```
B08 PIDE EN LA ACEPTACION                        EL ENSAYO
  «R1=270, media=135»                              `test_los_numeros_exactos_del_caso_de_aceptacion`
  «ausencia de energia con proteina conocida»       `test_energia_conocida_y_proteina_con_cobertura_distinta`
  «idempotencia»                                    `test_la_misma_operacion_dos_veces_no_duplica`
                                                    `test_dos_operaciones_distintas_con_lo_mismo_son_dos`
  «aislamiento A/B»                                 `test_el_dia_de_una_persona_no_ve_el_de_otra`
                                                    `test_la_clave_no_cruza_entre_personas`
  «compra nunca genera consumo por si sola»          `test_una_compra_no_es_consumo`
«receta versionada»                                `test_una_version_que_no_existe_tampoco`
«cobertura antes de confirmar»                      `test_energia_conocida_y_proteina_con_cobertura_distinta`
«sin totalizar un dia no completo»                  *** POR MIRAR ***
«recarga»                                          *** POR MIRAR ***
```

> *** Y las dos «por mirar» son de otra capa: *** **«recarga»** *es de la pantalla, y **«sin totalizar un dia no
> completo»** *suena a la **vista de previstos**, que **no es `diario.py`**.*
>
> *** Y no se dice que falten. ***
