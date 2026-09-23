# Las cifras de la ultima ejecucion

**Ejecucion del 23 de septiembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.417** |
| grupos comparables | **8.781** |
| productos comparables por kg/l/m | **42.340** |
| productos con codigo de barras | **25.395** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.790** |
| productos con certificado | **712** |
| productos con Nutri-Score | **8.412** |
| productos con tabla nutricional | **3.861** |
| productos con envase | **9.145** |

## Historico

    815.258 filas, 18 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.842 | 0 | 4.180 s | 2026-09-23 |
| carrefour | 16.375 | 4 | 3.487 s | 2026-09-23 |
| dia | 5.809 | 0 | 647 s | 2026-09-23 |
| mercadona | 4.325 | 0 | 93 s | 2026-09-23 |
| aldi | 2.066 | 0 | 84 s | 2026-09-23 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 6.581 |
| **de tarjeta** (no bajan lo que pagas en caja) | **1.676** |
| **solo por internet** (no bajan el ticket de la tienda) | **390** |
| ofertas que cuentan de verdad | 4.515 |
