# B02 · **Y «requests efectivos» existe**: se llama `peticiones`, y estaba en el fichero que leia

*(13 de octubre de 2026. **La octava -- y estaba en la misma pantalla.**)*

## 1. Lo que hay, en `lidl.py:236`

```python
if a.web:
    peticiones.registra_al_salir(FUENTE)          # <- *** PETICIONES ***
    f = Fetcher(rate_per_sec=config.RITMO.get(FUENTE, 1.0))
    if not _robots_permite(f):
        print("  la politica publicada de la web no permite esa ruta: no se pide")
        return 1                                   # <- UNA SALIDA DE FRACASO
    respuesta = f.get(URL)
    save_raw(FUENTE, "ofertas-semanales", respuesta.body)
    html = respuesta.body.decode("utf-8", "replace")
```

> **`peticiones.registra_al_salir(FUENTE)`.** *O sea: **hay un registro de peticiones**, y se llama **al
> salir**.*
>
> ***Eso es «requests efectivos»*** -- *la quinta de las cinco cosas que el plan pide medir, y **la unica que yo
> habia dado por no vista**, escribiendo con cuidado: «es lo unico que NO HE VISTO, y NO VOY A DECIR QUE NO
> EXISTA».*
>
> **Y estaba en `lidl.py`.** *En **el fichero que estaba leyendo** -- **catorce lineas mas arriba** del sitio donde
> miraba.*

## 2. Y esto cierra las cinco medidas del plan, las cinco con nombre

```
requests efectivos       -- `peticiones.registra_al_salir(FUENTE)`   (y existe en los seis, cabe suponer)
cobertura de ramas       -- `cobertura.solo_cesta_familiar` + core/cobertura.py
productos unicos         -- `log_run(filas)` + `check_drift`
tiempo                   -- `time.monotonic() - t0` -> `log_run(segundos)`
motivo de cada reintento  -- `_por_que_fallan` (Carrefour) y el mensaje del WAF (Alcampo)
```

> **Las cinco. Las cinco tienen nombre, fichero y linea.** *Y **ninguna hay que inventarla**.*
>
> *Y de las cinco, **dos las di por no existentes** («el tiempo no se mide», «requests efectivos no lo he visto»), y
> **las dos estaban en ficheros que ya habia abierto**.*

## 3. Y esto deja B02 en su tamano real, que ya no cambia mas

```
LO QUE HAY (ocho hallazgos):
  1) RetoWAF (13 usos) y la resistencia de Alcampo
  2) VUELTAS_DE_RESCATE, backoff exponencial y _por_que_fallan de Carrefour
  3) tests/test_waf_alcampo.py (9,3 KB) y tests/fixtures/
  4) core/cobertura.py -- la revision
  5) cobertura_diaria.py -- 162 lineas, veredicto y CLI
  6) cobertura.solo_cesta_familiar + _apuntar_alcance + check_drift + log_run EN ALCAMPO
  7) core/runlog.py -- el registro de pasadas, con `completa = not detener and errores == 0`
  8) *** `peticiones.registra_al_salir(FUENTE)` -- LOS REQUESTS EFECTIVOS, EN LIDL ***

LO QUE FALTA (y son cuatro cosas pequenas):
  1) Lidl: llamar a log_run -- en el fracaso (0, 1, ...) y en el exito (filas, errores, segundos, completa)
  2) Carrefour y Alcampo: el fichero de cobertura por dia (5 lineas)
  3) los fixtures en tests/fixtures/
  4) la decision del navegador -- del propietario
```

## 4. Y la leccion, que ya no es una regla sino una observacion

**Ocho hallazgos. Ocho cosas que ya estaban.** *Y las ocho se encontraron **leyendo**, ninguna **buscando**.*

> *Y las dos ultimas -- `runlog` y `peticiones` -- **estaban en ficheros que ya habia abierto**.*
>
> ***Lo que faltaba no era informacion: era haber leido esos ficheros enteros.*** *Y por eso la regla termina
> donde termina: `ls`, **leer entero**, y `grep` al final -- *porque **`grep` encuentra lo que buscas, y lo que
> falta es justo lo que no se te ocurrio buscar**.*
>
> **`peticiones` y `runlog`: dos palabras que no estaban en ninguna de mis listas, y las dos en la misma
> pantalla.**
