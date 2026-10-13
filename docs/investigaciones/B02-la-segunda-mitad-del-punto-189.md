# B02 · **La segunda mitad del punto 189**: el ritmo **declarado** y el presupuesto de **cuatro anos y medio**

*(13 de octubre de 2026. **Y el ultimo cabo de B02 queda leido -- y es la mejor pieza del paquete.**)*

## 1. Donde estaba

```
`docs/SUPERAPP-EJECUCION.md:914`  *** ### G09, punto 189: «Lidl entra, y con presupuesto» ***
   y la fila de la tabla: `| *** 189 *** `ORDEN` sin Lidl; presupuesto y resumen | *** ✓✓ *** ... |`
```

> *** O sea: **el punto 189 tiene tres piezas, y la tabla lo marca `✓✓` -- hecho.** *
>
> *** Y **`run.py` decia «la **primera** mitad del punto 189»**: *o sea, **la (1)** -- *y **las otras dos estaban aqui.** *

## 2. Las tres piezas, y la mejor es la (2)

```
**(1) Lidl esta en `ORDEN`.** `_en_paralelo` resuelve el colector por nombre de modulo (`importlib.import_module`),
     asi que *** entraba con una palabra y no estaba ***; va al final, porque `ORDEN` tambien es el orden de LECTURA
     de los resultados.

**(2) Su ritmo esta declarado.** Era un `RITMO.get("lidl", 1.0)` *** IMPLICITO ***: *** «un valor que nadie habia
     elegido y que no se podia revisar» ***. Declarado con el mismo 1.0 -- *** «no cambia lo que pasa, cambia que se
     pueda ver y discutir» ***.

**(3) Y el presupuesto, que es la «cifra artificial» del titulo.** `--limite` valia *** 3 ***, y la cola real de Lidl
     son *** 5.026 pendientes ***: *** 1.676 ejecuciones, CUATRO AÑOS Y MEDIO *** para una sola [pasada]...
     -> *y la solucion:* *** `LIMITE_POR_EJECUCION = 1000` -> 6 ejecuciones (~1,7 h de red) -> 6 dias ***
     -> *y es lo que G08 pide calcular en su 179: «tres fichas por ejecucion no acreditan cobertura completa».*
```

> *** Y la (2) es **la mejor frase de todo el proyecto**, y hay que subrayarla: ***
>
> > *** «Era un `RITMO.get("lidl", 1.0)` implicito: *** UN VALOR QUE NADIE HABIA ELEGIDO Y QUE NO SE PODIA REVISAR. ***
> > Declarado con el mismo 1.0 -- *** NO CAMBIA LO QUE PASA, CAMBIA QUE SE PUEDA VER Y DISCUTIR. ***» ***
>
> *** O sea: **declararlo no cambia ni un segundo del ritmo** *** -- *y **cambia todo lo demas**: *un `1.0` **dentro
> de un `get`** es **una decision escondida**; *y **el mismo `1.0` escrito a la vista** es **una decision revisable.** *
>
> *** Y es **la misma familia que todo lo demas**, en su forma mas pura: *** *** `fuente_dato NOT NULL` · `FUENTES`
> vacia · `ABSTIENE` · `razon_declarada` · y ahora **un ritmo que se declara para poder discutirlo.** *
> *** Decimotercera forma. ***
>
> *** Y la (3) es **la que contesta el titulo**: *** *** «con presupuesto» *** -- *y el presupuesto es **un numero
> medido contra otro**: *3 por pasada -> **cuatro anos y medio**; *1000 por pasada -> **6 dias.** *
> *** Que es **el parametro que convierte «no se puede» en «seis dias»**, *y esta elegido **a la vista.** *

## 3. Y entonces **el punto 189 esta entero**, y B02 se cierra del todo

```
B02 PEDIA:
  *** «Integra Lidl en el MISMO ciclo diario y en API/UI como sexta fuente, con ambito regional y cobertura
      demostrados. NO LO DECLARES COMPLETO POR TENER UN SITEMAP.» ***

Y LO MEDIDO, ENTERO:
  *** (1) en el ciclo ***          `ORDEN = [..., "lidl"]` (run.py:40) · y «entraba con una palabra»
  *** (2) con su ritmo declarado *** `RITMO` explicito, y **el mismo 1.0**: «cambia que se pueda ver y discutir»
  *** (3) y CON PRESUPUESTO ***      `LIMITE_POR_EJECUCION = 1000` -> **6 ejecuciones, ~1,7 h, 6 dias**
                                    *(contra `--limite = 3`, que daban **1.676 ejecuciones y cuatro anos y medio**)*
  *** y en API/UI ***               B03: la superficie, la columna `region`, la cobertura por zona
  *** y «no por un sitemap» ***     *el alcance esta DICHO, y su limite tambien*

*** Y la unica cosa que queda de B02 es la prediccion con hora: ***
   *** mañana 14/10 a las 06:00 ***, y la linea que la comprueba:
   `Get-Content data\runs.csv -Tail 8 | Select-String lidl`
```

> *** Y **con esto, el paquete que mas correcciones costo** *(10 de las 10 de la sesion)* **queda cerrado con tres
> piezas medidas y una prediccion fechada** *** -- *y **su defecto insignia escrito en el codigo**: *«el dia seguia sin
> Lidl, **con un aviso en el log que parecia una precaucion**». *
>
> *** Y **no se declara cerrado del todo**: *** *se declara **cerrado salvo una comprobacion con hora**, *que **es lo
> que se puede decir sin mentir.** *
