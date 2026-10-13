# B07 · **Los nombres de los ensayos**: la version, el «en voz alta», y el «no se inventa» -- decima vez

*(13 de octubre de 2026. **Tercera ronda de B07. Y el paso (3) del metodo vuelve a ser el que mas informa.**)*

## 1. Los nueve, y a que clausula contestan

```
tests/test_detalle_receta.py:
  test_la_ruta_del_detalle_ya_no_sirve_el_modulo_compartido
  test_el_detalle_lee_la_receta_de_la_ruta_y_no_un_estado_de_paso    <- la receta se lee DEL DATO
  test_el_404_SE_DISTINGUE_DE_UN_FALLO                                <- «conflicto, no exito ficticio»
  test_se_puede_llegar_a_una_VERSION_CONCRETA                         <- *** LA VERSION ***

tests/test_editar_receta.py:
  test_el_detalle_tiene_el_formulario_conectado
  test_editar_DICE_EN_VOZ_ALTA_QUE_CREA_VERSION_NUEVA                 <- *** «SE DICE» + LA VERSION ***
  test_lo_que_no_se_cambia_no_se_manda
  test_SIN_CANTIDAD_NO_SE_INVENTA_UNA                                 <- *** NO SE INVENTA, DECIMA VEZ ***
  test_los_campos_no_bajan_de_16_px                                   <- UX (y es de las buenas)
```

## 2. Y contesta tres clausulas de B07, con las palabras del plan

```
B07 PIDE                                          EL ENSAYO
  «edicion ... VERSION»                             `test_se_puede_llegar_a_una_version_concreta`
                                                    `test_editar_dice_en_voz_alta_que_crea_version_nueva`
  «Editor con CANTIDADES/UNIDADES»                  `test_sin_cantidad_no_se_inventa_una`
  «...»                                             `test_el_404_se_distingue_de_un_fallo`
```

> *** Y `test_editar_dice_en_voz_alta_que_crea_version_nueva` es el mejor nombre de todo B07, *** *porque **dice
> tres cosas a la vez**:*
>
>   1. **que editar CREA UNA VERSION NUEVA** *-- no sobrescribe: *la receta tiene historia;*
>   2. **que lo DICE**, *y «en voz alta»* -- *o sea: **la pantalla avisa**, no lo hace en silencio;*
>   3. **y que eso es una decision que se prueba** *-- *no un detalle de implementacion.*
>
> *** Y es **la misma forma** de las nueve de B06 y de las tres de B05: ***
>
>   - *`test_kg_y_ud_no_se_restan_y_se_dice_por_que` (B05);*
>   - *`test_un_ingrediente_escrito_a_mano_no_entra_y_se_dice` (B05);*
>   - *`test_quitar_dos_veces_da_404_y_no_dice_hecho_cuando_no_ha_hecho_nada` (B05);*
>   - *y ahora **`test_editar_dice_en_voz_alta_que_crea_version_nueva`**.*
>
> *** El proyecto no tiene «no hagas X»: tiene **«no hagas X, Y DILO»** -- *y lo prueba.*

## 3. Y `test_sin_cantidad_no_se_inventa_una` es **la decima**

```
  1) la columna `cantidad` de la despensa    ->  NULL = «no se sabe», que no es 0
  2) `sin_precio`                            ->  «no se sabe el precio», que no es gratis
  3) `diario.fuente_dato`                    ->  de donde viene el dato          (y `NOT NULL`)
  4) `COALESCE` en `anade_linea`             ->  «no llega» no es «llega vacio»
  5) `core/alimentos.py`                     ->  «mezcla», que no es ni «si» ni «no»
  6) `test_un_cero_no_se_confunde_con_no_haber_dato`
  7) `unidad_canon`                          ->  sin unidad, las cifras NO SON COMPARABLES
  8) `FUENTES` + `ValueError`                ->  un origen que no es de los conocidos SE LEVANTA
  9) `DESCONOCIDO` EN LA LISTA               ->  «no se sabe» es un VALOR
 10) *** y `test_sin_cantidad_no_se_inventa_una` -> si no hay cantidad, NO SE PONE UNA ***
```

> *** DIEZ SITIOS. Y el decimo es de recetas -- *o sea: **la regla no es de nutricion, ni de precios, ni de
> despensa**: **es de todo el proyecto**, y **aparece en cada modulo nuevo que se lee**.* ***
>
> *Y **es exactamente lo que el encargo pide**: «**no inventes** calorias, densidad, alergenos, equivalencias,
> objetivos de salud, precios ni costes de viajes» -- *y aqui, **ni cantidades de una receta**.*

## 4. Y B07, con tres rondas, tiene localizado lo siguiente

```
  1) EL EDITOR DE RECETA    -> `test_editar_receta.py` (formulario, cantidad, version) y el detalle
  2) LA IMPORTACION         *** POR MIRAR *** -- `core/importar_receta.py`, que es la clausula con MAS guardas
  3) EL PLAN                *** POR MIRAR *** -- varias comidas, duplicar semana, raciones por ocurrencia
  4) LA COCINA              `core/cocina.py` leido: el temporizador como hora de fin; «sin declarar consumo» POR MIRAR
  5) Y LA VERSION           CON ENSAYO -- `test_se_puede_llegar_a_una_version_concreta`
  6) Y LA ACEPTACION        *** «CINCO RECETAS CON DATOS ... y NO CERRAR POR ENTRAR A CINCO RUTAS VACIAS» ***
                            -> y suena a que hay una prueba de recorrido (`test_prueba_funciones.py`)
```

> *** Y la (6) hay que decirla asi, porque es **la instruccion del propietario puesta como aceptacion**: ***
> **cinco recetas con datos, edicion, version, importacion, cocina, recarga y cambios de semana** -- *y **«no
> cerrar por entrar a cinco rutas vacias»**.*
>
> *** Es decir: **el paquete no se cierra porque las rutas existan; se cierra porque las cinco recetas tienen
> contenido.** ***
