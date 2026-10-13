# B06 · **Los veintiun ensayos de nutricion**, y el inventario del criterio esta **entero** -- con la doctrina, sexta vez

*(13 de octubre de 2026. **Tercera ronda de B06. Y el paso (3) del metodo vuelve a ser el que mas informa.**)*

## 1. Los veintiun ensayos, y a que clausula de B06 contesta cada uno

*El plan pide, de B06:* *«Inventario de **ingredientes, alergenos, kcal, macros, fibra/sal, pesos, cantidades,
origen, conservacion, descripcion y fechas**. Campo nativo/enriquecido/manual; **ausente/no aplicable/no
publicado/error/pendiente diferenciados**.»*

```
tests/test_dia_nutricion.py:

  test_sin_tabla_no_hay_campo                                  <- «AUSENTE»
  test_tabla_parcial_se_conserva_sin_inventar_el_resto          <- *** PARCIAL, SIN INVENTAR EL RESTO ***
  test_nutrientes_invalidos_no_se_publican                      <- «ERROR» (y no se publica)
  test_lo_que_no_es_un_numero_no_se_inventa                     <- *** NO SE INVENTA ***
  test_con_solo_proteinas_si_se_guarda                          <- un campo suelto SI vale
  test_la_tabla_completa_se_guarda_como_json
  test_el_numero_sale_de_dentro_del_envoltorio
  test_por_cuanto_esta_expresada                                <- *** LA UNIDAD (por 100 g) ***
  test_un_cero_no_se_confunde_con_no_haber_dato                 <- *** ¡LA DOCTRINA, SEXTA VEZ! ***
  test_la_tabla_va_directamente_a_nutricion_sin_pasar_por_ingredientes

  test_el_peso_neto_solo_se_cree_si_es_creible                  <- «PESOS», y con juicio
  test_el_tipo_de_producto_es_fino
  test_el_envase_se_guarda_tal_cual_lo_dice_la_cadena           <- *** «TAL CUAL»: no se normaliza ***
  test_el_envase_llega_normalizado_a_bronze
  test_los_dias_de_caducidad_son_un_entero                       <- «FECHAS»
  test_la_caducidad_centinela_no_pasa                           <- y un centinela no cuela
  test_la_conservacion_sale_de_storage_instructions              <- «CONSERVACION»
  test_el_origen_prefiere_el_pais_y_si_no_el_fabricante          <- «ORIGEN»
  test_una_direccion_postal_no_es_un_origen                     <- y una direccion no es un origen
  test_los_codigos_de_barras_de_mas_se_guardan_pero_no_emparejan
  test_una_ficha_pelada_no_revienta                             <- una ficha vacia no rompe
```

## 2. Y el inventario del criterio esta **entero**, campo por campo

```
EL PLAN PIDE          ENSAYO QUE LO CUBRE
  ingredientes          test_la_tabla_va_directamente_a_nutricion_sin_pasar_por_ingredientes
  kcal / macros         todo el bloque de la tabla (json, completo, parcial, solo proteinas)
  fibra/sal             (dentro de la tabla)
  pesos                 test_el_peso_neto_solo_se_cree_si_es_creible
  cantidades            test_por_cuanto_esta_expresada
  origen                test_el_origen_prefiere_el_pais_y_si_no_el_fabricante
                        test_una_direccion_postal_no_es_un_origen
  conservacion          test_la_conservacion_sale_de_storage_instructions
  descripcion           (envase / tipo de producto)
  fechas                test_los_dias_de_caducidad_son_un_entero
                        test_la_caducidad_centinela_no_pasa
  alergenos             *** NO APARECE EN ESTOS 21 -- y NO SE DICE QUE FALTE: hay otros ficheros ***
```

> *** Y la ultima linea importa: los alergenos no salen aqui, y **no se dice que no existan** -- *se dice que **no
> estan en estos 21**.* *** Que es la leccion de B02, aplicada. ***

## 3. Y la doctrina, **sexta vez**

```
test_un_cero_no_se_confunde_con_no_haber_dato
```

> *** Y ya van seis: ***
>
>   ```
>   1) la columna `cantidad` de la despensa    ->  NULL = «no se sabe», que no es 0
>   2) `sin_precio`                            ->  «no se sabe el precio», que no es gratis
>   3) `diario.fuente_dato`                    ->  de donde viene el dato
>   4) `COALESCE` en `anade_linea`             ->  «no llega» no es «llega vacio»
>   5) `core/alimentos.py`                     ->  «mezcla», que no es ni «si» ni «no»
>   6) *** y `test_un_cero_no_se_confunde_con_no_haber_dato` ***
>   ```
>
> *** SEIS SITIOS, SEIS MODULOS DISTINTOS, Y LA MISMA REGLA: **si el mundo tiene tres casos, la respuesta tiene
> tres valores** -- *y forzarla a dos **es inventar**.* ***
>
> *Que es, para el encargo, **la respuesta mas repetida que este proyecto da**: `«no inventes calorias, densidad,
> alergenos, equivalencias, objetivos de salud, precios ni costes de viajes»` **no es una regla que haya que
> recordar** -- *es **la forma que tiene el codigo**, escrita seis veces.*

## 4. Y B06, con tres rondas, tiene **cuatro de sus cinco** clausulas localizadas

```
  1) EL INVENTARIO DE CAMPOS      LOCALIZADO -- los 21 ensayos, campo por campo (falta «alergenos», y no se dice que no este)
  2) NATIVO / ENRIQUECIDO / MANUAL *** POR MIRAR *** -- no se ha visto ese campo en ningun sitio
  3) AUSENTE / NO APLICABLE / NO PUBLICADO / ERROR / PENDIENTE   -> «ausente» y «error» SI; «no aplicable» en
                                     `core/alimentos.py`; «no publicado» y «pendiente» POR MIRAR
  4) LA COLA CON PRESUPUESTO      *** POR MIRAR *** -- «no 88 horas de fichas sin prioridad»
  5) Y EL HISTORICO DE FICHA      *** POR MIRAR *** -- «no mezclar precio actual con detalle obsoleto»
```

> *** Y las tres que faltan son las tres que **tienen que ver con el TIEMPO** ***: *de donde viene el campo, con
> que prioridad se pide, y que se guarda del pasado.*
>
> *Que es, mirado bien, **una sola pregunta con tres caras**: **cada dato, de cuando es, y por que se volvio a
> pedir.*** *Y es **donde el plan pone los dos numeros**: **«88 horas»** y **«cada dia»**.*
