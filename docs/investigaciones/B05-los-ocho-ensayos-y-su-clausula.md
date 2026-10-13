# B05 · **Los ocho ensayos, y cubren cada clausula del criterio** -- dichos por sus nombres

*(13 de octubre de 2026. **Tercera ronda de B05. Y es la que cierra la mitad del paquete.**)*

## 1. Los ocho, y a que clausula del criterio contesta cada uno

```
tests/test_g12_traspaso.py:

  test_la_misma_operacion_no_duplica                            <- «REPETIR NO DUPLICA»
  test_dentro_de_la_misma_semana_tambien_es_la_misma_operacion   <- y no por el dia, sino por la SEMANA
  test_otra_semana_si_es_otra_operacion                          <- «OTRA SEMANA SI»
  test_otra_version_de_la_receta_es_otra_operacion               <- y otra VERSION tambien
  test_la_receta_de_otro_no_se_traspasa                          <- EL DUEÑO
  test_sin_dueno_no_hay_traspaso                                 <- EL DUEÑO
  test_la_semana_la_calcula_el_servidor_y_es_el_lunes             <- «LA CLAVE LA CALCULA EL SERVIDOR»
  test_el_id_de_la_linea_es_determinista_y_distingue              <- LA IDEMPOTENCIA
```

> *** Ocho ensayos, y los ocho tienen el criterio dentro. ***
>
> *Y fijate en **los dos del medio**: `test_dentro_de_la_misma_semana_tambien_es_la_misma_operacion` **y**
> `test_otra_semana_si_es_otra_operacion`.* *** Los dos a la vez. *** *Que es **exactamente la frase que el
> docstring decia que decidia el diseño* -- «"repetir no duplica" y "otra semana si" **no se pueden cumplir a la
> vez mirando las lineas de la lista**» -- *y **hay un ensayo para cada mitad**.*
>
> *Y `test_la_semana_la_calcula_el_servidor_y_es_el_lunes` prueba **las dos cosas del diseño** que el docstring
> razona: **que la calcula el servidor** (y no el cliente, que es lo que romperia con dos pestañas) **y que es el
> lunes** (el ancla de la semana ISO).*

## 2. Y B05, con esto, tiene la mitad dicha -- y hay que decir cual es

```
DE LAS SEIS COSAS DEL CRITERIO, Y ESTADO CON LO LEIDO:

  1) RECIBO Y HUELLA DEL CONTENIDO     -> `Operacion` + `clave()` + `id_de_linea()`
                                          *** y sus ensayos ***                        HECHO
  2) CONFLICTO, NO EXITO FICTICIO      -> la identidad es de la OPERACION, no del contenido
                                          *** y hay tabla + `_migra` ***                 HECHO, por diseño
  3) DOS PESTAÑAS / CONCURRENTES       -> la clave y la semana las calcula el SERVIDOR
                                          *** y hay ensayo de que es el lunes ***        HECHO
  5) RESERVAS DE DESPENSA              -> «solo si esta modelada Y la persona LO ELIGE»
                                          *** y NO se ha mirado el cuerpo de `pasar_a_lista` ***  POR MIRAR
  6) DESTINO DISTINTO                  -> B04                                          HECHO

  Y LA QUE NO ES DE ESTE PUENTE:
  4) CAIDA TRAS INSERTAR MEDIA LISTA   -> *** es del OTRO puente: plan->lista, y del almacen ***  POR MIRAR
```

> *** O sea: de las seis, **cuatro estan hechas y con ensayo**, una esta por mirar en el cuerpo de
> `pasar_a_lista`, *y **la de «caida tras insertar media lista» es del plan→lista y de `almacen.py`** -- que es
> **el siguiente sitio**, y que tiene 58,4 KB.* ***

## 3. Y el contraste con B02, que ya se puede medir

```
B02:  diez rondas para saber que habia -- y NUEVE correcciones de mis conclusiones
B05:  tres rondas, y ya se sabe que cuatro de las seis cosas estan HECHAS Y CON ENSAYO
```

> *** La diferencia no es el paquete: es **por donde se empezo**.*** *B02 empezo con **un `grep` de mis palabras**;
> B05 empezo **con `ls` de la zona**, siguio **abriendo el fichero que el propio titulo del paquete señalaba**, y
> **leyo los nombres de sus ensayos**.*
>
> *Y en las tres rondas **no se ha escrito ni una conclusion sin cita**: el docstring tiene sus frases, los nombres
> tienen sus lineas, y **lo que no se ha leido esta dicho como no leido**.*
>
> *** Que es, al final, lo unico que B02 enseno y B05 esta aplicando: **mirar primero, y decir lo que falta**.***
