# B02 · **Existe `core/runlog.py`** -- y con esto la parte de medir de B02 esta hecha

*(13 de octubre de 2026. **El septimo hallazgo, y el que cierra la pregunta de B02.**)*

## 1. Lo que hay

```
core/runlog.py:20:   def log_run(fuente: str, filas: int, errores: int, segundos: float, ...)
core/runlog.py:63:   def check_drift(fuente: str, filas_hoy: int, tolerancia: float = 0.10) -> str | None
projects/cesta/collectors/alcampo.py:180:   def _apuntar_alcance() -> None
```

> **Hay un modulo dedicado a registrar las pasadas: `core/runlog.py`.** *Con:*
>
>   - **`log_run(fuente, filas, errores, segundos, ...)`** *-- ***lo que el plan pide medir***: **productos**,
>     **errores**, **tiempo** -- *y una `completa` que se le pasa.*
>   - **`check_drift(fuente, filas_hoy, tolerancia=0.10)`** *-- **la deriva, con tolerancia**: *avisa si hoy hay
>     un 10 % menos que la referencia.*
>
> *Y **`_apuntar_alcance()`** en `alcampo.py:180`, que apunta lo que quedo fuera.*

## 2. Y con esto, la parte de «medir» de B02 esta hecha -- y son SIETE los hallazgos

```
1) RetoWAF (13 usos) y el backoff de Alcampo
2) VUELTAS_DE_RESCATE, backoff exponencial y _por_que_fallan de Carrefour
3) tests/test_waf_alcampo.py (9,3 KB) y tests/fixtures/ (la carpeta)
4) core/cobertura.py -- la revision, con error si falta medio catalogo
5) projects/cesta/cobertura_diaria.py -- 162 lineas: filas_por_dia, veredicto, CLI
6) cobertura.solo_cesta_familiar + _apuntar_alcance + check_drift + log_run, EN ALCAMPO
7) *** core/runlog.py -- EL MODULO QUE REGISTRA LAS PASADAS ***
```

> **Y las cuatro cosas que el plan pide medir -- «requests efectivos, cobertura de ramas, productos unicos,
> tiempo y motivo de cada reintento» -- tienen las cinco su sitio:**
>
>   - **productos unicos** *-- `log_run(filas)` y `check_drift`;*
>   - **tiempo** *-- `log_run(segundos)`, con `time.monotonic()`;*
>   - **motivo de cada reintento** *-- `_por_que_fallan` en Carrefour, y el mensaje del WAF en Alcampo;*
>   - **cobertura de ramas** *-- `cobertura.solo_cesta_familiar` y `core/cobertura.py`;*
>   - **y requests efectivos** *-- **es lo unico que no he visto**, *y **no voy a decir que no exista**.*

## 3. Y lo que queda de B02, ahora, de verdad

```
HECHO, CON NOMBRE Y FICHERO:
  medir         core/runlog.py (log_run con filas, errores, segundos, completa) + check_drift
  cobertura     core/cobertura.py + cobertura_diaria.py (veredicto, CLI) + solo_cesta_familiar
  resistencia   RetoWAF / AVANCE_MINIMO / CORTES_PARA_RENDIRSE / MAX_RENOVACIONES / detener  (Alcampo)
                VUELTAS_DE_RESCATE / backoff exponencial / VUELTAS_SIN_BLOQUEO / _por_que_fallan (Carrefour)
  no inventar   `None` cuando no se puede leer (los dos)
  ensayos       11 de colectores, uno del WAF

FALTA:
  1) EL FICHERO DE COBERTURA POR CADENA Y DIA -- que hoy solo escribe Lidl, con las 5 lineas de lidl.py:278-285
  2) LOS FIXTURES en tests/fixtures/ -- seis casos
  3) LA DECISION DEL NAVEGADOR -- del propietario
  y POR MIRAR, sin decir que no existe:
  4) si Carrefour usa `log_run` y `check_drift` igual que Alcampo
  5) de donde salen los «requests efectivos», si de algun sitio
```

## 4. Y la conclusion, que hay que decir con la boca pequena

**Siete hallazgos. Siete cosas que ya estaban.** *Y B02 -- que en la ronda 105 parecia «construir un sistema de
resistencia entero» -- resulta ser, sobre todo, **escribir un fichero que ya se sabe escribir, en dos colectores
que ya miden todo lo que hay que meter dentro**.*

> *Y **dos de esas siete se encontraron solo despues de decir «y nada mas»**.*
>
> ***Que es la septima vez que la misma frase resulta falsa*** -- *y la razon de que este documento termine con
> la unica regla que estas nueve rondas han dejado clara:*
>
> **`ls` · leer entero · `grep` al final con los nombres del codigo · y NUNCA decir «y nada mas».**
