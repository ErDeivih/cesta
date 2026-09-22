# Las cifras de la ultima ejecucion

**Ejecucion del 22 de septiembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.567** |
| grupos comparables | **7.992** |
| productos comparables por kg/l/m | **42.353** |
| productos con codigo de barras | **25.517** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.823** |
| productos con certificado | **730** |
| productos con Nutri-Score | **8.450** |
| productos con tabla nutricional | **3.841** |
| productos con envase | **9.120** |

## Historico

    763.042 filas, 17 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| carrefour | 16.525 | 4 | 2.789 s | 2026-09-22 |
| alcampo | 9.729 | 1 | 463 s | 2026-09-22 |
| dia | 5.780 | 0 | 112 s | 2026-09-22 |
| mercadona | 4.328 | 0 | 91 s | 2026-09-22 |
| aldi | 2.123 | 0 | 3 s | 2026-09-22 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 7.087 |
| **de tarjeta** (no bajan lo que pagas en caja) | **1.899** |
| **solo por internet** (no bajan el ticket de la tienda) | **392** |
| ofertas que cuentan de verdad | 4.796 |
