# B05 · **Los nueve ensayos de la despensa**, y dos son **las restricciones del propietario**

*(13 de octubre de 2026. **Septima ronda de B05. Y la clausula 4 esta cerrada con nombre y apellido.**)*

## 1. Los nueve, por su nombre

```
tests/test_fase2_f11_despensa.py:

  test_consumo_parcial_descuenta_lo_que_queda
  test_gastarlo_todo_borra_la_existencia_y_no_deja_un_cero          <- «no se sabe» NO es «cero»
  test_sin_saber_cuanto_hay_consumir_lo_deja_desconocido_y_lo_dice   <- el NULL, dicho
  test_kg_y_g_son_la_misma_unidad
  test_kg_y_ud_no_se_restan_y_se_dice_por_que                       <- *** NO INVENTA EQUIVALENCIAS ***
  test_una_unidad_que_no_se_conoce_no_se_resta                      <- *** NO INVENTA ***
  test_la_fecha_es_opcional_y_una_sin_fecha_no_es_un_problema
  test_no_hay_ninguna_funcion_que_sume_una_compra                   <- *** «COMPRA NO ES CONSUMO» ***
  test_lo_que_falta_separa_disponibles_de_faltantes_y_dice_el_motivo
```

## 2. Y dos de los nueve son las restricciones del propietario, **literales**

```
RESTRICCION DEL PROPIETARIO:  «Compra no es consumo: el plan calcula nutricion prevista; el diario
                               solo registra las porciones confirmadas por cada persona.»
   -> test_no_hay_ninguna_funcion_que_sume_una_compra          *** Y ADEMAS ES UN ENSAYO, NO UNA PROMESA ***

RESTRICCION DEL PROPIETARIO:  «no inventes calorias, densidad, alergenos, EQUIVALENCIAS, objetivos de
                               salud, precios ni costes de viajes»
   -> test_kg_y_ud_no_se_restan_y_se_dice_por_que              *** «se dice por que»: no se resta, Y SE EXPLICA ***
   -> test_una_unidad_que_no_se_conoce_no_se_resta             *** y si no se conoce, no se resta ***
```

> *** Y fijate en la forma del segundo: *** *`no_se_restan` **y** `se_dice_por_que`.* *O sea: **no solo no inventa
> la equivalencia -- dice por que no la inventa**.*
>
> *Que es exactamente lo que el encargo pide cuando dice «**no inventes**»: **no basta con no inventar; hay que
> decir que no se sabe** -- *y eso es **una respuesta**, no un hueco.*
>
> *** Y es la misma doctrina de la columna `cantidad` que admite NULL: «no se sabe cuanto queda» es un dato, y
> **«no queda» es otro**. **Los dos ensayos con `no` en el nombre son el contrato.** ***

## 3. Y B05 queda **a una clausula** -- la mas de «plan»

```
  1) RECIBO Y HUELLA                HECHO -- Operacion + clave() + id_de_linea() + 8 ensayos
  2) CONFLICTO, NO EXITO FICTICIO   HECHO -- `id uuid PRIMARY KEY`, garantizado por la BASE
  3) CONCURRENCIA Y MEDIA LISTA     HECHO -- `borrado_en` + las dos razones del comentario
  4) RESERVAS DE DESPENSA           HECHO -- `017_la_despensa.sql` + **9 ensayos, dos de ellos del propietario**
  5) CALCULO INCREMENTAL DEL PLAN   *** POR MIRAR ***
  6) DESTINO DISTINTO               HECHO -- B04
```

> *** Y la que queda es una sola, y es la unica que habla del PLAN ***: *que **editar un menú** no borre las
> **líneas manuales** de compra **ni duplique todas las necesidades**.*
>
> *Y suena a `018_la_cocina.sql` (3,3 KB) y a un modulo de planes -- *y **no se dice nada, porque no se ha mirado**.*

## 4. Y el metodo, medido en siete rondas de B05

```
RONDA 131  el criterio desglosado, doce ficheros localizados            -- sin abrir ninguno
RONDA 132  core/traspaso.py: docstring + seis nombres + 8 ensayos       -- 4 clausulas
RONDA 133  almacen.py + el esquema: `id uuid PRIMARY KEY`               -- 5 clausulas, y la BASE
RONDA 134  017_la_despensa.sql: la regla EN EL DDL                      -- 4a clausula
           y test_fase2_f11_despensa.py: 9 ensayos, dos del propietario
```

> *** Siete rondas, cinco clausulas cerradas, **todas con cita**, y **ninguna** con «no existe», «y nada mas»,
> «hay que construirlo» ni «ya esta» sin su linea. ***
>
> **Y el contraste con B02 es el que hay que dejar escrito**: *B02 tardo **diez rondas** en saber lo que habia, y
> produjo **nueve correcciones** de mis conclusiones -- *porque empezo con **un `grep` de mis palabras**.*
>
> *** B05 empezo con `ls`, siguio por el fichero que **el titulo del paquete nombraba**, y luego **leyo los
> nombres de los ensayos**. *** *Que es la unica diferencia, y lo unico que hay que repetir en B06.*
