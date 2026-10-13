# B02 · **Sexta correccion, y la mas grande**: Alcampo ya mide el tiempo, la deriva y registra la pasada

*(13 de octubre de 2026. **Se leyo `alcampo.py:1014-1031`. Y se caen otras dos conclusiones mias.**)*

## 1. Lo que hay, literal

```python
en_alcance = cobertura.solo_cesta_familiar(df)
if en_alcance.height != df.height:
    print(f"  {df.height - en_alcance.height} productos fuera de alcance: no se guardan", flush=True)
    df = en_alcance
write_parquet(df, "bronze", FUENTE)
_apuntar_alcance()
filas = df.to_dicts()

segundos = time.monotonic() - t0
aviso = check_drift(FUENTE, len(filas))
log_run(FUENTE, len(filas), errores, segundos, completa)
if aviso:
    print(f"  {aviso}")
print(f"{FUENTE}: {len(filas)} productos, {errores} errores, {segundos:.0f}s")
```

> **Y ahi esta, otra vez, casi todo lo que B02 pide:**
>
>   - **`cobertura.solo_cesta_familiar(df)`** *-- **usa `core/cobertura`**, que es **la misma funcion que el
>     control de cobertura**, y el comentario lo dice: «**para que colector y control no discrepen**».*
>   - **`_apuntar_alcance()`** *-- **apunta el alcance**. *O sea: **hay un registro del alcance**, y no lo vi.*
>   - **`segundos = time.monotonic() - t0`** *-- ***MIDE EL TIEMPO***. ✗ *Yo dije que era «lo unico que no se
>     mide».*
>   - **`check_drift(FUENTE, len(filas))`** *-- **comprueba la deriva**: *si hoy hay mucho menos que ayer.*
>   - **`log_run(FUENTE, len(filas), errores, segundos, completa)`** *-- ***Y REGISTRA LA PASADA***, con
>     productos, errores, segundos **y si fue completa**.*

## 2. Y entonces caen DOS conclusiones mas, y ya van seis

```
RONDA 111 dije:  «los colectores guardan write_parquet y save_raw, Y NADA MAS»        FALSO
                 -> hay `log_run`, `_apuntar_alcance`, `check_drift` y `cobertura.solo_cesta_familiar`
RONDA 112 dije:  «de las cuatro cosas que el plan pide medir... EL TIEMPO es lo unico que no se mide»   FALSO
                 -> `segundos = time.monotonic() - t0`, y va a `log_run`
```

> **Y las dos salieron de lo mismo:** *mire `save_raw` y `write_parquet` con un `grep`, **vi dos nombres, y
> concluí «y nada mas»**.*
>
> ***«Y nada mas» es la conclusion mas peligrosa que se puede sacar de un `grep`**: porque **un `grep` solo
> encuentra lo que buscas**, y **«nada mas» afirma sobre lo que NO buscaste**.*

## 3. Y B02, tras seis correcciones, es casi nada -- y hay que decirlo

```
HECHO YA:
  Alcampo      RetoWAF (13 usos) · AVANCE_MINIMO · CORTES_PARA_RENDIRSE · MAX_RENOVACIONES · `detener`
               · abre navegador para el reto · cobertura.solo_cesta_familiar · _apuntar_alcance
               · check_drift · log_run(errores, segundos, completa) · Y MIDE EL TIEMPO
  Carrefour    VUELTAS_DE_RESCATE · backoff exponencial · VUELTAS_SIN_BLOQUEO · _por_que_fallan
  los dos      no inventan catalogo cuando no pueden leer
  core/        cobertura.py (la revision) · cobertura_diaria.py (filas_por_dia, veredicto, CLI)
  tests/       11 ensayos de colectores, uno del WAF (9,3 KB)

LO QUE FALTA, Y HAY QUE MEDIRLO ANTES DE DECIRLO:
  1) ¿que escribe `log_run` y donde?      <- NO SE HA MIRADO, Y ES LO PRIMERO
  2) ¿que apunta `_apuntar_alcance()`?
  3) ¿Carrefour tiene `log_run` y `check_drift`?  <- NO SE HA MIRADO
  4) el fichero de cobertura POR CADENA Y DIA -- que hoy solo escribe Lidl
  5) los FIXTURES
  6) la decision del navegador (del propietario)
```

> **Y fijate en que las tres primeras son «no se ha mirado»** *-- *no «no existe».* **Que es exactamente la
> distincion que he confundido seis veces.**

## 4. Y la regla, corregida por sexta vez -- y esta vez con la palabra que faltaba

```
1) ls                          -- que hay
2) leer los ficheros, ENTEROS  -- y no veinte lineas
3) y grep al final, con los nombres del codigo
4) *** Y NUNCA DECIR «Y NADA MAS» ***
```

> **Las seis correcciones tienen la misma forma: una afirmacion sobre lo que NO se miro.** *«No existe nada»,
> «falta la distincion», «una linea y nada mas», «no se sabe si hay fixtures», «el tiempo no se mide»,
> **y ahora «y nada mas»**.*
>
> ***Todas son la misma frase: «lo que vi es todo lo que hay». Y ninguna se puede decir con un `grep`.***
> *Se dice -- cuando se puede decir -- **habiendo leido el fichero entero**.* **Y ni entonces, casi nunca.**
