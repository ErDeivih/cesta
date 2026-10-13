# B05 · **La sexta clausula, y con sus palabras**: el plan incremental **ya esta**, y con cuatro ensayos

*(13 de octubre de 2026. **Octava ronda de B05. Y cierra la ultima clausula del criterio.**)*

## 1. Los ensayos, y a que frase del plan contesta cada uno

*El plan pide, de B05:* *«**Reservas de despensa y actualizacion del plan con calculo incremental: editar un menu
no borra lineas manuales de compra ni duplica todas las necesidades**.»*

```
tests/test_la_previa_del_plan.py:

  test_lo_que_ya_esta_se_dice_aparte_y_no_entra        <- «NO DUPLICA TODAS LAS NECESIDADES»
  test_la_previa_no_toca_la_lista                      <- «NO BORRA LAS LINEAS MANUALES»
  test_pulsar_dos_veces_no_duplica                     <- LA IDEMPOTENCIA
  test_un_ingrediente_escrito_a_mano_no_entra_y_se_dice <- *** LAS LINEAS MANUALES, Y «SE DICE» ***
  test_la_previa_dice_lo_que_entraria                    <- la previa (preview)
  test_la_accion_mete_lo_que_la_previa_dijo             <- *** Y LA ACCION HACE LO QUE LA PREVIA DIJO ***

tests/test_quitar_del_plan.py:

  test_quitar_una_receta_de_un_dia_la_deja_libre
  test_quitar_dos_veces_da_404_Y_NO_DICE_HECHO_CUANDO_NO_HA_HECHO_NADA   <- «CONFLICTO, NO EXITO FICTICIO»
  test_un_dia_equivocado_no_borra_el_plan_de_otro_dia
  test_un_anonimo_no_quita_nada
  test_b_no_puede_quitar_la_receta_planificada_de_a                      <- el dueno

tests/test_b04_contrato_de_del_plan.py:  (el contrato de B04)
  test_devuelve_los_campos_que_los_consumidores_leen
  test_la_cantidad_ya_viene_escalada                   <- «escalado por comensales» (B04)
  test_devuelve_tambien_los_nombres_que_ya_estaban_en_la_lista
  test_lo_que_no_tiene_destino_sigue_llegando_y_se_puede_decir
  test_sin_recetas_en_el_plan_no_hay_lineas_y_no_revienta
```

## 2. Y las tres frases del plan tienen su ensayo, **con las mismas palabras**

```
EL PLAN DICE                                          EL ENSAYO QUE LO FIJA
  «editar un menu NO BORRA las lineas manuales
   de compra»                                          test_la_previa_no_toca_la_lista
                                                       test_un_ingrediente_escrito_a_mano_no_entra_y_se_dice

  «ni DUPLICA todas las necesidades»                   test_lo_que_ya_esta_se_dice_aparte_y_no_entra
                                                       test_pulsar_dos_veces_no_duplica

  «misma clave con contenido distinto produce
   CONFLICTO, NO EXITO FICTICIO»                        test_quitar_dos_veces_da_404_y_no_dice_hecho_
                                                       cuando_no_ha_hecho_nada
```

> *** Y el tercero es de una precision que vale la pena subrayar ***: *«**da 404 y no dice "hecho" cuando no ha hecho
> nada**»*.*
>
> *Que es **exactamente** «conflicto, no éxito ficticio» -- *y **con el detalle de que el codigo de estado tambien
> importa**: **no basta con no mentir en el cuerpo; hay que no mentir en el status**.*
>
> *** Y `test_un_ingrediente_escrito_a_mano_no_entra_y_se_dice` es la otra mitad de la doctrina del proyecto ***:
> *no entra **y se dice** -- *la misma forma que `test_kg_y_ud_no_se_restan_y_se_dice_por_que`.* **No basta con no
> hacerlo: hay que decirlo.**

## 3. Y B05 queda **entero**, con las seis clausulas y su evidencia

```
  1) RECIBO Y HUELLA                -> Operacion + clave() + id_de_linea()      + 8 ensayos (g12)
  2) CONFLICTO, NO EXITO FICTICIO   -> `id uuid PRIMARY KEY` (la BASE)           + test_quitar_dos_veces_...
  3) CONCURRENCIA Y MEDIA LISTA     -> `borrado_en` + las dos razones del DDL
  4) RESERVAS DE DESPENSA           -> `017_la_despensa.sql`, regla EN EL DDL    + 9 ensayos (f11)
  5) CALCULO INCREMENTAL DEL PLAN   -> la previa y quitar del plan               + 11 ensayos
  6) DESTINO DISTINTO               -> B04 (`014_la_linea_sin_destino.sql`)
```

> *** Seis de seis, y **cada una con nombre de fichero, linea o ensayo**. ***
>
> *Y **cinco de las seis estaban ya** -- *lo que el paquete pedia, **el proyecto lo habia hecho y razonado**, y **en
> tres niveles**: el razonamiento en los docstrings, la garantia en el esquema, y **la prueba con el nombre de la
> frase del plan**.*

## 4. Y el balance final de B05, que es lo que hay que dejar escrito

```
OCHO RONDAS. Y CERO LINEAS DE CODIGO.

  y las seis clausulas del criterio, cerradas:
    - cuatro con el razonamiento del proyecto CITADO (core/traspaso.py, el DDL de lista_linea, 017, y los ensayos)
    - y ninguna con «no existe», «y nada mas», «hay que construirlo» ni «ya esta» sin su cita.

CONTRA B02: diez rondas, NUEVE correcciones de mis conclusiones, y una de ellas («no existe nada») HABRIA
PUESTO UN SEXTO COLECTOR AL LADO DE CINCO QUE FUNCIONAN.

  *** y la unica diferencia fue POR DONDE SE EMPEZO: ***
      B02:  un `grep` con MIS palabras
      B05:  `ls` de la zona -> el fichero que EL TITULO DEL PAQUETE nombraba -> LOS NOMBRES DE LOS ENSAYOS
```

> *** Y eso es lo que queda para B06 y los que faltan: *** **`ls` · el fichero que el título nombra · los nombres de
> los ensayos · y `grep` al final, con las palabras del código.** *Que es lo unico que estas dos comparaciones
> demuestran, y lo unico que hace falta recordar.*
