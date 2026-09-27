# Las cifras de la ultima ejecucion

**Ejecucion del 27 de septiembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.824** |
| grupos comparables | **8.829** |
| productos comparables por kg/l/m | **42.563** |
| productos con codigo de barras | **25.527** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.760** |
| productos con certificado | **767** |
| productos con Nutri-Score | **8.442** |
| productos con tabla nutricional | **3.841** |
| productos con envase | **9.106** |

## Historico

    977.746 filas, 21 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.932 | 1 | 15 s | 2026-09-26 |
| carrefour | 16.579 | 4 | 584 s | 2026-09-26 |
| dia | 5.757 | 0 | 620 s | 2026-09-27 |
| mercadona | 4.339 | 0 | 102 s | 2026-09-27 |
| aldi | 2.218 | 0 | 66 s | 2026-09-27 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 7.932 |
| **de tarjeta** (no bajan lo que pagas en caja) | **569** |
| **solo por internet** (no bajan el ticket de la tienda) | **328** |
| ofertas que cuentan de verdad | 7.035 |
