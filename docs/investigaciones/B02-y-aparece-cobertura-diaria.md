# B02 · **Y aparece `cobertura_diaria.py`** -- la quinta cosa que ya existia

*(13 de octubre de 2026. **La quinta de B02, y ya no sorprende: sorprenderia lo contrario.**)*

## 1. Lo que hay

```
projects/cesta/cobertura_diaria.py

  docstring:  «Por que existe, habiendo ya un control de cobertura.
               En `core/cobertura.py` hay dos ...»

  uso:        uv run python -m projects.cesta.cobertura_diaria                 # hoy
              uv run python -m projects.cesta.cobertura_diaria --fecha ... --dias 30
```

> **Hay un modulo dedicado a la cobertura diaria, con su CLI, su `--fecha` y su `--dias`** -- *o sea: **sabe
> hacerlo por dia y por ventana de dias**, que es mas de lo que el fichero de Lidl hace.*
>
> **Y su docstring empieza explicando por que existe *ademas* de `core/cobertura.py`** -- *que es la pregunta que
> yo iba a hacerme, contestada por quien lo escribio.*

## 2. Y esto ya es la quinta, y las cinco son de B02

```
1) RetoWAF y el backoff de Alcampo            -- resistencia entera
2) VUELTAS_DE_RESCATE y el backoff exponencial de Carrefour
3) tests/test_waf_alcampo.py y tests/fixtures/  -- el ensayo del WAF y la carpeta
4) core/cobertura.py                          -- la revision de cobertura
5) projects/cesta/cobertura_diaria.py         -- Y LA COBERTURA DIARIA, CON SU CLI
```

> **Cinco cosas, y las cinco estaban ahi.** *Y las cinco se encontraron **en las ultimas cuatro rondas**, despues
> de que las seis primeras dijeran cosas como «no existe nada» y «hay que construirlo».*
>
> *Y lo que cambió entre unas y otras **no fue el esfuerzo: fue la herramienta**.* *Las seis primeras buscaron con
> `grep` y **mis palabras**; las cuatro ultimas **miraron el directorio y leyeron los ficheros que salieron**.*

## 3. Y lo que esto dice de B02, que es lo unico que queda por decir

**Antes de escribir una linea de B02, hay que leer `cobertura_diaria.py` entero.** *Porque:*

  - **si ya escribe el fichero por cadena y por dia**, *entonces **la parte 1 de B02 esta hecha** y solo falta
    **metersela en el ciclo** -- *que es el mismo caso que el veto de Lidl, que estaba en una linea y no corrió
    nunca porque `run.py` llamaba `main()` sin argumentos;*
  - **y si no lo hace**, *entonces **el sitio y la forma ya estan escritos**, y solo falta rellenarlo.*

> **En los dos casos, escribir antes de leerlo seria el error de la ronda 105 otra vez.** *Y ya van cinco.*

## 4. Y la regla, con su quinta confirmacion

```
1) ls        -- que hay
2) leer los ficheros que salgan, ENTEROS
3) y solo despues, grep -- con los nombres del codigo
```

> **`cobertura_diaria.py` tiene un docstring que contesta la duda que yo tenia.** *Eso es lo que hace un docstring
> bien escrito: **deja la pregunta contestada para el que venga despues**.*
>
> *Y **no se lee con `grep`**: se lee abriendo el fichero.* *Que es, otra vez, lo mismo que estas cinco rondas
> han estado aprendiendo.*
