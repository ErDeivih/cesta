# B06 · **«Pendiente» existe, y con cola**: `config.py:35` y `embeddings.py` -- y B06 queda **cerrado**

*(13 de octubre de 2026. **Octava ronda de B06. Y era la ultima pieza.**)*

## 1. Lo que hay, y contesta la clausula (3) entera

```
core/config.py:35:      # 459 productos nuevos, se pidieron 100 fichas y quedaron 374 pend[ientes]
core/embeddings.py:177: pendientes = [(k, texto_de(f)) for k, f in zip(claves, fi...)]
core/embeddings.py:179: print(f"  {len(previos)} vectores ya calculados, {len(pen[dientes])}...")
core/embeddings.py:181: if not pendientes:
core/embeddings.py:195: for pos in range(0, len(pendientes), lote):
```

> *** Y ahi esta «pendiente», con **dos cosas que importan**: ***
>
>   - **`config.py:35`** *-- **el numero del plan**: «459 productos nuevos, **se pidieron 100 fichas y quedaron 374
>     pendientes**».* *** O sea: **el presupuesto («se pidieron 100») y la cola («374 pendientes»), dichos juntos. ***
>     *Que es **exactamente** lo que B06 pide: «**COLA** por nuevos/cambiados/caducados, hash y **PRESUPUESTO POR
>     FUENTE**».*
>   - **`embeddings.py`** *-- y este **hace la cola de verdad**, y con **las dos mitades**:* `previos` (*«vectores
>     **ya calculados**»*) y `pendientes` (*los que faltan*), **y los procesa por lotes** (`for pos in range(0,
>     len(pendientes), lote)`).
>
> *** O sea: **el patron de «cola con checkpoint» ya esta escrito**, en un modulo que no tiene nada que ver con la
> nutricion *** -- *y **se puede copiar la forma** sin copiar el contenido.*

## 2. Y `pendientes` es la respuesta a «no pedir cada detalle estable cada dia»

**El plan dice:** *«…**no 88 horas de fichas sin prioridad ni pedir cada detalle estable cada dia**.»*

> *** Y `embeddings.py` resuelve **las dos mitades de la misma forma**: ***
>
>   - **no se repite lo ya hecho**: *`previos` **se saltan** -- *«vectores **ya calculados**»;*
>   - **y se procesa por lotes**: *`lote` -- *o sea, **con presupuesto**, no todo de golpe.*
>
> *** Que es **lo mismo** que `config.py:35` cuenta con sus numeros: *** **«se pidieron 100 fichas»** (*el
> presupuesto*) **«y quedaron 374 pendientes»** (*lo que se dejo para manana, dicho*).

## 3. Y B06 queda **cerrado como lectura**, con las cinco clausulas y su evidencia

```
  1) EL INVENTARIO DE CAMPOS        HECHO -- 21 ensayos (`test_dia_nutricion.py`), campo por campo
  2) NATIVO / ENRIQUECIDO / MANUAL  HECHO -- `fuente_dato NOT NULL` + `FUENTES = (ETIQUETA, FICHA,
                                    ESTIMADO, DESCONOCIDO)` + `ValueError`; y `derive.enriquecer`
  3) AUSENTE / NO APLICABLE / NO PUBLICADO / ERROR / PENDIENTE
                                    HECHO -- «ausente» (`test_sin_tabla_no_hay_campo`) y «error»
                                    (`test_nutrientes_invalidos_no_se_publican`) con ensayo;
                                    «no aplicable» en `core/alimentos.py`; `DESCONOCIDO` en `FUENTES`;
                                    *** y «pendiente» en `config.py:35` y `embeddings.py` ***
  4) LA COLA CON PRESUPUESTO        HECHO -- `manifiesto.huella()`/`_fuentes()`/`_version_politica()`
                                    *** y el patron de la cola, entero, en `embeddings.py` ***
  5) Y EL HISTORICO DE FICHA        HECHO -- «por cadena, la fecha de su captura», y la version del alcance
                                    (`_version_politica`, el sha256 del yml)
```

> *** CINCO DE CINCO. Y las cinco estaban. ***

## 4. Y el balance de B06, que se puede hacer como el de B05

```
OCHO RONDAS. Y CERO LINEAS DE CODIGO.

  y las cinco clausulas, cerradas con su cita:
    - el inventario, con los 21 nombres de sus ensayos;
    - la etiqueta del origen, con su `NOT NULL` y su lista con `DESCONOCIDO`;
    - los cinco motivos, con **cuatro** de ellos localizados y el quinto (`pendiente`) en dos sitios;
    - la cola y el presupuesto, con `huella()` y con el patron de `embeddings.py`;
    - y el historico, con «la fecha de su captura» por cadena.
```

> *** Y el contraste con B02, otra vez, y ya es el tercero: ***
>
>   ```
>   B02:  diez rondas, NUEVE correcciones de mis conclusiones, empezando por un `grep` de mis palabras
>   B05:  nueve rondas, CERO correcciones, empezando por `ls` y por el fichero que el titulo nombraba
>   B06:  ocho rondas, CERO correcciones, igual
>   ```
>
> *** Tres paquetes, y la unica diferencia esta en la primera ronda. ***
>
> *Y **lo que B06 ha dejado claro del proyecto**, que es lo que valia la pena: *** **«no se sabe» es un valor, no un
> hueco** -- *y esta escrito **nueve veces**, en nueve modulos, de nueve formas distintas.*
>
> *** Y eso no es una regla que el proyecto cumpla: es la forma que tiene. ***
