# Las cifras de la ultima ejecucion

**Ejecucion del 10 de noviembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **53.072** |
| grupos comparables | **8.891** |
| productos comparables por kg/l/m | **43.321** |
| productos con codigo de barras | **25.573** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.543** |
| productos con certificado | **1.033** |
| productos con Nutri-Score | **8.479** |
| productos con tabla nutricional | **3.887** |
| productos con envase | **8.954** |

## Historico

    2.866.370 filas, 65 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.572 | 0 | 6.569 s | 2026-11-10 |
| carrefour | 16.684 | 1 | 2.711 s | 2026-11-10 |
| dia | 5.681 | 0 | 691 s | 2026-11-10 |
| mercadona | 4.284 | 0 | 101 s | 2026-11-10 |
| aldi | 2.769 | 0 | 90 s | 2026-11-10 |
| lidl | 82 | 0 | 5 s | 2026-11-10 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 6.150 |
| **de tarjeta** (no bajan lo que pagas en caja) | **714** |
| **solo por internet** (no bajan el ticket de la tienda) | **78** |
| ofertas que cuentan de verdad | 5.358 |
