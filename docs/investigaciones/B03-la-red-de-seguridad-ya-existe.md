# B03 · **La red de seguridad ya existe, y es el precedente exacto**

*(13 de octubre de 2026. **Iba a escribir la prueba de «sin zonas, sale lo mismo». Y ya estaba escrita -- dos
veces.**)*

## 1. Lo que se encontro

`tests/test_invariante_reparto.py` -- **8 pruebas, y todas pasan**:

```
test_rechaza_la_union_que_dejaria_una_cadena_repetida      <- LA INVARIANTE
test_admite_el_duplicado_legitimo_con_el_mismo_ean
test_sin_el_parametro_se_comporta_como_antes               <- *** EL CASO «SIN ZONAS» ***
test_un_producto_sin_ean_no_se_da_por_el_mismo_que_otro
test_dos_nombres_que_se_contradicen_no_van_al_mismo_grupo
test_el_que_calla_no_bloquea
test_una_entera_y_una_semidesnatada_sin_lactosa_no_son_el_mismo_producto
test_sin_el_parametro_de_nombres_nada_cambia               <- *** Y ESTE TAMBIEN ***
```

> **Los dos que yo iba a escribir «primero» ya existen.** *Y no por casualidad: **`cadenas` y `nombres` se
> anadieron con el mismo problema que la zona** -- meter una invariante nueva en `agrupar_enlaces` **sin cambiar
> el comportamiento cuando no viene**.*
>
> *Y quien los anadio dejo escritas las dos pruebas que lo garantizan:*
>
>   - **`test_sin_el_parametro_se_comporta_como_antes`** -- *el parametro `cadenas`*
>   - **`test_sin_el_parametro_de_nombres_nada_cambia`** -- *y el parametro `nombres`*

## 2. Y eso convierte «generalizar la invariante» en un cambio con precedente

**La zona no es un caso nuevo: es el tercero.**

```
1º  cadenas   -> parametro nuevo + test_sin_el_parametro_se_comporta_como_antes
2º  nombres   -> parametro nuevo + test_sin_el_parametro_de_nombres_nada_cambia
3º  regiones  -> y la prueba se llamara test_sin_el_parametro_de_zonas_nada_cambia
```

> **O sea: el trabajo que queda en `agrupar_enlaces` no hay que inventarlo.** *Hay que **copiar la forma** de lo
> que ya se hizo dos veces --* y **el molde esta en el mismo fichero, con su prueba al lado.**
>
> **Y eso es lo mismo que se encontro en la ronda 74 con `grupos_de`**: *la pieza que parecia un diseno **ya
> estaba hecha, para otra cosa**.* *Primero para las cadenas; ahora, **tambien en las pruebas**.*

## 3. Y la condicion queda escrita con su nombre exacto

*Lo que hay que hacer, entonces, es esto y nada mas:*

  1. **`agrupar_enlaces(..., regiones: list[str] | None = None)`** *-- igual que `cadenas` y `nombres`*;
  2. **que la union por cadena se haga por `(cadena, zona)`** *cuando la zona viene*;
  3. **y que con `regiones=None` salga exactamente lo mismo que hoy** *-- que es lo que
     `test_sin_el_parametro_se_comporta_como_antes` ya vigila para el caso de al lado*;
  4. **y una prueba nueva**: `test_sin_el_parametro_de_zonas_nada_cambia`.

> **Y el paso 3 es el unico que puede romper algo**, *y por eso es el que tiene prueba de las dos formas: **la
> que ya existe** -- *que seguira corriendo* -- **y la que hay que anadir**, *con el nombre que la hace
> reconocible.*

## 4. Y lo que esto dice del estado de B03, que es lo importante

*En la ronda 75 se dijo:* **«lo que queda es un cambio de tres sitios con una condicion clara»**.

**Y ahora la condicion tiene prueba, precedente y molde:**

```
HECHO:        la zona en donde_comprar (si esta)                 -- f952c80
HECHO:        la zona en la clave que se hereda (si esta)        -- 0d1a50c
MEDIDO:       grupos_de -- la zona al lado de `cadenas`
MEDIDO:       agrupar_enlaces -- hay que generalizarla
Y CON PRECEDENTE: los dos parametros anteriores, CON SU PRUEBA CADA UNO
FALTA:        (1) escribir los tres pasos de arriba
              (2) que la clave con la que se hereda incluya la zona
              (3) y que donde_comprar haga algo con ella -- la decision esta escrita
```

> **O sea que B03 termina en un cambio que ya se ha hecho dos veces en ese mismo fichero**, con la prueba que lo
> vigila, y **con la decision de la comparacion ya tomada** -- *«comparar solo dentro de la misma zona, y decir
> cuando no hay con quien»*.
>
> *De las nueve medidas, **ninguna dejo una incognita**; y las tres que parecian diseno **resultaron ser
> precedentes**.*
