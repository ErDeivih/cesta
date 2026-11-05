# Las cifras de la ultima ejecucion

**Ejecucion del 5 de noviembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.320** |
| grupos comparables | **8.841** |
| productos comparables por kg/l/m | **42.835** |
| productos con codigo de barras | **25.607** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.390** |
| productos con certificado | **995** |
| productos con Nutri-Score | **8.518** |
| productos con tabla nutricional | **3.903** |
| productos con envase | **8.974** |

## Historico

    2.603.347 filas, 60 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 22.811 | 0 | 8.000 s | 2026-11-05 |
| carrefour | 16.738 | 1 | 6.634 s | 2026-11-05 |
| dia | 5.704 | 0 | 694 s | 2026-11-05 |
| mercadona | 4.267 | 0 | 101 s | 2026-11-05 |
| aldi | 2.709 | 0 | 86 s | 2026-11-05 |
| lidl | 91 | 0 | 4 s | 2026-11-05 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 6.222 |
| **de tarjeta** (no bajan lo que pagas en caja) | **717** |
| **solo por internet** (no bajan el ticket de la tienda) | **80** |
| ofertas que cuentan de verdad | 5.425 |
