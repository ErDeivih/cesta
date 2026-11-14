# Las cifras de la ultima ejecucion

**Ejecucion del 14 de noviembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **58.261** |
| grupos comparables | **9.431** |
| productos comparables por kg/l/m | **47.036** |
| productos con codigo de barras | **25.648** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **12.738** |
| productos con certificado | **1.140** |
| productos con Nutri-Score | **8.496** |
| productos con tabla nutricional | **3.905** |
| productos con envase | **8.970** |

## Historico

    3.092.702 filas, 69 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 28.320 | 0 | 8.858 s | 2026-11-14 |
| carrefour | 16.765 | 1 | 5.247 s | 2026-11-14 |
| dia | 5.700 | 0 | 701 s | 2026-11-14 |
| mercadona | 4.276 | 0 | 103 s | 2026-11-14 |
| aldi | 3.043 | 0 | 105 s | 2026-11-14 |
| lidl | 157 | 0 | 4 s | 2026-11-14 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 5.666 |
| **de tarjeta** (no bajan lo que pagas en caja) | **1.620** |
| **solo por internet** (no bajan el ticket de la tienda) | **87** |
| ofertas que cuentan de verdad | 3.959 |
