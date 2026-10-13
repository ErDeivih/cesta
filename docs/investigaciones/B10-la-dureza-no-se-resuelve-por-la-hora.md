# B10 · **La dureza**: cinco ensayos, y **no se resuelve por la hora** -- se resuelve por lo que se pidio

*(13 de octubre de 2026. **Quinta ronda de B10. Y esta es la clausula que toca la restriccion del propietario.**)*

## 1. Los cinco, por su nombre (`tests/test_fase2_f07_dos_sesiones.py`)

```
test_la_cantidad_VIEJA_no_gana_por_llegar_despues            <- *** la vieja NO gana por llegar despues ***
test_la_cantidad_NUEVA_gana_si_llega_despues                  <- y la nueva si
test_el_TACHADO_gana_EL_PRIMERO_aunque_llegue_segundo          <- *** ¡el PRIMERO gana, aunque llegue SEGUNDO! ***
test_tachar_dos_veces_no_es_un_error                          <- y repetirlo no es fallo
test_DESTACHAR_GANA_SIEMPRE_SIN_MIRAR_LA_HORA                  <- *** «SIN MIRAR LA HORA» ***
```

## 2. Y contestan la clausula (6) del criterio -- **la que el encargo del propietario pone como restriccion**

```
B10 PIDE:  «REINTENTO/OFFLINE/CONCURRENCIA NO PIERDEN CANTIDADES NI REVOCACIONES»
```

> *** Y los cinco ensayos son **esa frase, repartida**: ***
>
>   - **«no pierden cantidades»** *-> `test_la_cantidad_vieja_no_gana_por_llegar_despues` y
>     `test_la_cantidad_nueva_gana_si_llega_despues`;*
>   - **«ni revocaciones»** *-> `test_el_tachado_gana_el_primero_aunque_llegue_segundo` y
>     `test_destachar_gana_siempre_sin_mirar_la_hora`;*
>   - **y «reintento»** *-> `test_tachar_dos_veces_no_es_un_error`.*
>
> *** O sea: **las cuatro palabras del criterio tienen su ensayo**, y **dos de ellos dicen COMO se resuelve**: ***
> *«**el tachado gana el primero**» y «**destachar gana siempre sin mirar la hora**».*

## 3. Y `sin mirar la hora` es **la clave de todo**, y contestan la restriccion del propietario

**La restriccion, literal:**

> *«reproduce y corrige el fallo de que **300 g** necesarios terminan como **una unidad y una nota de 100 g**,
> **descartando la segunda receta como repetida**. Afecta a **AMBOS** puentes de transferencia (receta->lista y
> plan->lista).»*

> *** Y `test_destachar_gana_siempre_SIN_MIRAR_LA_HORA` dice **la regla que evita ese fallo**: ***
>
> ```
> SI LA DECISION SE TOMA POR LA HORA (timestamp),  el que llega despues PISA -- y si llega tarde, se pierde.
> *** SI SE TOMA POR LO QUE SE PIDIO (semantica), NO HAY CARRERA QUE PERDER. ***
> ```
>
> *** O sea: **«sin mirar la hora» no es un detalle de implementacion: es la razon de que las revocaciones no se
> pierdan.** *** *Si «destachar» dependiera del reloj, **un destachado con reloj atrasado perderia** -- *y es
> **exactamente** lo que el propietario vio: **algo que se descarta por llegar despues.** *
>
> *** Y las otras dos reglas son **la misma idea, en la cantidad**: ***
>
>   - **`test_la_cantidad_vieja_no_gana_por_llegar_despues`** *-- *llegar tarde **no da prioridad**;*
>   - **`test_el_tachado_gana_el_primero_aunque_llegue_segundo`** *-- *y **el orden de llegada tampoco decide**: **el
>     primero que lo pidio** gana, **aunque su mensaje llegue despues**.*
>
> *** Y eso es **`ON CONFLICT (id) DO UPDATE` con `borrado_en` y `COALESCE`** (B05): *el conflicto **pisa con
> contenido**, el borrado **es un campo**, y **un valor ausente no sobreescribe una decision posterior** --
> *o sea: **nada de esto consulta la hora.** *
>
> *** Y es **la septima forma de imposibilidad**... no: es **la tercera vez que la solucion es NO depender del
> reloj** *** -- *y **es la respuesta directa a la restriccion del propietario.** *

## 4. Y B10 cierra con **cinco de seis**, y las dos que faltan dichas

```
  1) LOS ESTADOS           `cambia_linea` + `SIN_CAMBIAR`                          *cuerpo POR LEER*
  2) LAS LISTAS Y EL ORDEN *** HECHO *** -- 15 ensayos
  3) BUSCAR Y FILTRAR      *** POR MIRAR *** -- «marca/formato/EAN y filtros utiles»
  4) LA PAGINACION         MEDIDA -- `limite` con cotas; sin `cursor`/`version`/`offset`
  5) EL GASTO Y EL AHORRO  *** HECHO *** -- 17 ensayos
  6) Y LA DUREZA           *** HECHO: *** 5 ensayos, y **la regla es «sin mirar la hora»**
```

> *** Y las dos que quedan son **(1) el cuerpo de `cambia_linea`, y (3) buscar/filtrar** *** -- *y **las dos son
> codigo** (`cambia_linea` es la funcion que **estos cinco ensayos prueban**), *asi que **leerlas cierra B10 por
> completo.** *
>
> *** Y lo que B10 deja escrito, y es nuevo en la sesion: *** *** la dureza de una operacion concurrente **no se
> compra con un reloj**: se compra **decidiendo por lo que se pidio, y no por cuando llego.** ***
>
> *** Y esa frase **es la respuesta tecnica a la restriccion del propietario**, encontrada **leyendo cinco nombres de
> ensayo** -- *que es **el paso (3) del metodo**, otra vez.*
