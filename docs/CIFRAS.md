# Las cifras de la ultima ejecucion

**Ejecucion del 24 de septiembre de 2026.** Este documento tiene un solo trabajo:
llevar los numeros de **hoy**. Lo reescribe entero
`projects/cesta/cifras.py` al final de cada pasada.

Existe porque los demas documentos guardan sus cifras **con la fecha
en que se midieron**, y eso no es una cifra caducada sino un registro:
cambiarla no la actualiza, la falsifica. Asi los numeros de hoy viven
aqui, la historia se queda quieta, y `verificar_docs` encuentra aqui lo
de hoy y deja de avisar sin que nadie tenga que reescribir nada.

    uv run python -m projects.cesta.verificar_docs

---

## Catalogo

| | |
|---|---:|
| productos del catalogo | **57.603** |
| grupos comparables | **9.206** |
| productos comparables por kg/l/m | **45.891** |
| productos con codigo de barras | **25.413** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **12.911** |
| productos con certificado | **713** |
| productos con Nutri-Score | **8.401** |
| productos con tabla nutricional | **3.853** |
| productos con envase | **9.126** |

## Historico

    872.650 filas, 19 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 28.977 | 0 | 5.442 s | 2026-09-24 |
| carrefour | 16.452 | 4 | 3.511 s | 2026-09-24 |
| dia | 5.789 | 0 | 664 s | 2026-09-24 |
| mercadona | 4.319 | 0 | 95 s | 2026-09-24 |
| aldi | 2.066 | 0 | 62 s | 2026-09-24 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 7.848 |
| **de tarjeta** (no bajan lo que pagas en caja) | **576** |
| **solo por internet** (no bajan el ticket de la tienda) | **341** |
| ofertas que cuentan de verdad | 6.931 |
