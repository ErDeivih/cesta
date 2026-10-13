# B02/B03 · **La linea que le falta a Lidl NO es una linea**: `completa` es un veredicto

*(13 de octubre de 2026. **Se fue a anadir `log_run` a Lidl, y el contrato pide algo que hay que decidir.**)*

## 1. Lo que Lidl tiene, y lo que `log_run` pide

```
lidl.py:   t0  1 uso  ·  time.monotonic 0  ·  errores 0  ·  completa 0  ·  segundos 0

core/runlog.py:20:  def log_run(fuente: str, filas: int, errores: int, segundos: float,
                                 completa: bool | None = None) -> None:
```

> **Lidl tiene un `t0` y no lo usa para medir.** *No tiene `errores`, ni `segundos`, ni `completa`.*
>
> *Asi que **no es «una linea»**: hay que **medir el tiempo, contar los errores y -- lo importante -- decidir el
> veredicto**.*

## 2. Y el veredicto es lo que hay que decidir, y su docstring lo explica

```
«Apunta la ejecucion. `completa` es el veredicto del colector.

 La columna `ok` decide dos cosas: si esta captura sirve de referencia para `check_drift`
 y si cuenta como "la ultima vez que salio bien". Durante diecinueve ejecuciones se calculo
 aqui dentro como `errores == 0`, que NO es lo que el colector entiende por buena.

 Carrefour tiene siempre cuatro o cinco categorias que fallan -- papeleria rota, alguna
 difunta -- y las da por buenas porque entran en su tolerancia ...»
```

> **O sea: `completa` es una decision del colector, y no se puede deducir de `errores == 0`.** *Y el docstring
> cuenta que **eso se hizo mal durante diecinueve ejecuciones**.*
>
> *Asi que para Lidl hay que contestar: **¿que es «una pasada buena» de Lidl?*** *Y con lo leido, la respuesta
> esta a la vista: **Lidl captura 79 fichas de ofertas semanales, y su `resumen` ya tiene `fichas_leidas` y
> `guardados`.*** *«Buena» seria **haber leido las ofertas que la pagina publica** -- *y eso **es un juicio que
> Lidl tiene que hacer**, no una resta.*

## 3. Y esto es, con precision, lo que le falta a Lidl

```
MEDIR EL TIEMPO    -- `t0` ya esta; falta `time.monotonic() - t0`
CONTAR ERRORES     -- y decidir que cuenta como error en Lidl
EL VEREDICTO       -- `completa`: que es «una pasada buena» de Lidl, DECIDIDO por su colector
Y LLAMAR           -- log_run(FUENTE, len(filas), errores, segundos, completa)
                     en el mismo sitio que los otros cinco
```

> ***Y el veredicto es la parte que no se puede copiar de Alcampo***: *porque **Alcampo tolera que fallen
> categorias** y **Lidl no tiene categorias** -- *tiene **una pagina de ofertas**.*
>
> **Asi que «completa» para Lidl es otra cosa, y hay que pensarla.** *Que es exactamente lo que el docstring de
> `log_run` avisa: **el veredicto es del colector, y deducirlo de `errores == 0` estuvo mal diecinueve veces**.*

## 4. Y esto completa la octava correccion, que ya no es una correccion sino un encargo

*Lo que empezo como «B02: construir un sistema de resistencia» y paso por siete correcciones **termina en
esto**:*

```
EL TRABAJO DE VERDAD DE B02, CON TODO LEIDO:
  1) Lidl: medir tiempo, contar errores, DECIDIR su veredicto, y llamar a log_run
     -> y NO es copiar de Alcampo: `completa` es distinto para cada colector
  2) Carrefour y Alcampo: escribir su fichero de cobertura por dia (las 5 lineas de lidl.py:278-285)
  3) los FIXTURES en tests/fixtures/
  4) y la decision del navegador (del propietario)
```

> **Y las cuatro son pequeñas, y ninguna era lo que yo creia en la ronda 105.**
>
> *Lo que costo encontrarlas fueron **nueve rondas**, y lo que las encontro no fue buscar mejor: fue **leer lo que
> ya habia y comparar los seis ficheros entre si**.*
>
> **`completa` es un veredicto por colector y no se deduce.** *Esa frase, sola, justifica no haber escrito nada
> hasta ahora.*
