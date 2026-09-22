# Las cifras de la ultima ejecucion

**Ejecucion del 21 de septiembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.661** |
| grupos comparables | **6.431** |
| productos comparables por kg/l/m | **40.830** |
| productos con codigo de barras | **25.544** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.840** |
| productos con certificado | **765** |
| productos con Nutri-Score | **8.448** |
| productos con tabla nutricional | **3.853** |
| productos con envase | **9.144** |

## Historico

    751.000 filas, 16 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.776 | 0 | 1.402 s | 2026-09-21 |
| carrefour | 16.560 | 3 | 984 s | 2026-09-21 |
| dia | 5.808 | 0 | 23 s | 2026-09-21 |
| mercadona | 4.327 | 0 | 94 s | 2026-09-21 |
| aldi | 2.190 | 0 | 7 s | 2026-09-21 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 7.132 |
| **de tarjeta** (no bajan lo que pagas en caja) | **1.900** |
| **solo por internet** (no bajan el ticket de la tienda) | **392** |
| ofertas que cuentan de verdad | 4.840 |
