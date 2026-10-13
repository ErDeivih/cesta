# B15 · **El material de aprendizaje, medido**: 24 capitulos, un modulo de 60 KB, y **veinte ensayos**

*(13 de octubre de 2026. **Segunda ronda de B15. Y la zona tiene mas de lo que parecia.**)*

## 1. Lo que hay

```
plataforma/aprende.py   -- *** 60 KB ***
docs/aprende/           -- *** 24 ficheros ***   (los «diez capitulos» eran los diez primeros alfabeticamente)
tests/test_aprende.py   -- existe, con *** VEINTE ensayos ***
```

## 2. Y los veinte, que son el contrato del material

```
test_lo_que_hay_en_la_carpeta_del_curso_es_del_curso
*** test_cada_capitulo_declara_una_SECCION_CONOCIDA ***
*** test_cada_capitulo_lleva_su_FRASE_EN_UNA_FRASE ***
test_una_pagina_por_documento_y_las_dos_de_estructura
test_el_temario_agrupa_por_secciones_y_en_orden
test_las_rutas_de_la_portada_llevan_a_capitulos_de_verdad
test_cada_capitulo_lleva_su_indice_de_pagina
test_los_enlaces_entre_documentos_apuntan_a_las_paginas
*** test_las_tablas_llevan_su_columna_en_cada_celda ***
test_la_franja_del_boton_de_copiar_no_la_paga_un_bloque_sin_boton
test_una_sola_cabecera_de_pagina_por_documento
*** test_la_pagina_DE_LO_QUE_NO_ESTA_existe_y_lleva_a_donde_si ***
test_el_material_se_regenera_en_la_pasada_del_dia
test_el_markdown_de_verdad_se_pinta
*** test_el_boton_de_copiar_tiene_salida_SIN_PORTAPAPELES ***
*** test_el_sitio_NO_PIDE_NADA_POR_RED ***
*** test_NADA_EN_LINEA_porque_EL_CSP_DE_CADDY_LO_PROHIBE ***
test_el_buscador_va_en_ficheros_y_lleva_todo_dentro
test_la_referencia_tiene_su_pagina_de_indice
test_el_sitio_esta_montado_donde_el_servidor_lo_busca
```

## 3. Y contestan B15, y **la doctrina aparece tres veces**

```
B15 PIDE:  «cada capitulo con EJEMPLO, COMANDO SEGURO, SALIDA ESPERADA Y TEST»
   -> *** y hay un `test_aprende.py` con veinte, y varios son ESTRUCTURALES ***:
      *«una pagina por documento» · «un indice por capitulo» · «una sola cabecera por documento» ·
      «las tablas llevan su columna en cada celda»*
      *** o sea: el material tiene FORMA, y la forma se prueba. ***
```

> *** Y las tres apariciones de la doctrina -- y las tres son nuevas en su forma: ***
>
> ```
> 1) *** test_la_pagina_DE_LO_QUE_NO_ESTA_existe_y_lleva_a_donde_si ***
>    -> *si un capitulo menciona algo que NO existe, **hay una pagina que lo dice, y lleva a lo que si.** *
>    *** Es «no se sabe» convertido en PAGINA. ***
>
> 2) *** test_el_sitio_NO_PIDE_NADA_POR_RED ***
>    -> *el material **no hace NI UNA peticion de red**: *todo va dentro.* *
>    *** Es B14 («no subir datos a una nube») y «los datos no salen de casa» (Ajustes.tsx), aplicado a un sitio. ***
>
> 3) *** test_NADA_EN_LINEA_porque_EL_CSP_DE_CADDY_LO_PROHIBE ***
>    -> *** y este es el mas fuerte: NO ES UNA PROMESA, ES QUE EL CSP LO PROHIBE. ***
>    *Lo mismo que `FUENTES` vacia (B07) y `cocina.py` sin importar el diario: *** la regla esta puesta en el
>    camino, no en el cuidado de quien escribe. ***
> ```
>
> *** Decima forma de imposibilidad, y la primera **impuesta por un servidor**: *** *** el CSP de Caddy **impide** el
> codigo en linea -- *o sea: **no es que nadie lo haya hecho; es que no se puede.** *

## 4. Y hay **dos ensayos que son de B14**, encontrados aqui

```
*** test_el_sitio_no_pide_nada_por_red ***
*** test_nada_en_linea_porque_el_csp_de_caddy_lo_prohibe ***
```

> *** B14 pide: *** *** «CSRF con sesion real de ensayo... *** CORS no sustituye autorizacion de mutacion ***...
> *** logs... y secretos ausentes ***». *
>
> *** Y la parte **del lado del navegador** esta aqui: *** *un sitio que **no pide nada por red** y **cuyo CSP prohibe
> el codigo en linea** -- *que es **la mitad de la superficie** que B14 quiere auditar.* *
>
> *** O sea: **B15 y B14 se tocan**, *y **el material de aprendizaje es, a la vez, un caso de estudio de seguridad**:
> *estatico, sin red, y con CSP.* *

## 5. Y B15 queda con **la zona medida, y una lista de lo que pide contra lo que hay**

```
B15 PIDE                                 LO QUE HAY
  fuente->raw->bronze->silver->gold->API   *** `02-ingenieria-de-datos` ***
  fichas versus precios                     *`06-estadistica-del-catalogo` · `07-indices-de-precios`*
  Parquet/DuckDB/SQLite/PostgreSQL           *en `02` y `03` -- POR COMPROBAR*
  entidades · unidades · matching            *** `03-unidades-y-comparabilidad` · `04-emparejar-productos` ***
  evaluacion del algoritmo                   *** `05-medir-el-emparejador` ***
  costes y promociones                       *** `08-promociones-y-anomalias` ***
  linaje                                     *** POR COMPROBAR -- ¿en `02`? ***
  nutricion                                  *** NO HAY CAPITULO CON ESE NOMBRE ***
  casos de errores reales                    *** POR COMPROBAR ***
  DBT/Dagster: que esta REALMENTE instalado   *** POR COMPROBAR -- y el encargo dice «no decorar el stack» ***
  cada capitulo con test                     *** HAY 20 ENSAYOS, y varios estructurales ***
```

> *** Y **`nutricion` es lo unico que **no tiene capitulo con ese nombre** *** -- *y **es tambien lo unico que B08 dejo
> abierto** (el eje de la PREVISION). *
>
> *** Y **no se dice que falte**: *** *se dice que **no hay capitulo con ese nombre**, *y que **es la segunda vez que
> «nutricion» aparece en una lista del plan y no en el codigo** -- *la primera fue **`_con_precios`, donde estaba
> NOMBRADA** (B08). *
